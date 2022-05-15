from django.contrib import admin

# Register your models here.
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportMixin, ImportExportModelAdmin
from nested_admin.nested import NestedStackedInline, NestedModelAdmin, NestedTabularInline

from accounts.forms import CustomImportForm, CustomConfirmImportForm
from accounts.models import Transporter, User, Supplement, Company, Brand, Weight, WeightPrices, Report


class CustomTransporterAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_tag']
    model = Transporter


admin.site.register(Transporter, CustomTransporterAdmin)

''' USERS '''

class CustomUserAdmin(admin.ModelAdmin):

    def change_button(self, obj):
        return format_html('<a class="btn" href="/admin/accounts/user/{}/change/">Edit</a>', obj.id)

    list_display = ['email', 'first_name', 'last_name', 'change_button']
    #list_filter = ['email']
    model = User

admin.site.register(User, CustomUserAdmin)


''' COMPANIES '''
class CustomCustomerAdmin(admin.ModelAdmin):
    list_display = ['name']
    model = Company

admin.site.register(Company, CustomCustomerAdmin)


''' SUPPLEMENTS '''

class CustomSupplementAdmin(ImportExportModelAdmin, admin.ModelAdmin):

    list_display = ['company', 'transporter']
    list_filter = ['company']
    model = Supplement
    # form = ColumnsForm

    def get_import_form(self):
        return CustomImportForm

    def get_confirm_import_form(self):
        return CustomConfirmImportForm

    # def get_form_kwargs(self, form, *args, **kwargs):
    #     # pass on `author` to the kwargs for the custom confirm form
    #     if isinstance(form, CustomImportForm):
    #         if form.is_valid():
    #             Supplement = form.cleaned_data['Supplement']
    #             kwargs.update({'Supplement': Supplement.id})
    #     return kwargs


admin.site.register(Supplement, CustomSupplementAdmin)






''' BRANDS '''

class CustomBrandAdmin(admin.ModelAdmin):

    list_display = ['name', 'company']
    list_filter = ['company']
    model = Brand

admin.site.register(Brand, CustomBrandAdmin)


''' WEIGHTS '''

class AdminWeightPrices(NestedTabularInline):
    model = WeightPrices


class CustomWeightAdmin(NestedModelAdmin):

    list_display = ['company', 'transporter']
    list_filter = ['company']
    model = Weight
    inlines = [AdminWeightPrices]

admin.site.register(Weight, CustomWeightAdmin)


''' REPORT '''
class CustomReportAdmin(admin.ModelAdmin):

    list_display = ['title', 'company']
    list_filter = ['company']
    model = Report

admin.site.register(Report, CustomReportAdmin)