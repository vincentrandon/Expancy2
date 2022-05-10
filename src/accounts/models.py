from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.postgres.fields import ArrayField
from django.core.mail import send_mail
from django.db import models

# Create your models here.


from django.db.models import DO_NOTHING, JSONField
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.safestring import mark_safe
from django_extensions.db.fields import AutoSlugField
from multiselectfield import MultiSelectField

from tool.models import CheckFile


########################################
# Classe dédiée au modèle utilisateurs
########################################

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField('username', max_length=30, blank=True)
    email = models.EmailField('Adresse mail', unique=True)
    first_name = models.CharField('Prénom', max_length=30, blank=True)
    last_name = models.CharField('Nom', max_length=30, blank=True)
    date_joined = models.DateTimeField('date joined', auto_now_add=True)
    company = models.ForeignKey('Company', on_delete=DO_NOTHING, blank=True, null=True)
    is_active = models.BooleanField('active', default=True)
    is_staff = models.BooleanField('staff status', default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def get_full_name(self):
        '''
        Returns the first_name plus the last_name, with a space in between.
        '''
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        '''
        Returns the short name for the user.
        '''
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        '''
        Sends an email to this User.
        '''
        send_mail(subject, message, from_email, [self.email], **kwargs)


################################
# Classe dédiée aux transporteurs
################################

class Transporter(models.Model):
    name = models.CharField(max_length=100)
    avatar = models.ImageField(blank=True, null=True)

    def __str__(self):
        return self.name

    def image_tag(self):
        if self.avatar:
            return mark_safe('<img src="%s" style="width: 150px; height:150px;" />' % self.avatar.url)
        else:
            return 'No Image Found'

    image_tag.short_description = 'Image'

    class Meta:
        verbose_name_plural = "transporters"


########################################
# Classe dédiée aux clients (entreprises)
########################################

class Company(models.Model):
    name = models.CharField(max_length=200, blank=False)
    transporters = models.ManyToManyField(Transporter, blank=True)

    # employees = User.objects.filter(company=company)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"


class Brand(models.Model):
    name = models.CharField(max_length=100, blank=False)
    company = models.ForeignKey(Company, on_delete=DO_NOTHING, blank=False, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"



class Supplement(models.Model):

    PROFILE_CHOICES_CHRONOPOST = [
        (1, 'No Facture'),
        (2, 'Sous-compte'),
        (3, 'Date LT'),
        (4, 'Code postal depart'),
        (5, 'Code postal arrivee'),
        (6, 'Pays depart'),
        (7, 'Pays arrivee'),
        (8, 'Ref Destinataire'),
        (9, 'Ref Expediteur'),
        (10, 'No Groupage tarifaire'),
        (11, 'Numero LT'),
        (12, 'Groupage'),
        (13, 'Type prestation'),
        (14, 'TVA'),
        (15, 'Observations'),
        (16, 'Zone Tarifaire'),
        (17, 'Poids'),
        (18, 'Produit'),
        (19, 'Montant HT'),
        (20, 'Raison sociale'),
        (21, 'Raison sociale 2'),
    ]

    PROFILE_CHOICES_DPD = [
        (1, 'Coucou'),
    ]

    transporter = models.ForeignKey(Transporter, on_delete=DO_NOTHING, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=DO_NOTHING, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=DO_NOTHING, blank=True, null=True)
    header_row = models.IntegerField(blank=True, null=True)
    supplement_annonce_incomplete = models.DecimalField('Supplément annonce incomplète', max_digits=7, decimal_places=3,
                                                        blank=True, null=True)
    supplement_retour_expediteur = models.DecimalField('Supplément Retour Expéditeur', max_digits=7, decimal_places=3,
                                                       blank=True, null=True)
    supplement_etiquette_non_conforme = models.DecimalField('Supplément Etiquette non-conforme', max_digits=7,
                                                            decimal_places=3, blank=True, null=True)
    supplement_zone_difficile_acces = models.DecimalField('Supplément zone difficile d\'accès', max_digits=7,
                                                          decimal_places=3, blank=True, null=True)
    supplement_corse = models.DecimalField('Supplément Corse', max_digits=7, decimal_places=3, blank=True, null=True)
    supplement_manutention = models.DecimalField('Supplément manutention', max_digits=7, decimal_places=3, blank=True,
                                                 null=True)
    supplement_gt = models.DecimalField('Supplément GT', max_digits=7, decimal_places=3, blank=True, null=True)
    supplement_carburant_routier = models.DecimalField('Supplément carburant routier', max_digits=7, decimal_places=3,
                                                       blank=True, null=True)
    supplement_frais_de_gestion = models.DecimalField('Supplément frais de gestion', max_digits=7, decimal_places=3,
                                                      blank=True, null=True)
    supplement_facture_papier = models.DecimalField('Supplément facture papier', max_digits=7, decimal_places=3,
                                                    blank=True, null=True)
    supplement_surete_colis = models.DecimalField('Supplément facture colis', max_digits=7, decimal_places=3,
                                                  blank=True, null=True)
    supplement_zone_internationale_eloignee = models.DecimalField('Supplément zone internationale éloignée',
                                                                  max_digits=7, decimal_places=3, blank=True, null=True)
    supplement_surcharge_carburant_routier = models.DecimalField('Supplément surcharge carburant routier', max_digits=7,
                                                                 decimal_places=3, blank=True, null=True)
    supplement_covid = models.DecimalField('Supplément COVID', max_digits=7, decimal_places=3, blank=True, null=True)
    supplement_taxe_carbone = models.DecimalField('Supplément taxe carbone', max_digits=7, decimal_places=3, blank=True,
                                                  null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    columns_to_keep = MultiSelectField(choices=PROFILE_CHOICES_CHRONOPOST, blank=True, null=True)


    #Titre de la page
    def __str__(self):
        if self.brand:
            return "[" + str(self.company) + " - " + str(self.brand) + "] " + str(self.transporter)
        else:
            return "[" + str(self.company) + "] " + str(self.transporter)

    #URL du supplément créé
    def get_absolute_url(self):
        return reverse("transporter-detail", kwargs={"slug": self.slug})

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if self:
    #         print(self.columns_to_keep)

    def save(self, *args, **kwargs):
        if not self.slug:
            if self.brand:
                self.slug = slugify(
                    str("tarifs-") + str(self.company) + "-" + str(self.brand) + "-" + str(self.transporter))
            else:
                self.slug = slugify(str("tarifs-") + str(self.company) + "-" + str(self.transporter))

        elif 'none' in self.slug:
            if self.brand:
                self.slug = slugify(
                    str("tarifs-") + str(self.company) + "-" + str(self.brand) + "-" + str(self.transporter))
            else:
                self.slug = slugify(str("tarifs-") + str(self.company) + "-" + str(self.transporter))


        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Supplément"
        verbose_name_plural = "Suppléments"


class Weight(models.Model):
    transporter = models.ForeignKey(Transporter, on_delete=DO_NOTHING, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=DO_NOTHING, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=DO_NOTHING, blank=True, null=True)


    def __str__(self):
        if self.brand:
            return "Poids [" + str(self.company) + " - " + str(self.brand) + "] " + str(self.transporter)
        else:
            return "Poids [" + str(self.company) + "] " + str(self.transporter)


    class Meta:
        verbose_name = "Weight"
        verbose_name_plural = "Weights"

class WeightPrices(models.Model):
    weight = models.ForeignKey(Weight, on_delete=DO_NOTHING, blank=False, null=True)
    min_weight = models.FloatField('Min weight', blank=False, null=True)
    max_weight = models.FloatField('Max weight', blank=False, null=True)
    price = models.FloatField('Price', blank=False, null=True)

    class Meta:
        verbose_name = "Weight Price"
        verbose_name_plural = "Weight Prices"