import os
import sqlite3
from pprint import pprint

import numpy as np
import pandas as pd
from django import forms
from django.shortcuts import get_object_or_404
from django_pandas.io import read_frame

from accounts.models import Transporter, Supplement, Weight, WeightPrices
from tool.helpers import parse_excel, parse_csv, parse_xml, validate_file_extension
from tool.models import CheckFile


class CompareFormTransporterCompany(forms.ModelForm):
    file = forms.FileField(label="Insertion fichier transporteur")
    name_transporter = forms.ModelChoiceField(label='Choose transporter', queryset=Transporter.objects.all())
    file_company = forms.FileField(label="Insertion fichier des commandes")

    class Meta:
        model = CheckFile
        fields = ['file',]


    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        user = self.request.user
        print(user)

    def clean(self):
        super().clean()
        user = self.request.user
        company = user.company
        transporter = self.cleaned_data.get('name_transporter')
        supplement = Supplement.objects.get(company=company, transporter=transporter)
        rowheader = supplement.header_row
        print(rowheader)
        columns_to_keep = str(supplement.columns_to_keep)
        columns_to_keep = columns_to_keep.split(",")
        columns_to_keep = [x.strip(' ') for x in columns_to_keep]

        #RETRIEVE TRANSPORTER FILE

        uploaded_file_transporter = self.request.FILES['file']
        extension = os.path.splitext(uploaded_file_transporter.name)[1]
        # uploaded_file_transporter = parse_excel(self.request.FILES['file'], rowheader=rowheader)
        if extension in ['.xls', '.xlsx']:
            uploaded_file_transporter = parse_excel(uploaded_file_transporter, rowheader=rowheader)
        elif extension == ".xml":
            uploaded_file_transporter = parse_xml(uploaded_file_transporter)
        elif extension == ".csv":
            uploaded_file_transporter = parse_csv(uploaded_file_transporter)
        self.request.session['uploaded_file_transporter'] = uploaded_file_transporter


        #RETRIEVE COMPANY FILE

        uploaded_file_company = self.request.FILES['file_company']
        extension = os.path.splitext(uploaded_file_company.name)[1]
        if extension in ['.xls', '.xlsx']:
            uploaded_file_company = parse_excel(uploaded_file_company, rowheader=rowheader)
        elif extension == ".xml":
            uploaded_file_company = parse_xml(uploaded_file_company)
        elif extension == ".csv":
            uploaded_file_company = parse_csv(uploaded_file_company)
        self.request.session['uploaded_file_company'] = uploaded_file_company



        ''' ############################
        First dataframe : TRANSPORTER
        ############################
        '''

        df_transporter = pd.DataFrame.from_dict(uploaded_file_transporter)
        cols = [col for col in df_transporter.columns if col in columns_to_keep]
        df_transporter = df_transporter[cols]
        #Removing last 5 rows
        df_transporter = df_transporter[:-5]
        #Replacing "," by "." to get actual integers
        df_transporter['Montant HT'] = df_transporter['Montant HT'].replace({",": "."})
        #Grouping sums
        df_transporter = df_transporter.groupby(['Numero LT'], as_index=False).agg(
                {'Montant HT': 'sum', 'Type prestation': 'first'})

        df_transporter['Type prestation'] = df_transporter['Type prestation'].str.lower() #Remove CAPS
        df_transporter['Type prestation'] = df_transporter['Type prestation'].str.replace(' ', '_') #Remove spaces and replace them with "_"
        df_transporter['Type prestation'] = df_transporter['Type prestation'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')


        ''' ############################
        Second dataframe : COMPANY FILE
        ############################
        '''

        df_commandes = pd.DataFrame.from_dict(uploaded_file_company)
        df_commandes = df_commandes.dropna(subset='Date LT')


        ''' ############################
        Third dataframe : SUPPLEMENTS
        ############################
        '''

        #SUPPLEMENTS
        #Convert list of supplements into DataFrame
        # query_supplements = Supplement.objects.filter(company=company).values()

        columns_to_keep2 = ['supplement_annonce_incomplete', 'supplement_retour_expediteur',
                            'supplement_etiquette_non_conforme',
                            'supplement_zone_difficile_acces', 'supplement_corse', 'supplement_manutention',
                            'supplement_gt',
                            'supplement_carburant_routier', 'supplement_frais_de_gestion', 'supplement_facture_papier',
                            'supplement_surete_colis', 'supplement_zone_internationale_eloignee',
                            'supplement_surcharge_carburant_routier',
                            'supplement_covid', 'supplement_taxe_carbone']

        query_supplements = Supplement.objects.filter(company=company, transporter=transporter).values()
        df_tarifs = pd.DataFrame(query_supplements)
        cols2 = [col for col in df_tarifs.columns if col in columns_to_keep2]
        df_tarifs = df_tarifs[cols2]
        df_tarifs = df_tarifs.T
        df_tarifs = df_tarifs.reset_index()
        df_tarifs.columns = ['Type prestation', 'Price transporter']


        ''' ############################
        Fourth dataframe : WEIGHT PRICES
        ############################
        '''

        #WEIGHTS

        weight_id = Weight.objects.filter(company=company, transporter=transporter)
        query_weights = WeightPrices.objects.filter(weight__in=weight_id).values()
        df_weight = pd.DataFrame(query_weights)
        columns_to_keep3 = ['min_weight', 'max_weight',
                            'price']
        cols3 = [col for col in df_weight.columns if col in columns_to_keep3]
        df_weight = df_weight[cols3]


        ''' ############################
        Final dataframe : COMPARISON
        ############################
        '''

        df3 = df_commandes.merge(df_transporter, how='left')
        df4 = df3.merge(df_tarifs, how='left')
        df4.columns = df4.columns.str.replace(' ', '_')
        df4['Poids'].astype(float)
        pprint(df4)
        pprint(df_weight)

        weights_comparison = df4['Poids'].values
        min_weights_comparison = df_weight['min_weight'].values
        max_weights_comparison = df_weight['max_weight'].values

        i, j = np.where((weights_comparison[:, None] >= min_weights_comparison) & (weights_comparison[:, None] <= max_weights_comparison))

        df5 = pd.concat([
            df4.loc[i, :].reset_index(drop=True),
            df_weight.loc[j, :].reset_index(drop=True)
        ], axis=1).append(
            df4[~np.in1d(np.arange(len(df4)), np.unique(i))],
            ignore_index=True, sort=False
        )

        df5.rename(columns={'price':'Weight_price'}, inplace=True)
        df5['Price_transporter'] = df5['Price_transporter'].astype(float).fillna(0)
        df5['Weight_price'] = df5['Weight_price'].astype(float).fillna(0)
        df5['Result'] = df5['Price_transporter'] + df5['Weight_price']


        ''' ############################
        Final dataframe : RESULT
        ############################
        '''

        df5['IsSimilar'] = np.where(df5['Montant_HT'] == df5['Result'], True, False)




