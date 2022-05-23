from django.db import models

# Create your models here.
from accounts.models import Transporter, Company, User, Report
from tool.helpers import validate_file_extension

PROFILE_CHOICES = [
    ('CLI', 'Client'),
    ('TRP', 'Transporteur'),
]

class CompanyFile(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    file = models.FileField('Insertion fichier des commandes', null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return str(self.name)


    class Meta:
        verbose_name = "Company File"
        verbose_name_plural = "Company Files"


class TransporterFile(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    file = models.FileField('Insertion fichier transporteur', null=True, blank=False)
    transporter = models.ForeignKey(Transporter, on_delete=models.CASCADE, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return str(self.transporter)

    class Meta:
        verbose_name = "Transporter File"
        verbose_name_plural = "Transporter Files"
