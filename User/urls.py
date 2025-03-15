from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('user-profile/', views.get_user_profile, name='get_user_profile'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-email/', views.email_verification, name='email_verification'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('verify-token/', views.verify_token, name='verify_token'),  
    path('refresh-token/', views.refresh_token, name='refresh_token'),  
    path('update-profile/', views.update_user_profile, name='update_profile'),
    path('update-email/', views.update_email, name='update_email'),
    path('update-phone/', views.update_phone, name='update_phone'),
    path('delete-profile/', views.delete_user_profile, name='delete_profile'),
]