from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView, CreateView, FormView, DetailView, ListView, UpdateView

from accounts.models import User, Supplement
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

class UserSupplementView(TemplateView):

    model = User
    template_name = 'tool/transporters.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['supplements'] = user.company.supplement_set.all()
        print(context['supplements'])
        return context

class UserSupplementTransporterView(TemplateView):
    model = Supplement
    template_name = 'tool/transporter-detail.html'
    context_object_name = "tarifs"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs['slug']
        context['supplement'] = get_object_or_404(Supplement, slug=slug)
        return context

class UserSupplementTransporterEditView(UpdateView):
    model = Supplement
    template_name = 'tool/transporter-detail.html'
    context_object_name = "edit-tarifs"


