from django.urls import path
from django.views.generic import TemplateView

app_name = "tool"

urlpatterns = [
    path('', TemplateView.as_view(template_name="tool/home.html"), name="home"),
    path('upload/', TemplateView.as_view(template_name="tool/upload.html"), name="upload"),
]