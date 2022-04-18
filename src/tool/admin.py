from django.contrib import admin

# Register your models here.
from tool.models import CheckFile


class CustomFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'month', 'timestamp', 'file',]
    model = CheckFile

admin.site.register(CheckFile, CustomFileAdmin)