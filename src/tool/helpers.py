import os
from pprint import pprint

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.crypto import get_random_string

from accounts.models import Supplement, Weight, WeightPrices, SupplementDetails
from reports.models import Report, ReportDetails


def validate_file_extension(value):
    """ Validates file extension. """

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


def get_header_row(company, transporter):
    """ Get header row of transporter. """

    supplement = Supplement.objects.get(company=company, transporter=transporter)
    supplements_details = SupplementDetails.objects.get(supplement=supplement)
    return supplements_details.header_row


def parse_file(file, extension, header_row=0):
    """Parses file and return it for analysis"""

    if extension in ['.xls', '.xlsx']:
        df = pd.read_excel(file, skiprows=header_row)

    elif extension == ".xml":
        df = pd.read_xml(file)

    elif extension == ".csv":
        df = pd.read_csv(file, skiprows=header_row)

    return df.to_dict()


def columns_to_keep_transporter(company, transporter):
    """ Retrieves columns to keep in model "SUPPLEMENT DETAILS" """

    supplement = Supplement.objects.get(company=company, transporter=transporter)
    supplements_details = SupplementDetails.objects.get(supplement=supplement)
    columns_to_keep = supplements_details.columns_to_keep
    columns_to_keep = list(columns_to_keep.keys())

    return columns_to_keep


def parse_transporter_file(transporter_file, company, transporter):
    """ Parses TRANSPORTER FILE and cleans it. """

    # Getting 'Supplements_details' to retrieve values
    supplement = Supplement.objects.get(company=company, transporter=transporter)
    supplements_details = SupplementDetails.objects.get(supplement=supplement)
    supplement_header_row = supplements_details.header_row

    # Retrieve column 'Prestation type'
    column_prestation = supplements_details.column_prestation_type
    column_prestation = list(column_prestation.keys())
    column_prestation = ''.join(column_prestation)

    # Retrieve column 'Package number'
    column_package_number = supplements_details.column_package_number
    column_package_number = list(column_package_number.keys())
    column_package_number = ''.join(column_package_number)

    # Retrieve column 'Weight'
    column_weight = supplements_details.column_weight
    column_weight = list(column_weight.keys())
    column_weight = ''.join(column_weight)

    # Retrieve column 'Price'
    column_price = supplements_details.column_price
    column_price = list(column_price.keys())
    column_price = ''.join(column_price)
    column_price = column_price

    # Creating DF
    df_creation = parse_file(transporter_file, extension=os.path.splitext(transporter_file.name)[1],
                             header_row=supplement_header_row)
    df = pd.DataFrame(df_creation)
    columns_to_keep = columns_to_keep_transporter(company=company, transporter=transporter)
    # columns_to_keep = columns_to_keep.split(",")
    columns_to_keep = [x.strip(' ') for x in columns_to_keep]

    cols = [col for col in df.columns if col in columns_to_keep]

    # Keep new columns
    df = df[cols]
    # Removing last 5 rows
    df = df[:-5]

    # Replacing "," by "." to get actual integers (if need be)
    df[column_price] = df[column_price].replace({",": "."})

    # Grouping sums
    df = df.groupby([column_package_number], as_index=False).agg(
        {column_price: 'sum', column_prestation: 'first', column_weight: 'first'})


    # Cleaning data, i.e removing CAPS, spaces (replacing with "_") and removing accents
    df[column_prestation] = df[column_prestation].str.lower()
    df[column_prestation] = df[column_prestation].str.replace(' ', '_')
    df[column_prestation] = df[column_prestation].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode(
        'utf-8')

    return df.to_dict()


def parse_company_file(company_file):
    """ Parses COMPANY FILE and cleans it. """

    # Get company file
    df_creation = parse_file(company_file, extension=os.path.splitext(company_file.name)[1], header_row=2)
    df = pd.DataFrame(df_creation)
    df = df.dropna(subset='Date LT')

    return df.to_dict()


def parse_query_supplements(company, transporter):
    """ Retrieves SUPPLEMENT from queryset and cleans data. """

    # Getting variables
    supplement = Supplement.objects.get(company=company, transporter=transporter)
    query_supplements = Supplement.objects.filter(company=company, transporter=transporter).values()
    supplement_details = SupplementDetails.objects.get(supplement=supplement)
    columns_to_keep = supplement_details.columns_supplements
    columns_to_keep = list(columns_to_keep.keys())

    # Cleaning values
    df = pd.DataFrame(query_supplements)
    cols = [col for col in df.columns if col in columns_to_keep]
    df = df[cols]
    df = df.T
    df = df.reset_index()
    df.columns = ['Type prestation', 'Price transporter']

    return df.to_dict()


def parse_weights(company, transporter):
    """ Retrieves WEIGHTS from queryset and cleans data. """

    # Creating DF
    weight_id = Weight.objects.filter(company=company, transporter=transporter)
    query_weights = WeightPrices.objects.filter(weight__in=weight_id).values()
    df = pd.DataFrame(query_weights)


    # Processing columns
    weight_columns = Weight.objects.get(company=company, transporter=transporter)
    columns_to_keep = weight_columns.columns_to_keep
    columns_to_keep = list(columns_to_keep.keys())
    cols = [col for col in df.columns if col in columns_to_keep]

    # Final DF
    df = df[cols]


    return df.to_dict()


def analyze(transporter_file, company_file, company, transporter, **kwargs):
    """ Analyzes files and returns a dictionary with results. """
    """ Conducts analysis from all DF. """

    df_transporter = parse_transporter_file(transporter_file=transporter_file, company=company, transporter=transporter)
    df_company = parse_company_file(company_file=company_file)
    df_supplements = parse_query_supplements(company=company, transporter=transporter)
    df_weights = parse_weights(company=company, transporter=transporter)

    #Transforming into DF
    df_transporter = pd.DataFrame(df_transporter)
    df_company = pd.DataFrame(df_company)
    df_supplements = pd.DataFrame(df_supplements)
    df_weights = pd.DataFrame(df_weights)

    # Retrieves column 'Price'
    supplement = Supplement.objects.get(company=company, transporter=transporter)
    supplements_details = SupplementDetails.objects.get(supplement=supplement)
    column_price = supplements_details.column_price
    column_price = list(column_price.keys())
    column_price = ''.join(column_price)

    # Retrieve column 'Weight'
    column_weight = supplements_details.column_weight
    column_weight = list(column_weight.keys())
    column_weight = ''.join(column_weight)

    # Merging DFS
    df = df_transporter.merge(df_company, how='left')
    df2 = df.merge(df_supplements, how='left')
    df2.columns = df2.columns.str.replace(' ', '_')

    # df_weights['Poids'].astype(float) # Converting to float

    # Processing comparison
    weights_comparison = df2['Poids'].values # A MODIFIER
    min_weights_comparison = df_weights['min_weight'].values
    max_weights_comparison = df_weights['max_weight'].values

    i, j = np.where((weights_comparison[:, None] >= min_weights_comparison) & (
            weights_comparison[:, None] <= max_weights_comparison))

    df3 = pd.concat([
        df2.loc[i, :].reset_index(drop=True),
        df_weights.loc[j, :].reset_index(drop=True)], axis=1).append(
        df2[~np.in1d(np.arange(len(df2)), np.unique(i))],
        ignore_index=True, sort=False)

    df3.rename(columns={'price': 'Weight_price'}, inplace=True)
    df3['Price_transporter'] = df3['Price_transporter'].astype(float).fillna(0)
    df3['Weight_price'] = df3['Weight_price'].astype(float).fillna(0)
    df3['Result'] = df3['Price_transporter'] + df3['Weight_price']

    # Final result

    df3['IsSimilar'] = np.where(df3['Montant_HT'] == df3['Result'], 'Yes', 'No')



    return df3.to_dict()


def store_results(pk, transporter, data):

    """ Stores transporters results in database. """
    df = pd.DataFrame(data)
    report_id = Report.objects.get(pk=pk)
    report_details = ReportDetails.objects.create(report=report_id, transporter=transporter, data=df.to_json(), slug=get_random_string(length=32))

    return report_details.pk




# def download_data(request, **kwargs):
#
#     file = request.session['report_file']
#
#

# def export_report(request, company):
#
#
#
#     report_id = request.session['report_id']
#     n_title = request.session['date_f']
#     n_title = str(company) + " " + str(n_title)
#     n_report = Report.objects.filter(pk=report_id).update(result=df_report)  # Update result value
#     n_report_title = Report.objects.filter(pk=report_id).update(title=n_title)
#
#
#
#                   report_id = self.request.session['report_id']
#                   n_title = self.request.session['date_f']
#                   n_title = str(company) + " " + str(n_title)
#                   n_report = Report.objects.filter(pk=report_id).update(result=df_report)  # Update result value
#                   n_report_title = Report.objects.filter(pk=report_id).update(title=n_title)
#
#                   # Updating slug according to new data
#                   temp_slug = n_title + "-" + str(report_id)
#                   n_slug = Report.objects.filter(pk=report_id).update(slug=slugify(temp_slug))
#
# def parse_data(**kwargs):
#     """Parses file and return it for analysis"""
#
#     for key in kwargs:
#
#         company = kwargs['company']
#         transporter = kwargs['transporter']
#         extension = kwargs['extension']
#         file = kwargs['file']
#         header_row = kwargs['header_row']
#         columns_to_keep = kwargs['columns_to_keep']
#         # company_file = kwargs['company_file']
#
#
#         ''' ############################
#         First dataframe : TRANSPORTER
#         ############################
#         '''
#
#         if extension in ['.xls', '.xlsx']:
#             df = pd.read_excel(file, skiprows=header_row)
#
#             # Retrieving columns and cleaning names
#             columns_to_keep = str(columns_to_keep)
#             columns_to_keep = columns_to_keep.split(",")
#             columns_to_keep = [x.strip(' ') for x in columns_to_keep]
#
#             cols = [col for col in df.columns if col in columns_to_keep]
#
#             df = df[cols]
#             # Removing last 5 rows
#             df = df[:-5]
#             # Replacing "," by "." to get actual integers
#             df['Montant HT'] = df['Montant HT'].replace({",": "."})
#             # Grouping sums
#             df = df.groupby(['Numero LT'], as_index=False).agg(
#                 {'Montant HT': 'sum', 'Type prestation': 'first', 'Poids': 'first'})
#
#             df['Type prestation'] = df['Type prestation'].str.lower()  # Remove CAPS
#             df['Type prestation'] = df['Type prestation'].str.replace(' ',
#                                                                       '_')  # Remove spaces and replace them with "_"
#             df['Type prestation'] = df['Type prestation'].str.normalize('NFKD').str.encode('ascii',
#                                                                                            errors='ignore').str.decode(
#                 'utf-8')
#
#             ''' ############################
#             Second dataframe : COMPANY FILE
#             ############################
#             '''
#
#             df_company = pd.DataFrame.from_dict(company_file)
#             df_company = df_company.dropna(subset='Date LT')
#
#             ''' ############################
#             Third dataframe : SUPPLEMENTS
#             ############################
#             '''
#
#             columns_to_keep2 = ['supplement_annonce_incomplete', 'supplement_retour_expediteur',
#                                 'supplement_etiquette_non_conforme',
#                                 'supplement_zone_difficile_acces', 'supplement_corse', 'supplement_manutention',
#                                 'supplement_gt',
#                                 'supplement_carburant_routier', 'supplement_frais_de_gestion',
#                                 'supplement_facture_papier',
#                                 'supplement_surete_colis', 'supplement_zone_internationale_eloignee',
#                                 'supplement_surcharge_carburant_routier',
#                                 'supplement_covid', 'supplement_taxe_carbone']
#
#             query_supplements = Supplement.objects.filter(company=company, transporter=transporter).values()
#             df_tarifs = pd.DataFrame(query_supplements)
#             cols2 = [col for col in df_tarifs.columns if col in columns_to_keep2]
#             df_tarifs = df_tarifs[cols2]
#             df_tarifs = df_tarifs.T
#             df_tarifs = df_tarifs.reset_index()
#             df_tarifs.columns = ['Type prestation', 'Price transporter']
#             #
#             ''' ############################
#             Fourth dataframe : WEIGHT PRICES
#             ############################
#             '''
#
#             # WEIGHTS
#
#             weight_id = Weight.objects.filter(company=company, transporter=transporter)
#             query_weights = WeightPrices.objects.filter(weight__in=weight_id).values()
#             df_weight = pd.DataFrame(query_weights)
#             columns_to_keep3 = ['min_weight', 'max_weight',
#                                 'price']
#             cols3 = [col for col in df_weight.columns if col in columns_to_keep3]
#             df_weight = df_weight[cols3]
#
#             ''' ############################
#             Final dataframe : COMPARISON
#             ############################
#             '''
#             df3 = df_company.merge(df, how='left')
#             df4 = df3.merge(df_tarifs, how='left')
#             df4.columns = df4.columns.str.replace(' ', '_')
#             df4['Poids'].astype(float)
#
#             weights_comparison = df4['Poids'].values
#             min_weights_comparison = df_weight['min_weight'].values
#             max_weights_comparison = df_weight['max_weight'].values
#
#             i, j = np.where((weights_comparison[:, None] >= min_weights_comparison) & (
#                     weights_comparison[:, None] <= max_weights_comparison))
#
#             df5 = pd.concat([
#                 df4.loc[i, :].reset_index(drop=True),
#                 df_weight.loc[j, :].reset_index(drop=True)
#             ], axis=1).append(
#                 df4[~np.in1d(np.arange(len(df4)), np.unique(i))],
#                 ignore_index=True, sort=False
#             )
#
#             df5.rename(columns={'price': 'Weight_price'}, inplace=True)
#             df5['Price_transporter'] = df5['Price_transporter'].astype(float).fillna(0)
#             df5['Weight_price'] = df5['Weight_price'].astype(float).fillna(0)
#             df5['Result'] = df5['Price_transporter'] + df5['Weight_price']
#
#             ''' ############################
#             Final dataframe : RESULT
#             ############################
#             '''
#
#             df5['IsSimilar'] = np.where(df5['Montant_HT'] == df5['Result'], 'Yes', 'No')
#             df_report = df5.to_json()  # For the REPORT model
#             df_result = df5.to_dict()
#             # self.request.session['result'] = df_result
#
#             ''' ############################
#             We stock the result of the comparison within the REPORT model
#             ############################
#             '''
#
#             # print(df_report)
#             # report_id = self.request.session['report_id']
#             # n_title = self.request.session['date_f']
#             # n_title = str(company) + " " + str(n_title)
#             # n_report = Report.objects.filter(pk=report_id).update(result=df_report)  # Update result value
#             # n_report_title = Report.objects.filter(pk=report_id).update(title=n_title)
#             #
#             # # Updating slug according to new data
#             # temp_slug = n_title + "-" + str(report_id)
#             # n_slug = Report.objects.filter(pk=report_id).update(slug=slugify(temp_slug))
#
#             return df5.to_dict()
#
#
#
#
