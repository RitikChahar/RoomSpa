from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class Location(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_location')
    address = models.TextField()
    service_radius = models.DecimalField(max_digits=5, decimal_places=2, help_text="Service radius in kilometers")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

class Pictures(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_pictures')
    profile_picture = models.URLField()
    more_pictures = ArrayField(models.URLField(), blank=True, default=list)
    certificate = models.URLField()
    national_id = models.URLField()

class Services(models.Model):
    SERVICE_CHOICES = [
        ('foot', 'Foot Massage'),
        ('thai', 'Thai Massage'),
        ('oil', 'Oil Massage'),
        ('aroma', 'Aroma Therapy'),
        ('4_hands_oil', '4 Hands Oil Massage'),
        ('pedicure', 'Pedicure/Manicure'),
        ('nails', 'Nails'),
        ('hair', 'Hair Fan'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_services')
    services = ArrayField(
        models.CharField(max_length=20, choices=SERVICE_CHOICES),
        blank=True,
        default=list
    )

class BankDetails(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_bank_details')
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    swift_code = models.CharField(max_length=50)