import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from pprint import pprint

# Create your views here.
from django.urls import path, reverse_lazy, reverse
from django.views.generic import TemplateView, CreateView, FormView, DetailView, ListView, UpdateView
from django_pandas.io import read_frame

from accounts.models import User, Supplement, Weight, WeightPrices
from tool.forms import CompareFormTransporterCompany
import json

from tool.models import CheckFile


class RequestFormMixin:
    """Mixin to inject the request in the form."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


'''
Form result2:
'''

class CompareFormView(RequestFormMixin, FormView):
    """ View to show results of comparison between two files. """

    template_name = 'tool/upload.html'
    form_class = CompareFormTransporterCompany
    success_url = reverse_lazy('tool:result')


'''
TRANSPORTERS:
View to see the list of transporters affected to one user.
'''

class UserSupplementView(TemplateView):

    model = User
    template_name = 'tool/transporters.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['supplements'] = user.company.supplement_set.all()
        print(context['supplements'])
        return context

class UserSupplementTransporterView(TemplateView):
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

class UserSupplementTransporterEditView(UpdateView):
    model = Supplement
    fields = ['supplement_annonce_incomplete', 'supplement_retour_expediteur', 'supplement_etiquette_non_conforme','supplement_zone_difficile_acces', 'supplement_corse', 'supplement_manutention', 'supplement_gt', 'supplement_carburant_routier', 'supplement_frais_de_gestion', 'supplement_facture_papier', 'supplement_surete_colis', 'supplement_zone_internationale_eloignee', 'supplement_surcharge_carburant_routier', 'supplement_covid', 'supplement_taxe_carbone']
    template_name = 'tool/transporter-detail-edit.html'
    context_object_name = "edit-tarifs"

    def form_valid(self, form):
        context = self.get_context_data()
        slug = self.kwargs['slug']
        form.instance.supplement = Supplement.objects.get(slug=slug)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tool:tarifs', kwargs={'slug' : self.object.slug})





'''
Webpage result:
'''

class ResultView(TemplateView):
    template_name = 'tool/result.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['uploaded'] = self.request.session['uploaded']
        context['selection'] = self.request.session['selection']
    #     context['profile'] = self.request.session['profile']
    #     dict_comparaison_p1 = dict(enumerate(context['uploaded'].items()))
    #     list_comparaison_p2 = context['selection']
    #     dict_comparaison_p2 = {number: dict_comparaison_p1[number] for number in list_comparaison_p2}
    #     d_col = {}
    #     df = pd.DataFrame()
    #     for idx, (k, v) in enumerate(dict_comparaison_p2.items()):
    #         d_col[k] = v[0]
    #         # print(d_col[k])
    #         df = df.append(pd.DataFrame(data=v[1], index=[idx]))
    #
    #     d_col2 = {i: v for i, v in enumerate(d_col.values())}
    #     df = df.T.rename(columns=d_col2)
    #     print(df)
    #     ''' Rework du dataframe '''
    #     #Rework columns
    #     df.columns = df.columns.map(lambda x: x.strip())
    #     #Withdrawing 5 last rows
    #     df = df[:-5]
    #     #Replacing "," by "." to get actual integers
    #     df['Montant HT'] = df['Montant HT'].replace({",": "."})
    #     #Grouping sums
    #     df = df.groupby(['Numero LT'], as_index=False).agg(
    #         {'Montant HT': 'sum', 'Type prestation': 'first'})
    #     print(df)
    #
    #     columns_to_keep = ['supplement_annonce_incomplete', 'supplement_retour_expediteur',
    #                        'supplement_etiquette_non_conforme',
    #                        'supplement_zone_difficile_acces', 'supplement_corse', 'supplement_manutention',
    #                        'supplement_gt',
    #                        'supplement_carburant_routier', 'supplement_frais_de_gestion', 'supplement_facture_papier',
    #                        'supplement_surete_colis', 'supplement_zone_internationale_eloignee',
    #                        'supplement_surcharge_carburant_routier',
    #                        'supplement_covid', 'supplement_taxe_carbone']
    #
    #     #SUPPLEMENTS
    #     #Convert list of supplements into DataFrame
    #     query_supplements = Supplement.objects.filter(company=user.company).values()
    #     df2 = read_frame(query_supplements)
    #     cols = [col for col in df2.columns if col in columns_to_keep]
    #     df2 = df2[cols]
    #     df2 = df2.T
    #
    #
    #     #WEIGHTS
    #     #Transporter name is needed for filtering
    #     transporter = Supplement.objects.get(company=user.company)
    #     transporter = transporter.transporter
    #     weight_id = Weight.objects.filter(company=user.company, transporter=transporter)
    #
    #     #Weight prices
    #     weight_prices_list = weight_id.values()
    #     print(weight_prices_list)

        # return context

