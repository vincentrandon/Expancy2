import os
from pprint import pprint

from django import forms

from tool.helpers import parse_excel, parse_csv, parse_xml
from tool.models import CheckFile


class CompareFormCommandes(forms.ModelForm):
    file = forms.FileField(label="Fichier CSV", required=True)

    class Meta:
        model = CheckFile
        fields = ['file',]

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        super().clean()
        extension = os.path.splitext(self.request.FILES['file'].name)[1]
        print(extension)
        if extension in ['.xlsx', '.xls']:
            uploaded = parse_excel(self.request.FILES['file'])
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
        print(columns)

        return [int(column) for column in columns]

    def clean(self):
        super().clean()
        print(self.cleaned_data['columns'])
        self.request.session['selection'] = self.cleaned_data.get('columns')
        print(self.request.session['selection'])