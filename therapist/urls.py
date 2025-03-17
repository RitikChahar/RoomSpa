from django.urls import path
from . import views

urlpatterns = [
    path('location/', views.location_view, name='therapist_location'),
    path('pictures/', views.pictures_view, name='therapist_pictures'),
    path('services/', views.services_view, name='therapist_services'),
    path('bank-details/', views.bank_details_view, name='therapist_bank_details'),
    path('profile/', views.therapist_profile_view, name='therapist_profile'),
]