from django.urls import path
from django.views.generic import TemplateView

from tool.forms import CompareFormCommandes
from tool.views import FormCompareCommandes, FormColumnSelection

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('test/', TemplateView.as_view(template_name="tool/test.html"), name="test"),
    path('upload/', TemplateView.as_view(template_name="tool/upload.html"), name="upload"),
    path('upload-fichier-commandes/', FormCompareCommandes.as_view(), name="upload-fichier-commandes"),
    path('upload-columns-selection/', FormColumnSelection.as_view(), name="upload-columns-selection"),
]