from django.urls import path
from django.views.generic import TemplateView

from tool.views import UserSupplementView, UserSupplementTransporterView, \
    UserSupplementTransporterEditView, ResultView, CompareFormView

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('transporters/', UserSupplementView.as_view(), name="transporters"),
    path('transporters/<slug:slug>', UserSupplementTransporterView.as_view(), name="tarifs"),
    path('transporters/<slug:slug>/edit', UserSupplementTransporterEditView.as_view(), name="edit-tarifs"),
    path('result/', ResultView.as_view(), name='result'),
    path('upload/', CompareFormView.as_view(), name='upload'),
]