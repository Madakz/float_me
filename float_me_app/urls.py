from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
#import for customizing password reset
from .views import CustomPasswordResetView


urlpatterns = [
    path('', views.index, name='landing_page'),
    # user dashboard urls
    path('user/', views.home, name='user_dashboard'),
    # admin dashboard urls
    path('admin_dashboard/', views.admin_dash, name='admin_dashboard'), 
    # superadmin dashboard urls
    path('superadmin_dashboard/', views.superadmin_dash, name='superadmin_dashboard'), 
    # signup or register urls
    path('register/', views.register, name='signup'),
    # login urls
    path('login/', views.signin, name='signin'),
    # logout urls
    path('logout/', views.user_logout, name='logout'),

    # Password reset views
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    #for user subscription
    path('create_subscription/', views.subscribing, name='subscribe'),
    path('user_subscriptions/', views.user_subscriptions, name='user_subscriptions'),
    path('cancel_subscription/<int:subscription_id>', views.cancel_subscription, name="cancel_subscription"),
    path('user_payments/', views.user_payments, name='my_payments'),
    path('user_payouts/', views.user_payouts, name='my_payouts'),
    path('add_bank_details', views.user_bank, name='add_bank'),

    # Admin activate subscription
    path('admin_dashboard/activate_subscription/<int:subscription_user_id>/<int:subscription_id>/<str:amount_paid>/', views.activate_subscription, name='activate_subscription'),

    # Admin create payout record for matured subscription
    path('admin_dashboard/payout_subscription/<int:user_id>/<int:subscription_id>/<str:amount_paid>/', views.payout_matured_subscriptions, name='payout_matured_subscription'),
    
    # Admin authorise payout payment to matured subscription user account
    path('admin_dashboard/payout_to_user/<int:payout_id>/<int:user_id>/<str:amount>/', views.authorize_payouts, name='authorize_payout_payment'),
    
]