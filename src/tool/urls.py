from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from reports.views import UserAddReportView, UserReportsView, UserViewReport
from tool.views import UserSupplementView, UserSupplementTransporterView, \
    UserSupplementTransporterEditView, ResultView, DownloadView, \
    UploadView, UploadCompanyFileView

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('reports/add-report', UserAddReportView.as_view(), name='add-report'),
    path('reports/add-report/2', UploadView.as_view(), name='upload'),
    path('reports/add-report/3', UploadCompanyFileView.as_view(), name='upload-company-file'),
    path('transporters/', UserSupplementView.as_view(), name="transporters"),
    path('transporters/<slug:slug>', UserSupplementTransporterView.as_view(), name="tarifs"),
    path('transporters/<slug:slug>/edit', UserSupplementTransporterEditView.as_view(), name="edit-tarifs"),
    path('result/', ResultView.as_view(), name='result'),
    path('download/<slug:slug>', DownloadView.as_view(), name='download'),
    path('reports/', UserReportsView.as_view(), name='reports'),
    path('reports/<slug:slug>', UserViewReport.as_view(), name='single-report'),
]