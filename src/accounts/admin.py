from django.contrib import admin

# Register your models here.
from django.utils.html import format_html

from accounts.models import Transporter, User, Supplement, Company, Brand


class CustomTransporterAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_tag']
    model = Transporter


admin.site.register(Transporter, CustomTransporterAdmin)

class CustomCustomerAdmin(admin.ModelAdmin):
    list_display = ['name']
    model = Company

admin.site.register(Company, CustomCustomerAdmin)

class CustomUserAdmin(admin.ModelAdmin):

    def change_button(self, obj):
        return format_html('<a class="btn" href="/admin/accounts/user/{}/change/">Edit</a>', obj.id)

    list_display = ['email', 'first_name', 'last_name', 'change_button']
    #list_filter = ['email']
    model = User

admin.site.register(User, CustomUserAdmin)

class CustomSupplementAdmin(admin.ModelAdmin):

    list_display = ['company', 'transporter']
    list_filter = ['company']
    model = Supplement

admin.site.register(Supplement, CustomSupplementAdmin)



#Marques

class CustomBrandAdmin(admin.ModelAdmin):

    list_display = ['name', 'company']
    list_filter = ['company']
    model = Brand

admin.site.register(Brand, CustomBrandAdmin)