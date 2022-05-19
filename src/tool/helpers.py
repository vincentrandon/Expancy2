import os
from pprint import pprint

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from accounts.models import Supplement, Weight, WeightPrices


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.xls', '.xlsx', '.csv', '.xml']
    if ext not in valid_extensions:
        raise ValidationError(u'Ce type de fichier n\'est pas supporté !')

def parse_csv(file):
    """Parses the csv file and return a dictionary representation of its
    content."""
    df = pd.read_csv(file)

    return df.to_dict()

def parse_excel(file, rowheader):
    """Parses the xls/xlsx file and return a dictionary representation of its
    content."""

    df = pd.read_excel(file, skiprows=rowheader)

    return df.to_dict()


def parse_xml(file):
    """Parses the xml file and return a dictionary representation of its
    content."""
    df = pd.read_xml(file)

    return df.to_dict()


def parse_data(**kwargs):
    """Parses file and return it for analysis"""

    for key in kwargs:

        company = kwargs['company']
        transporter = kwargs['transporter']
        extension = kwargs['extension']
        file = kwargs['file']
        header_row = kwargs['header_row']
        columns_to_keep = kwargs['columns_to_keep']
        # company_file = kwargs['company_file']

        print(company)

        ''' ############################
        First dataframe : TRANSPORTER
        ############################
        '''

        if extension in ['.xls', '.xlsx']:
            df = pd.read_excel(file, skiprows=header_row)

            #Retrieving columns and cleaning names
            columns_to_keep = str(columns_to_keep)
            columns_to_keep = columns_to_keep.split(",")
            columns_to_keep = [x.strip(' ') for x in columns_to_keep]

            cols = [col for col in df.columns if col in columns_to_keep]

            df = df[cols]
            # Removing last 5 rows
            df = df[:-5]
            # Replacing "," by "." to get actual integers
            df['Montant HT'] = df['Montant HT'].replace({",": "."})
            # Grouping sums
            df = df.groupby(['Numero LT'], as_index=False).agg(
                {'Montant HT': 'sum', 'Type prestation': 'first', 'Poids': 'first'})

            df['Type prestation'] = df['Type prestation'].str.lower()  # Remove CAPS
            df['Type prestation'] = df['Type prestation'].str.replace(' ', '_')  # Remove spaces and replace them with "_"
            df['Type prestation'] = df['Type prestation'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

            ''' ############################
            Second dataframe : COMPANY FILE
            ############################
            '''

            df_company = pd.DataFrame.from_dict(company_file)
            df_company = df_company.dropna(subset='Date LT')


            ''' ############################
            Third dataframe : SUPPLEMENTS
            ############################
            '''
#
            # SUPPLEMENTS
            # Convert list of supplements into DataFrame
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
#
            ''' ############################
            Fourth dataframe : WEIGHT PRICES
            ############################
            '''

            # WEIGHTS

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
            df3 = df_company.merge(df, how='left')
            pprint(df3)
            df4 = df3.merge(df_tarifs, how='left')
            df4.columns = df4.columns.str.replace(' ', '_')
            df4['Poids'].astype(float)

            weights_comparison = df4['Poids'].values
            min_weights_comparison = df_weight['min_weight'].values
            max_weights_comparison = df_weight['max_weight'].values

            i, j = np.where((weights_comparison[:, None] >= min_weights_comparison) & (
                        weights_comparison[:, None] <= max_weights_comparison))

            df5 = pd.concat([
                df4.loc[i, :].reset_index(drop=True),
                df_weight.loc[j, :].reset_index(drop=True)
            ], axis=1).append(
                df4[~np.in1d(np.arange(len(df4)), np.unique(i))],
                ignore_index=True, sort=False
            )

            df5.rename(columns={'price': 'Weight_price'}, inplace=True)
            df5['Price_transporter'] = df5['Price_transporter'].astype(float).fillna(0)
            df5['Weight_price'] = df5['Weight_price'].astype(float).fillna(0)
            df5['Result'] = df5['Price_transporter'] + df5['Weight_price']

            ''' ############################
            Final dataframe : RESULT
            ############################
            '''

            df5['IsSimilar'] = np.where(df5['Montant_HT'] == df5['Result'], 'Yes', 'No')
            df_report = df5.to_json()  # For the REPORT model
            df_result = df5.to_dict()
            # self.request.session['result'] = df_result



            ''' ############################
            We stock the result of the comparison within the REPORT model
            ############################
            '''

            # print(df_report)
            # report_id = self.request.session['report_id']
            # n_title = self.request.session['date_f']
            # n_title = str(company) + " " + str(n_title)
            # n_report = Report.objects.filter(pk=report_id).update(result=df_report)  # Update result value
            # n_report_title = Report.objects.filter(pk=report_id).update(title=n_title)
            #
            # # Updating slug according to new data
            # temp_slug = n_title + "-" + str(report_id)
            # n_slug = Report.objects.filter(pk=report_id).update(slug=slugify(temp_slug))

            return df5.to_dict()
