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
from django.http import HttpResponse, JsonResponse
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

from accounts.models import User, Supplement, Weight, WeightPrices, Report, Company
from tool.forms import ReportForm, TransporterFileForm, TransporterFileFormSet, CompanyFileForm
import json

from tool.helpers import parse_data
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


'''
Webpage result:
'''


class ResultView(LoginRequiredMixin, TemplateView):

    """ View to access results from comparison """

    template_name = 'tool/result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company_file_pk'] = self.request.session['company_file_pk']
        print(context['company_file_pk'])
        dict_files = self.request.session['dict_files']
        print(dict_files)
        user = self.request.user
        context['result'] = self.request.session['result']
        result = context['result']

        # Transformation into DF
        df = pd.DataFrame(result)
        # pprint(df)

        # Count number of rows
        nb_rows = df[df.columns[0]].count()
        context['nb_rows'] = nb_rows

        # Count number of rows which are errored
        nb_errors = np.sum(df['IsSimilar'] == 'No')
        context['nb_errors'] = nb_errors

        # Sum all rows
        total_amount = df['Montant_HT'].sum()
        context['total_amount'] = total_amount

        # Sum all rows which are errored
        rows_errors_sum = df.loc[df['IsSimilar'] == 'No', ['Result']].sum().values
        rows_errors_sum = str(rows_errors_sum).replace('[', '').replace(']', '')
        rows_errors_sum = float(rows_errors_sum)
        context['rows_errors_sum'] = rows_errors_sum

        return context


class DownloadView(LoginRequiredMixin, TemplateView):

    """ View to download results in XLSX format. """


    template_name = 'tool/download.html'

    def get(self, request, *args, **kwargs):
        content = self.request.session['result']
        df = pd.DataFrame(content)

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


class UserAddReportView(LoginRequiredMixin, RequestFormMixin, CreateView):

    """ View to create a report. """

    model = Report
    template_name = 'tool/add-report.html'
    form_class = ReportForm
    success_url = reverse_lazy('tool:upload')

    def form_valid(self, form):
        self.object = form.save()
        self.request.session['report_id'] = self.object.pk
        if not self.object.slug:
            self.object.slug = slugify(str(self.object.company) + "-" + get_random_string(length=32))
        return super().form_valid(form)


class UserReportsView(LoginRequiredMixin, TemplateView):
    """ View to access reports """

    model = Report
    template_name = 'tool/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['reports'] = Report.objects.filter(company=user.company)
        # slug = self.kwargs['slug']
        # context['report'] = get_object_or_404(Report, slug=slug)

        return context


class UserViewReport(LoginRequiredMixin, TemplateView):
    """ View to access ONE report """

    model = Report
    template_name = 'tool/single-report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['result'] = self.request.session['result']
        slug = self.kwargs['slug']
        context['report'] = get_object_or_404(Report, slug=slug)
        data = context['report']
        data = data.result
        # We recover the DF linked to the report

        df = pd.read_json(data)

        # Count number of rows
        nb_rows = df[df.columns[0]].count()
        context['nb_rows'] = nb_rows

        # Count number of rows which are errored
        nb_errors = np.sum(df['IsSimilar'] == 'No')
        context['nb_errors'] = nb_errors

        # Sum all rows
        total_amount = df['Montant_HT'].sum()
        context['total_amount'] = total_amount

        # Sum all rows which are errored
        rows_errors_sum = df.loc[df['IsSimilar'] == 'No', ['Result']].sum().values
        rows_errors_sum = str(rows_errors_sum).replace('[', '').replace(']', '')
        rows_errors_sum = float(rows_errors_sum)
        context['rows_errors_sum'] = rows_errors_sum

        df_stats = df['IsSimilar'].value_counts()
        context['data_dict'] = df_stats.to_dict()

        return context


class TransporterFileFormPartialView(FormView):
    form_class = TransporterFileForm
    template_name = 'tool/upload-form.html'
    success_url = '.'


    def form_valid(self, form):
        user = self.request.user
        report_id = self.request.session['report_id']
        print(report_id)
        transporter_file = TransporterFile.objects.create(
            file=form.cleaned_data['file'],
            transporter=form.cleaned_data['transporter'],
            user=user,
        )

        transporter_file_pk = transporter_file.pk

        return super().form_valid(form)



class UploadView(RequestFormMixin, TemplateView):

    template_name = 'tool/upload.html'

    def get_context_data(self, **kwargs):
        print(self.request.META.get('HTTP_REFERER'))
        context = super().get_context_data(**kwargs)
        context['formset'] = TransporterFileFormSet(queryset=TransporterFile.objects.none())
        context['files'] = TransporterFile.objects.all()

        return context


    def post(self, request, *args, **kwargs):

        user = self.request.user
        company = get_object_or_404(Company, pk=user.company.pk)
        formset = TransporterFileFormSet(data=request.POST or None, files=request.FILES, instance=company)

        if formset.is_valid():

            dict_files = {}
            files_list = []
            pk_list = []

            for form in formset:
                obj = form.save(commit=False)
                cd = form.cleaned_data
                file = cd.get('file')
                form.save()
                transporter_file = TransporterFile.objects.get(pk=obj.pk)
                n_transporter_file = TransporterFile.objects.filter(pk=obj.pk).update(name=transporter_file.file.name)
                n_transporter_file = TransporterFile.objects.filter(pk=obj.pk).update(user=user)
                pk_list.append(obj.pk)
                files_list.append(transporter_file.file.name)
                dict_files['pk'] = pk_list
                dict_files['files'] = files_list
                request.session['dict_files'] = dict_files


            return redirect('tool:upload-company-file')



        else:
            raise ValidationError('You cannot submit empty form.')


        return self.render_to_response({'formset': formset})



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







# class CompareFormView(CustomLoginRequiredMixin, RequestFormMixin, TemplateView):
#     """ View to show results of comparison between two files. """
#
#     template_name = 'tool/upload.html'
#     # success_url = '.'
#
#
#     def post(self, *args, **kwargs):
#
#
#
#         if formset.is_valid():
#             obj = formset.save(commit=False)
#             # transporter_file = get_object_or_404(TransporterFile, pk=form.pk)
#             obj.save()
#             transporter_file = TransporterFile.objects.get(pk=obj.pk)
#             transporter_file_pk = transporter_file.pk
#             update_transporter_file = TransporterFile.objects.filter(pk=obj.pk).update(user=self.request.user)
#             # report_id = self.request.session['report_id']
#             # update_transporter_report_id = TransporterFile.objects.filter(pk=obj.pk).update(report=report_id)
#
#             return redirect(reverse_lazy('tool:upload'))

    #
    #         d_transporters = {}
    #
    #         for form in formset:
    #             d_form = form.save(commit=False)
    #             d_form_data = form.cleaned_data
    #
    #             # Retrieve all variables
    #             transporter = d_form_data.get('transporter')
    #             file = d_form_data.get('file')
    #             user = self.request.user
    #             company = user.company
    #             extension = os.path.splitext(file.name)[1]
    #             supplement = Supplement.objects.get(company=company, transporter=transporter)
    #             header_row = supplement.header_row
    #             columns_to_keep = str(supplement.columns_to_keep)
    #             print(extension)
    #
    #             #Passing values into dictionary
    #
    #             extension_list = []
    #             file_list = []
    #             header_row_list = []
    #
    #             if len(d_transporters) == 0:
    #                 d_transporters['transporter'] = transporter.name
    #
    #             # Send data
    #             d_form.save()
    #             transporter_file = get_object_or_404(TransporterFile, pk=d_form.pk)
    #             print(transporter_file.pk)
    #
    #         return redirect(reverse_lazy('tool:upload-detail', kwargs={'pk': transporter_file.pk}))
    #
    #
    #
    #     return self.render_to_response({'transporter_formset': formset})

