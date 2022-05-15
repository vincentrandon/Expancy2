from django.contrib import admin

# Register your models here.
from tool.models import CheckFile


class CustomFileAdmin(admin.ModelAdmin):
    list_display = ['name_transporter']
    model = CheckFile

admin.site.register(CheckFile, CustomFileAdmin)