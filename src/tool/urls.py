from django.urls import path
from django.views.generic import TemplateView

from tool.views import FormColumnSelection, UserSupplementView, UserSupplementTransporterView, \
    UserSupplementTransporterEditView, FormCompareTransporteur, ResultView

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('transporters/', UserSupplementView.as_view(), name="transporters"),
    path('transporters/<slug:slug>', UserSupplementTransporterView.as_view(), name="tarifs"),
    path('transporters/<slug:slug>/edit', UserSupplementTransporterEditView.as_view(), name="edit-tarifs"),
    path('upload-fichier-transporteur/', FormCompareTransporteur.as_view(), name="upload-fichier-transporteur"),
    path('upload-columns-selection/', FormColumnSelection.as_view(), name="upload-columns-selection"),
    path('result/', ResultView.as_view(), name='result'),
]