from django.urls import path
from django.views.generic import TemplateView

from tool.views import UserSupplementView, UserSupplementTransporterView, \
    UserSupplementTransporterEditView, ResultView, DownloadView, UserAddReportView, UserReportsView, \
    UserViewReport, TransporterFileFormPartialView, \
    UploadView, UploadCompanyFileView

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('report/add-report', UserAddReportView.as_view(), name='add-report'),
    path('report/add-report/2', UploadView.as_view(), name='upload'),
    path('report/add-report/3', UploadCompanyFileView.as_view(), name='upload-company-file'),
    path('upload-form/', TransporterFileFormPartialView.as_view(), name="upload-form"),
    path('transporters/', UserSupplementView.as_view(), name="transporters"),
    path('transporters/<slug:slug>', UserSupplementTransporterView.as_view(), name="tarifs"),
    path('transporters/<slug:slug>/edit', UserSupplementTransporterEditView.as_view(), name="edit-tarifs"),
    path('result/', ResultView.as_view(), name='result'),
    path('download/', DownloadView.as_view(), name='download'),

    path('reports/', UserReportsView.as_view(), name='reports'),
    path('reports/<slug:slug>', UserViewReport.as_view(), name='single-report'),
]