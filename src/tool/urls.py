from django.urls import path
from django.views.generic import TemplateView

from tool.views import FormColumnSelection, UserSupplementView, UserSupplementTransporterView, \
    UserSupplementTransporterEditView, FormCompareTransporteur

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('transporters/', UserSupplementView.as_view(), name="transporters"),
    path('transporters/<slug:slug>', UserSupplementTransporterView.as_view(), name="tarifs"),
    path('transporters/<slug:slug>/edit', UserSupplementTransporterEditView.as_view(), name="edit-tarifs"),
    path('upload/', TemplateView.as_view(template_name="tool/upload.html"), name="upload"),
    path('upload-fichier-transporteur/', FormCompareTransporteur.as_view(), name="upload-fichier-transporteur"),
    path('upload-columns-selection/', FormColumnSelection.as_view(), name="upload-columns-selection"),
]