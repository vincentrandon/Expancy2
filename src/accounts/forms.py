from django import forms
from django.forms import ModelForm
from import_export.forms import ImportForm, ConfirmImportForm

from accounts.models import Supplement, User

''' FORM POUR L'ADMIN '''

class CustomImportForm(ImportForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True)

    def __str__(self):
        return User.first_name

class CustomConfirmImportForm(ConfirmImportForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True)

    def __str__(self):
        return User.first_name


''''''


