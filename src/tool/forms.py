from pprint import pprint

from django import forms

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
        self.request.session['uploaded'] = uploaded
        self.request.session['profile'] = self.cleaned_data.get('profile')