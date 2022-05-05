import os
import pandas as pd
from django.core.exceptions import ValidationError
from django.http import JsonResponse


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
