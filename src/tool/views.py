from django.shortcuts import render

# Create your views here.
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView, CreateView, FormView, DetailView

from accounts.models import User
from tool.forms import CompareFormCommandes, CompareFormPartTwo


class RequestFormMixin:
    """Mixin to inject the request in the form."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

class FormCompareCommandes(RequestFormMixin, CreateView):
    """Implémente la première étape : le téléchargement du fichier."""

    template_name = 'tool/upload-fichier-commandes.html'
    form_class = CompareFormCommandes
    success_url = reverse_lazy('tool:upload-columns-selection')

class FormColumnSelection(RequestFormMixin, FormView):
    """Implémente la seconde étape: le choix multiple dynamique -> choix des colonnes """

    template_name = 'tool/upload-columns-selection.html'
    form_class = CompareFormPartTwo
    success_url = reverse_lazy('tool:result')

class UserDetailView(DetailView):

    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()

        return context
