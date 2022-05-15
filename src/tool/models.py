from django.db import models

# Create your models here.
from accounts.models import Transporter, Company
from tool.helpers import validate_file_extension

PROFILE_CHOICES = [
    ('CLI', 'Client'),
    ('TRP', 'Transporteur'),
]

class CheckFile(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)
    file_transporter = models.FileField('Insertion fichier transporteur', null=True)
    name_transporter = models.ForeignKey(Transporter, on_delete=models.CASCADE, blank=True, null=True)
    company_file = models.FileField('Insertion fichier transporteur', null=True)


    def __str__(self):
        return self.name_transporter

    class Meta:
        verbose_name = "file"
        verbose_name_plural = "files"


