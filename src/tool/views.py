import os
from io import BytesIO
import time
import numpy as np
import pandas as pd
import xlsxwriter
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from pprint import pprint

from django.template.defaultfilters import slugify
import plotly.graph_objects as go
from django.urls import path, reverse_lazy, reverse
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, CreateView, FormView, DetailView, ListView, UpdateView, DeleteView
from django_pandas.io import read_frame

from accounts.models import User, Supplement, Weight, WeightPrices, Company, Transporter, SupplementDetails
from reports.models import Report, ReportDetails
from tool.forms import TransporterFileForm, CompanyFileForm
import json

from tool.helpers import get_header_row, parse_file, analyze, store_results
from tool.models import TransporterFile, CompanyFile

pd.set_option('display.width', 400)
pd.set_option('display.max_columns', 15)


class RequestFormMixin:
    """Mixin to inject the request in the form."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class CustomLoginRequiredMixin(LoginRequiredMixin):
    """ The LoginRequiredMixin extended to add a relevant message to the
    messages framework by setting the ``permission_denied_message``
    attribute. """

    permission_denied_message = 'You have to be logged in to access that page'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.add_message(request, messages.WARNING,
                                 self.permission_denied_message)
            return self.handle_no_permission()
        return super(CustomLoginRequiredMixin, self).dispatch(
            request, *args, **kwargs
        )


'''
TRANSPORTERS:
View to see the list of transporters affected to one user.
'''


class UserSupplementView(CustomLoginRequiredMixin, TemplateView):
    """ View to see transporters """

    model = User
    template_name = 'tool/transporters.html'
    permission_denied_message = 'Restricted access!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['supplements'] = user.company.supplement_set.all()
        print(context['supplements'])
        return context


class UserSupplementTransporterView(LoginRequiredMixin, TemplateView):
    model = Supplement
    template_name = 'tool/transporter-detail.html'
    context_object_name = "tarifs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        context['supplement'] = get_object_or_404(Supplement, slug=slug)
        return context

    def get_form_kwargs(self):
        kwargs = super(UserSupplementTransporterView, self).get_form_kwargs()
        slug = self.kwargs['slug']
        kwargs['header'] = get_object_or_404(Supplement, slug=slug).header_row
        return kwargs


'''
TRANSPORTER:
View to edit pricings of transporter.
'''


class UserSupplementTransporterEditView(LoginRequiredMixin, UpdateView):
    """ View to edit supplements """

    model = Supplement
    fields = ['supplement_annonce_incomplete', 'supplement_retour_expediteur', 'supplement_etiquette_non_conforme',
              'supplement_zone_difficile_acces', 'supplement_corse', 'supplement_manutention', 'supplement_gt',
              'supplement_carburant_routier', 'supplement_frais_de_gestion', 'supplement_facture_papier',
              'supplement_surete_colis', 'supplement_zone_internationale_eloignee',
              'supplement_surcharge_carburant_routier', 'supplement_covid', 'supplement_taxe_carbone']
    template_name = 'tool/transporter-detail-edit.html'
    context_object_name = "edit-tarifs"

    def form_valid(self, form):
        context = self.get_context_data()
        slug = self.kwargs['slug']
        form.instance.supplement = Supplement.objects.get(slug=slug)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tool:tarifs', kwargs={'slug': self.object.slug})


class UploadView(RequestFormMixin, TemplateView):
    template_name = 'tool/upload.html'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['formset'] = TransporterFileFormSet(queryset=TransporterFile.objects.none())
    #     context['files'] = TransporterFile.objects.all()
    #
    #     ''' Even if user is logged in, cannot access directly the URL. Have to use the form. '''
    #     # if reverse('tool:add-report') not in self.request.META.get('HTTP_REFERER'):
    #     #     raise Http404
    #
    #     return context
    #
    # def post(self, request, *args, **kwargs):
    #
    #     user = self.request.user
    #     company = get_object_or_404(Company, pk=user.company.pk)
    #     formset = TransporterFileFormSet(data=request.POST or None, files=request.FILES, instance=company)

        # if formset.is_valid():
        #
        #     dict_files = {}
        #     files_list = []
        #     transporter_list = []
        #     pk_list = []
        #
        #     for form in formset:
        #         obj = form.save(commit=False)
        #         cd = form.cleaned_data
        #         file = cd.get('file')
        #         transporter = cd.get('transporter')
        #         print(transporter)
        #         form.save()
        #         transporter_file = TransporterFile.objects.get(pk=obj.pk)
        #         n_transporter_file = TransporterFile.objects.filter(pk=obj.pk).update(name=transporter_file.file.name)
        #         n_transporter_file = TransporterFile.objects.filter(pk=obj.pk).update(user=user)
        #         pk_list.append(obj.pk)
        #         files_list.append(transporter_file.file.name)
        #         transporter_list.append(transporter.name)
        #         print(transporter_list)
        #         dict_files['pk'] = pk_list
        #         dict_files['files'] = files_list
        #         dict_files['transporter'] = transporter_list
        #         request.session['dict_files'] = dict_files
        #
        #     return redirect('tool:upload-company-file')
        #
        #
        #
        # else:
        #     raise ValidationError('You cannot submit empty form.')
        #
        # return self.render_to_response({'formset': formset})


class UploadCompanyFileView(LoginRequiredMixin, CreateView):
    model = CompanyFile
    template_name = 'tool/upload-company-file.html'
    form_class = CompanyFileForm
    success_url = reverse_lazy('tool:result')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dict_files'] = self.request.session['dict_files']
        print(context['dict_files'])
        return context

    def form_valid(self, form):
        self.object = form.save()
        user = self.request.user
        self.object.user = user
        self.object.company = user.company
        self.object.name = self.object.file.name
        # self.request.session['report_id'] = self.object.pk
        # if not self.object.slug:
        #     self.object.slug = slugify(str(self.object.company) + "-" + get_random_string(length=32))
        self.request.session['company_file_pk'] = self.object.pk
        return super().form_valid(form)


'''
Webpage result:
'''


class ResultView(LoginRequiredMixin, TemplateView):
    """ View to access results from comparison """

    template_name = 'tool/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #Preparing empty data
        transporters_profile_list = []
        transporters_list = []
        dict_errors = {}

        ''' TRANSPORTERS '''
        transporters_profile = Supplement.objects.filter(company=self.request.user.company).values_list(
            'transporter__name', flat=True)
        for profile in transporters_profile:
            transporters_profile_list.append(profile)



        ''' FILES '''
        # Company file
        context['company_file_pk'] = self.request.session['company_file_pk']
        company_file = get_object_or_404(CompanyFile, pk=context['company_file_pk'])
        company_file = company_file.file

        # File list
        dict_files = self.request.session['dict_files']

        for i in range(len(dict_files.get('pk'))):
            # Get variables and names
            pk = dict_files.get('pk')[i]

            #Handling transporters. If transporter is in list, then outputs result.
            transporter = dict_files.get('transporter')[i]
            transporters_list.append(transporter)
            transporter = Transporter.objects.get(name=transporter)

            #Managing header_row
            header_row = get_header_row(company=self.request.user.company, transporter=transporter)

            #Get actual transporter file
            transporter_file = TransporterFile.objects.get(pk=pk)
            transporter_file = transporter_file.file
            extension = os.path.splitext(transporter_file.name)[1]

            ''' Analysis '''
            'To make analysis, function analyze() needs to be called.' \
            'The function needs to be called with the company file, transporter file, the transporter and the company.'

            df = analyze(transporter_file=transporter_file,
                            company_file=company_file,
                            transporter=transporter,
                            company=self.request.user.company)



            context['transporters'] = transporters_list

            ''' Preparing new DF with errors and sums. '''
            df = pd.DataFrame(df)
            print(self.request.session['report_id'])
            report_details_pk = store_results(pk=self.request.session['report_id'], data=df.to_dict(), transporter=transporter)
            slug = ReportDetails.objects.get(pk=report_details_pk).slug

            #Calculating number of errors
            nb_errors = np.sum(df['IsSimilar'] == 'No')
            context['nb_errors'] = nb_errors
            #Calculating sum of all orders
            total_amount = df['Montant_HT'].sum()
            total_amount = round(total_amount)
            context['total_amount'] = total_amount
            # Sum all rows which are errored
            rows_errors_sum = df.loc[df['IsSimilar'] == 'No', ['Result']].sum().values
            rows_errors_sum = str(rows_errors_sum).replace('[', '').replace(']', '')
            rows_errors_sum = float(rows_errors_sum)
            context['rows_errors_sum'] = rows_errors_sum


            ''' Storing errors in dict_errors '''
            dict_errors[transporter.name] = {
                'nb_errors': nb_errors,
                'total_amount': total_amount,
                'rows_errors_sum': rows_errors_sum,
                'slug': slug
            }

            context['dict_errors'] = dict_errors
            self.request.session['report_detail_pk'] = report_details_pk



        return context


class DownloadView(LoginRequiredMixin, TemplateView):
    """ View to download results in XLSX format. """
    model = ReportDetails
    template_name = 'tool/download.html'

    def get(self, request, *args, **kwargs):
        slug = self.kwargs['slug']
        report_details = ReportDetails.objects.get(slug=slug)
        data = json.loads(report_details.data)
        df = pd.DataFrame(data)

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        with BytesIO() as b:
            writer = pd.ExcelWriter(b, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Rapport', index=False)
            number_rows = len(df.index) + 1
            wb = writer.book
            ws = writer.sheets['Rapport']
            format1 = wb.add_format({'bg_color': '#FFC7CE',
                                     'font_color': '#9C0006'})

            ws.conditional_format("$A$1:$O$%d" % (number_rows),
                                  {"type": "formula",
                                   "criteria": '=INDIRECT("O"&ROW())="No"',
                                   "format": format1
                                   }
                                  )

            writer.save()
            filename = 'Rapport'
            content_type = 'application/vnd.ms-excel'
            response = HttpResponse(b.getvalue(), content_type=content_type)
            response['Content-Disposition'] = 'attachment; filename="' + filename + '.xlsx"'

            return response

