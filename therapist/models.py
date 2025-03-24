from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
import uuid

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

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    therapist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='therapist_orders')
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_orders')
    service_type = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

class Earnings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='last_message_for')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']