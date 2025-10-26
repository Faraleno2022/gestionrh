from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Entreprise, Utilisateur, ProfilUtilisateur, DroitAcces, LogActivite,
    Societe, Etablissement, Service, Poste
)


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ['nom_entreprise', 'slug', 'email', 'ville', 'plan_abonnement', 'actif', 'date_creation']
    list_filter = ['actif', 'plan_abonnement', 'ville']
    search_fields = ['nom_entreprise', 'slug', 'email', 'nif']
    readonly_fields = ['date_creation']
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom_entreprise', 'slug', 'logo')
        }),
        ('Immatriculation', {
            'fields': ('nif', 'num_cnss')
        }),
        ('Coordonnées', {
            'fields': ('adresse', 'ville', 'pays', 'telephone', 'email')
        }),
        ('Abonnement', {
            'fields': ('plan_abonnement', 'max_utilisateurs', 'date_expiration')
        }),
        ('Statut', {
            'fields': ('actif', 'date_creation')
        }),
    )


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ['nom_profil', 'niveau_acces', 'actif']
    list_filter = ['niveau_acces', 'actif']
    search_fields = ['nom_profil']


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'entreprise', 'profil', 'est_admin_entreprise', 'actif', 'date_derniere_connexion']
    list_filter = ['actif', 'profil', 'entreprise', 'est_admin_entreprise', 'require_reauth', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = UserAdmin.fieldsets + (
        ('Entreprise', {
            'fields': ('entreprise', 'est_admin_entreprise')
        }),
        ('Informations supplémentaires', {
            'fields': ('telephone', 'profil', 'actif', 'photo', 'date_derniere_connexion', 'tentatives_connexion')
        }),
        ('Sécurité', {
            'fields': ('require_reauth', 'last_reauth')
        }),
    )


@admin.register(DroitAcces)
class DroitAccesAdmin(admin.ModelAdmin):
    list_display = ['profil', 'module', 'lecture', 'ecriture', 'modification', 'suppression', 'validation']
    list_filter = ['profil', 'module']
    search_fields = ['profil__nom_profil']


@admin.register(LogActivite)
class LogActiviteAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'action', 'module', 'date_action', 'adresse_ip']
    list_filter = ['module', 'date_action']
    search_fields = ['utilisateur__username', 'action', 'details']
    readonly_fields = ['utilisateur', 'action', 'module', 'table_concernee', 'id_enregistrement', 'details', 'adresse_ip', 'date_action']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Societe)
class SocieteAdmin(admin.ModelAdmin):
    list_display = ['raison_sociale', 'nif', 'num_cnss_employeur', 'ville', 'actif']
    list_filter = ['actif', 'ville']
    search_fields = ['raison_sociale', 'nif']
    fieldsets = (
        ('Informations générales', {
            'fields': ('raison_sociale', 'forme_juridique', 'secteur_activite', 'code_ape', 'logo')
        }),
        ('Immatriculation', {
            'fields': ('nif', 'num_cnss_employeur', 'num_inam')
        }),
        ('Coordonnées', {
            'fields': ('adresse', 'commune', 'prefecture', 'ville', 'pays', 'telephone', 'email', 'site_web')
        }),
        ('Informations financières', {
            'fields': ('date_creation', 'capital_social')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ['code_etablissement', 'nom_etablissement', 'type_etablissement', 'ville', 'actif']
    list_filter = ['type_etablissement', 'actif', 'ville']
    search_fields = ['code_etablissement', 'nom_etablissement']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['code_service', 'nom_service', 'etablissement', 'responsable_service', 'actif']
    list_filter = ['actif', 'etablissement']
    search_fields = ['code_service', 'nom_service']
    raw_id_fields = ['responsable_service']


@admin.register(Poste)
class PosteAdmin(admin.ModelAdmin):
    list_display = ['code_poste', 'intitule_poste', 'service', 'categorie_professionnelle', 'actif']
    list_filter = ['categorie_professionnelle', 'actif']
    search_fields = ['code_poste', 'intitule_poste']
    fieldsets = (
        ('Informations de base', {
            'fields': ('code_poste', 'intitule_poste', 'service', 'categorie_professionnelle', 'classification')
        }),
        ('Prérequis', {
            'fields': ('niveau_requis', 'experience_requise')
        }),
        ('Description', {
            'fields': ('description_poste', 'responsabilites', 'competences_requises')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
