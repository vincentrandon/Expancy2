from django.contrib import admin

# Register your models here.
from tool.models import TransporterFile, CompanyFile


class CustomTransporterFileAdmin(admin.ModelAdmin):

    list_display = ['transporter']
    model = TransporterFile

admin.site.register(TransporterFile, CustomTransporterFileAdmin)

class CustomCompanyFileAdmin(admin.ModelAdmin):

    list_display = ['company']
    model = CompanyFile

admin.site.register(CompanyFile, CustomCompanyFileAdmin)