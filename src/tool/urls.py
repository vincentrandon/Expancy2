from django.urls import path
from django.views.generic import TemplateView

from tool.views import UserSupplementView, UserSupplementTransporterView, \
    UserSupplementTransporterEditView, ResultView, CompareFormView, DownloadView, UserAddReportView, UserReportsView, \
    UserViewReport, TransporterFileFormPartialView, TransporterFileFormDetailView, TransporterFileFormDeleteView

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('upload-form/', TransporterFileFormPartialView.as_view(), name="upload-form"),
    path('upload-detail/<int:pk>', TransporterFileFormDetailView.as_view(), name="upload-detail"),
    path('upload-detail/<int:pk>/delete/', TransporterFileFormDeleteView.as_view(), name="upload-delete"),
    path('transporters/', UserSupplementView.as_view(), name="transporters"),
    path('transporters/<slug:slug>', UserSupplementTransporterView.as_view(), name="tarifs"),
    path('transporters/<slug:slug>/edit', UserSupplementTransporterEditView.as_view(), name="edit-tarifs"),
    path('result/', ResultView.as_view(), name='result'),
    path('download/', DownloadView.as_view(), name='download'),
    path('report/add-report', UserAddReportView.as_view(), name='add-report'),
    path('report/add-report/2', CompareFormView.as_view(), name='upload'),
    path('reports/', UserReportsView.as_view(), name='reports'),
    path('reports/<slug:slug>', UserViewReport.as_view(), name='single-report'),
]