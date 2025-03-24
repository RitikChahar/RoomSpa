from django.urls import path
from . import views

urlpatterns = [
    path('location/', views.location_view, name='therapist_location'),
    path('pictures/', views.pictures_view, name='therapist_pictures'),
    path('services/', views.services_view, name='therapist_services'),
    path('bank-details/', views.bank_details_view, name='therapist_bank_details'),
    path('profile/', views.therapist_profile_view, name='therapist_profile'),
    path('orders/incoming/', views.incoming_orders_view, name='incoming_orders'),
    path('orders/<uuid:order_id>/', views.order_detail_view, name='order_detail'),
    path('orders/<uuid:order_id>/update/', views.update_order_view, name='update_order'),
    path('orders/<uuid:order_id>/accept/', views.accept_order_view, name='accept_order'),
    path('orders/<uuid:order_id>/start/', views.start_service_view, name='start_service'),
    path('orders/<uuid:order_id>/complete/', views.complete_order_view, name='complete_order'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
    path('earnings/', views.earnings_summary_view, name='earnings_summary'),
    path('conversations/', views.conversations_view, name='conversations'),
    path('conversations/<int:conversation_id>/', views.conversation_detail_view, name='conversation_detail'),
    path('conversations/<int:conversation_id>/messages/', views.send_message_view, name='send_message'),
    path('stats/', views.therapist_stats_view, name='therapist_stats'),
    path('reviews/', views.therapist_reviews_list, name='therapist_reviews_list'),
    path('reviews/summary/', views.therapist_review_summary, name='therapist_review_summary'),
    path('reviews/<int:review_id>/', views.therapist_review_detail, name='therapist_review_detail'),
    path('reviews/create/', views.post_therapist_review, name='post_therapist_review'),
]