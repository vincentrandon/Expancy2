import os
from pprint import pprint

import pandas as pd
from django import forms

from accounts.models import Transporter, Supplement
from tool.helpers import parse_excel, parse_csv, parse_xml, validate_file_extension
from tool.models import CheckFile


class CompareFormTransporterCompany(forms.ModelForm):
    file = forms.FileField(label="File (CSV, XLSX, XML) ")
    name_transporter = forms.ModelChoiceField(label='Choose transporter', queryset=Transporter.objects.all())

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
        columns_to_keep = str(supplement.columns_to_keep)
        columns_to_keep = columns_to_keep.split(",")
        columns_to_keep = [x.strip(' ') for x in columns_to_keep]
        uploaded = parse_excel(self.request.FILES['file'], rowheader=rowheader)
        self.request.session['uploaded'] = uploaded

        df = pd.DataFrame.from_dict(uploaded)
        cols = [col for col in df.columns if col in columns_to_keep]
        df = df[cols]
        pprint(df)




