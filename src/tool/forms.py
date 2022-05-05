import os
from pprint import pprint

from django import forms

from tool.helpers import parse_excel, parse_csv, parse_xml
from tool.models import CheckFile


class CompareFormTransporteur(forms.ModelForm):
    file = forms.FileField(label="Fichier (CSV, XLSX, XML) ", required=True)
    header_row = forms.IntegerField(label="Header row", required=True)


    class Meta:
        model = CheckFile
        fields = ['file',]

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.request.session['header_row'] = self['header_row'].value()
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        extension = os.path.splitext(self.request.FILES['file'].name)[1]
        integer = self.request.session['header_row']
        print(integer)
        if extension in ['.xlsx', '.xls']:
            uploaded = parse_excel(self.request.FILES['file'], rowheader=2)
        elif extension == ".csv":
            uploaded = parse_csv(self.request.FILES['file'])
        elif extension == ".xml":
            uploaded = parse_xml(self.request.FILES['file'])

        self.request.session['uploaded'] = uploaded
        self.request.session['profile'] = self.cleaned_data.get('profile')

class CompareFormPartTwo(forms.Form):
    columns = forms.MultipleChoiceField(label="Colonnes", widget=forms.CheckboxSelectMultiple())

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.uploaded = request.session['uploaded']
        columns_choices = []
        for key in enumerate(self.uploaded):
            columns_choices.append(key)

        self.fields['columns'].choices = columns_choices

    def clean_columns(self):
        """Valide les données sur les columns et transforme les choix en int."""
        columns = self.cleaned_data['columns']

        return [int(column) for column in columns]

    def clean(self):
        super().clean()
        self.request.session['selection'] = self.cleaned_data.get('columns')
        print(self.request.session['selection'])