import os
import sqlite3
import calendar
from pprint import pprint
import time
import numpy as np
import pandas as pd
from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django_pandas.io import read_frame

from accounts.models import Transporter, Supplement, Weight, WeightPrices, Report, Company
from tool.helpers import parse_excel, parse_csv, parse_xml, validate_file_extension
from tool.models import TransporterFile, CompanyFile


class TransporterFileForm(forms.ModelForm):
    class Meta:
        model = TransporterFile
        fields = ('file', 'transporter')


TransporterFileFormSet = inlineformset_factory(Company, TransporterFile, form=TransporterFileForm, extra=0, can_delete=True)

class CompanyFileForm(forms.ModelForm):
    class Meta:
        model = CompanyFile
        fields = ('file', )

        def __init__(self, request, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.request = request
            user = self.request.user
            self.initial['user'] = user
            self.initial['company'] = user.company

        def clean(self):
            super().clean()
            user = self.request.user
            file = self.cleaned_data.get('file')
            print(file)



class ReportForm(forms.ModelForm):
    """ Form to create a report. """

    date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Report
        fields = ['company', ]

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        user = self.request.user
        self.initial['company'] = user.company

    def clean(self):
        super().clean()
        filtered_date = self.cleaned_data.get('date')
        month = filtered_date.month
        month = calendar.month_name[month]
        year = filtered_date.year
        date_f = str(month) + " " + str(year)
        self.request.session['date_f'] = date_f




# class CompareFormTransporterCompany(forms.ModelForm):
#     """ Form  to compare transporter file and company file. """
#
#     # class Meta:
#     #     model = ReportCompany
#     #     fields = '__all__'
#
#     def __init__(self, request, *args, **kwargs):
#         # self.request = request
#         # user = self.request.user
#         super().__init__(*args, **kwargs)

    #
    # def clean(self):
    #     super().clean()
    #     user = self.request.user
    #     company = user.company
    #     transporter = self.cleaned_data.get('name_transporter')
    #     supplement = Supplement.objects.get(company=company, transporter=transporter)
    #     rowheader = supplement.header_row
    #     start_time = time.perf_counter()
    #     print(rowheader)
    #     columns_to_keep = str(supplement.columns_to_keep)
    #     columns_to_keep = columns_to_keep.split(",")
    #     columns_to_keep = [x.strip(' ') for x in columns_to_keep]
    #
    #     # RETRIEVE TRANSPORTER FILE
    #
    #     uploaded_file_transporter = self.request.FILES['file']
    #     extension = os.path.splitext(uploaded_file_transporter.name)[1]
    #     # uploaded_file_transporter = parse_excel(self.request.FILES['file'], rowheader=rowheader)
    #     if extension in ['.xls', '.xlsx']:
    #         uploaded_file_transporter = parse_excel(uploaded_file_transporter, rowheader=rowheader)
    #     elif extension == ".xml":
    #         uploaded_file_transporter = parse_xml(uploaded_file_transporter)
    #     elif extension == ".csv":
    #         uploaded_file_transporter = parse_csv(uploaded_file_transporter)
    #     self.request.session['uploaded_file_transporter'] = uploaded_file_transporter
    #
    #     # RETRIEVE COMPANY FILE
    #
    #     uploaded_file_company = self.request.FILES['file_company']
    #     extension = os.path.splitext(uploaded_file_company.name)[1]
    #     if extension in ['.xls', '.xlsx']:
    #         uploaded_file_company = parse_excel(uploaded_file_company, rowheader=rowheader)
    #     elif extension == ".xml":
    #         uploaded_file_company = parse_xml(uploaded_file_company)
    #     elif extension == ".csv":
    #         uploaded_file_company = parse_csv(uploaded_file_company)
    #     self.request.session['uploaded_file_company'] = uploaded_file_company
    #
    #     ''' ############################
    #     First dataframe : TRANSPORTER
    #     ############################
    #     '''
    #
    #     df_transporter = pd.DataFrame.from_dict(uploaded_file_transporter)
    #     cols = [col for col in df_transporter.columns if col in columns_to_keep]
    #     df_transporter = df_transporter[cols]
    #     # Removing last 5 rows
    #     df_transporter = df_transporter[:-5]
    #     # Replacing "," by "." to get actual integers
    #     df_transporter['Montant HT'] = df_transporter['Montant HT'].replace({",": "."})
    #     # Grouping sums
    #     df_transporter = df_transporter.groupby(['Numero LT'], as_index=False).agg(
    #         {'Montant HT': 'sum', 'Type prestation': 'first', 'Poids': 'first'})
    #
    #     df_transporter['Type prestation'] = df_transporter['Type prestation'].str.lower()  # Remove CAPS
    #     df_transporter['Type prestation'] = df_transporter['Type prestation'].str.replace(' ',
    #                                                                                       '_')  # Remove spaces and replace them with "_"
    #     df_transporter['Type prestation'] = df_transporter['Type prestation'].str.normalize('NFKD').str.encode('ascii',
    #                                                                                                            errors='ignore').str.decode(
    #         'utf-8')
    #
    #     ''' ############################
    #     Second dataframe : COMPANY FILE
    #     ############################
    #     '''
    #
    #     df_commandes = pd.DataFrame.from_dict(uploaded_file_company)
    #     df_commandes = df_commandes.dropna(subset='Date LT')
    #
    #     ''' ############################
    #     Third dataframe : SUPPLEMENTS
    #     ############################
    #     '''
    #
    #     # SUPPLEMENTS
    #     # Convert list of supplements into DataFrame
    #     # query_supplements = Supplement.objects.filter(company=company).values()
    #
    #     columns_to_keep2 = ['supplement_annonce_incomplete', 'supplement_retour_expediteur',
    #                         'supplement_etiquette_non_conforme',
    #                         'supplement_zone_difficile_acces', 'supplement_corse', 'supplement_manutention',
    #                         'supplement_gt',
    #                         'supplement_carburant_routier', 'supplement_frais_de_gestion', 'supplement_facture_papier',
    #                         'supplement_surete_colis', 'supplement_zone_internationale_eloignee',
    #                         'supplement_surcharge_carburant_routier',
    #                         'supplement_covid', 'supplement_taxe_carbone']
    #
    #     query_supplements = Supplement.objects.filter(company=company, transporter=transporter).values()
    #     df_tarifs = pd.DataFrame(query_supplements)
    #     cols2 = [col for col in df_tarifs.columns if col in columns_to_keep2]
    #     df_tarifs = df_tarifs[cols2]
    #     df_tarifs = df_tarifs.T
    #     df_tarifs = df_tarifs.reset_index()
    #     df_tarifs.columns = ['Type prestation', 'Price transporter']
    #
    #     ''' ############################
    #     Fourth dataframe : WEIGHT PRICES
    #     ############################
    #     '''
    #
    #     # WEIGHTS
    #
    #     weight_id = Weight.objects.filter(company=company, transporter=transporter)
    #     query_weights = WeightPrices.objects.filter(weight__in=weight_id).values()
    #     df_weight = pd.DataFrame(query_weights)
    #     columns_to_keep3 = ['min_weight', 'max_weight',
    #                         'price']
    #     cols3 = [col for col in df_weight.columns if col in columns_to_keep3]
    #     df_weight = df_weight[cols3]
    #
    #     ''' ############################
    #     Final dataframe : COMPARISON
    #     ############################
    #     '''
    #     pprint(df_transporter)
    #     df3 = df_commandes.merge(df_transporter, how='left')
    #     pprint(df3)
    #     df4 = df3.merge(df_tarifs, how='left')
    #     df4.columns = df4.columns.str.replace(' ', '_')
    #     df4['Poids'].astype(float)
    #
    #     weights_comparison = df4['Poids'].values
    #     min_weights_comparison = df_weight['min_weight'].values
    #     max_weights_comparison = df_weight['max_weight'].values
    #
    #     i, j = np.where((weights_comparison[:, None] >= min_weights_comparison) & (
    #                 weights_comparison[:, None] <= max_weights_comparison))
    #
    #     df5 = pd.concat([
    #         df4.loc[i, :].reset_index(drop=True),
    #         df_weight.loc[j, :].reset_index(drop=True)
    #     ], axis=1).append(
    #         df4[~np.in1d(np.arange(len(df4)), np.unique(i))],
    #         ignore_index=True, sort=False
    #     )
    #
    #     df5.rename(columns={'price': 'Weight_price'}, inplace=True)
    #     df5['Price_transporter'] = df5['Price_transporter'].astype(float).fillna(0)
    #     df5['Weight_price'] = df5['Weight_price'].astype(float).fillna(0)
    #     df5['Result'] = df5['Price_transporter'] + df5['Weight_price']
    #
    #     ''' ############################
    #     Final dataframe : RESULT
    #     ############################
    #     '''
    #
    #     df5['IsSimilar'] = np.where(df5['Montant_HT'] == df5['Result'], 'Yes', 'No')
    #     df_report = df5.to_json()  # For the REPORT model
    #     df_result = df5.to_dict()
    #     self.request.session['result'] = df_result
    #     end_time = time.perf_counter()
    #
    #     print(f'Le temps de traitement est de {end_time - start_time:0.4f} secondes')
    #
    #     ''' ############################
    #     We stock the result of the comparison within the REPORT model
    #     ############################
    #     '''
    #
    #     print(df_report)
    #     report_id = self.request.session['report_id']
    #     n_title = self.request.session['date_f']
    #     n_title = str(company) + " " + str(n_title)
    #     n_report = Report.objects.filter(pk=report_id).update(result=df_report)  # Update result value
    #     n_report_title = Report.objects.filter(pk=report_id).update(title=n_title)
    #
    #     # Updating slug according to new data
    #     temp_slug = n_title + "-" + str(report_id)
    #     n_slug = Report.objects.filter(pk=report_id).update(slug=slugify(temp_slug))




