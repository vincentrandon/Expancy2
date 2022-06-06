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

from accounts.models import Transporter, Supplement, Weight, WeightPrices, Company
from reports.models import Report
from tool.helpers import parse_excel, parse_csv, parse_xml, validate_file_extension
from tool.models import TransporterFile, CompanyFile


class TransporterFileForm(forms.ModelForm):

    class Meta:
        model = TransporterFile
        fields = ('file', )
        widgets = {
        'file': forms.FileInput(attrs={'onchange': 'submit();'})
        }



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


