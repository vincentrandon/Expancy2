import calendar

from bootstrap_modal_forms.forms import BSModalModelForm
from django import forms

from reports.models import Report


class ReportForm(forms.ModelForm):
    """ Form to create a report. """

    date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Report
        fields = ['title', 'company', ]

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        user = self.request.user
        self.initial['company'] = user.company

    def clean(self):
        super().clean()
        filtered_date = self.cleaned_data.get('date')
        month = filtered_date.month
        month = calendar.month_name[month]
        year = filtered_date.year
        date_f = str(month) + " " + str(year)
        print(self.instance)
        self.request.session['date_f'] = date_f