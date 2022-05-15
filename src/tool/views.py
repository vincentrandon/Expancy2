from io import BytesIO
import time
import numpy as np
import pandas as pd
import xlsxwriter
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from pprint import pprint

from django.template.defaultfilters import slugify
import plotly.graph_objects as go
from django.urls import path, reverse_lazy, reverse
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, CreateView, FormView, DetailView, ListView, UpdateView
from django_pandas.io import read_frame

from accounts.models import User, Supplement, Weight, WeightPrices, Report
from tool.forms import CompareFormTransporterCompany, ReportForm
import json

from tool.models import CheckFile

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
Form result2:
'''

class CompareFormView(CustomLoginRequiredMixin, RequestFormMixin, FormView):
    """ View to show results of comparison between two files. """

    template_name = 'tool/upload.html'
    form_class = CompareFormTransporterCompany
    success_url = reverse_lazy('tool:result')
    permission_denied_message = 'Restricted access!'




'''
TRANSPORTERS:
View to see the list of transporters affected to one user.
'''

class UserSupplementView(CustomLoginRequiredMixin, TemplateView):
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
    template_name = 'tool/result.html'



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        #We recover the DF linked to the report

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
