from django.urls import path
from . import views
from .views_modules import cnss, expatries, inspection

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
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('send-invitation/', views.send_invitation, name='send_invitation'),
    
    # Superuser - contrôle global
    path('superuser/users/', views.superuser_manage_users, name='superuser_manage_users'),
    path('superuser/toggle-user/<int:user_id>/', views.superuser_toggle_user, name='superuser_toggle_user'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('entreprise-settings/', views.entreprise_settings, name='entreprise_settings'),
    
    # CNSS Télédéclaration
    path('cnss/', cnss.cnss_dashboard, name='cnss_dashboard'),
    path('cnss/configuration/', cnss.cnss_configuration, name='cnss_configuration'),
    path('cnss/generer/', cnss.cnss_generer_declaration, name='cnss_generer'),
    path('cnss/<int:pk>/', cnss.cnss_detail, name='cnss_detail'),
    path('cnss/<int:pk>/telecharger/', cnss.cnss_telecharger, name='cnss_telecharger'),
    path('cnss/<int:pk>/transmis/', cnss.cnss_marquer_transmis, name='cnss_marquer_transmis'),
    path('cnss/historique/', cnss.cnss_historique, name='cnss_historique'),
    
    # Gestion des expatriés
    path('expatries/', expatries.expatries_liste, name='expatries_liste'),
    path('expatries/ajouter/', expatries.expatrie_ajouter, name='expatrie_ajouter'),
    path('expatries/<int:pk>/', expatries.expatrie_detail, name='expatrie_detail'),
    path('expatries/<int:pk>/modifier/', expatries.expatrie_modifier, name='expatrie_modifier'),
    path('expatries/<int:expatrie_id>/permis/ajouter/', expatries.permis_ajouter, name='permis_ajouter'),
    path('expatries/permis/<int:pk>/modifier/', expatries.permis_modifier, name='permis_modifier'),
    path('expatries/alertes/', expatries.alertes_expatries, name='alertes_expatries'),
    
    # Inspection du travail
    path('inspection/', inspection.inspection_dashboard, name='inspection_dashboard'),
    path('inspection/registres/', inspection.registres_liste, name='registres_liste'),
    path('inspection/registres/ajouter/', inspection.registre_ajouter, name='registre_ajouter'),
    path('inspection/registres/<int:pk>/modifier/', inspection.registre_modifier, name='registre_modifier'),
    path('inspection/visites/', inspection.visites_liste, name='visites_liste'),
    path('inspection/visites/ajouter/', inspection.visite_ajouter, name='visite_ajouter'),
    path('inspection/visites/<int:pk>/', inspection.visite_detail, name='visite_detail'),
    path('inspection/checklist/', inspection.checklist_conformite, name='checklist_conformite'),
    path('inspection/rapport/', inspection.generer_rapport_conformite, name='generer_rapport'),
]
