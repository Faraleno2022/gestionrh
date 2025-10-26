from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.profile_view, name='users'),
    path('parametres/', views.profile_view, name='parametres'),
    
    # Multi-entreprise
    path('register-entreprise/', views.register_entreprise, name='register_entreprise'),
    path('reauth/', views.reauth_view, name='reauth'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('send-invitation/', views.send_invitation, name='send_invitation'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('entreprise-settings/', views.entreprise_settings, name='entreprise_settings'),
]
