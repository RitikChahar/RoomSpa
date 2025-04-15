from django.urls import path
from . import views

urlpatterns = [
    path('address/', views.customer_address_view, name='customer_address'),
    path('book/', views.book_therapist, name='book_therapist'),
    path('therapist/<int:therapist_id>/', views.therapist_detail_view, name='therapist_detail'),
    path('cancel-booking/<uuid:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('profile/', views.customer_profile_view, name='customer_profile'),
    path('search/', views.search_therapists_view, name='search_therapists'),
]