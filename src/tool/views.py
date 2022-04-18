from django.shortcuts import render

# Create your views here.
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView, CreateView

from tool.forms import CompareFormCommandes


class RequestFormMixin:
    """Mixin to inject the request in the form."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

class FormCompare(RequestFormMixin, CreateView):
    """Implémente la première étape: le téléchargement du fichier."""

    template_name = 'tool/upload-fichier-commandes.html'
    form_class = CompareFormCommandes
    success_url = reverse_lazy('tool:upload-columns-selection')
