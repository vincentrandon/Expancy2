from django.db import models

# Create your models here.
from tool.helpers import validate_file_extension

PROFILE_CHOICES = [
    ('CLI', 'Client'),
    ('TRP', 'Transporteur'),
]

class CheckFile(models.Model):
    name = models.CharField(max_length=200, blank=True) #devra être rempli automatiquement avec le nom de l'entreprise + timestamp
    month = models.DateField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    header_row = models.IntegerField('Numéro de ligne où sont contenus les titres de colonnes (si vide = 1)', default=1)
    profile = models.CharField('Choix du profil', blank=False, choices=PROFILE_CHOICES, max_length=100, default="Client")
    file = models.FileField(blank=True, null=True, upload_to="uploads/", validators=[validate_file_extension])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "file"
        verbose_name_plural = "files"