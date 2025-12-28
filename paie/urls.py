from django.urls import path
from . import views
from .views_irpp import bareme_irpp
from . import views_envoi
from . import views_export
from . import views_pret
from . import views_frais

app_name = 'paie'

urlpatterns = [
    # Accueil
    path('', views.paie_home, name='home'),
    
    # Périodes de paie
    path('periodes/', views.liste_periodes, name='liste_periodes'),
    path('periodes/creer/', views.creer_periode, name='creer_periode'),
    path('periodes/<int:pk>/', views.detail_periode, name='detail_periode'),
    path('periodes/<int:pk>/calculer/', views.calculer_periode, name='calculer_periode'),
    path('periodes/<int:pk>/valider/', views.valider_periode, name='valider_periode'),
    path('periodes/<int:pk>/cloturer/', views.cloturer_periode, name='cloturer_periode'),
    
    # Bulletins de paie
    path('bulletins/', views.liste_bulletins, name='liste_bulletins'),
    path('bulletins/<int:pk>/', views.detail_bulletin, name='detail_bulletin'),
    path('bulletins/<int:pk>/imprimer/', views.imprimer_bulletin, name='imprimer_bulletin'),
    path('bulletins/<int:pk>/telecharger-pdf/', views.telecharger_bulletin_pdf, name='telecharger_bulletin_pdf'),
    path('bulletins/public/<str:token>/', views.telecharger_bulletin_public, name='telecharger_bulletin_public'),
    
    # Envoi des bulletins
    path('bulletins/<int:pk>/envoyer-email/', views_envoi.envoyer_bulletin_email, name='envoyer_email'),
    path('bulletins/<int:pk>/envoyer-whatsapp/', views_envoi.envoyer_bulletin_whatsapp, name='envoyer_whatsapp'),
    path('bulletins/envoyer-masse/', views_envoi.envoyer_bulletins_masse, name='envoyer_masse'),
    path('bulletins/envoyer-masse/email/', views_envoi.envoyer_masse_email, name='envoyer_masse_email'),
    path('bulletins/envoyer-masse/whatsapp/', views_envoi.generer_liens_whatsapp_masse, name='generer_liens_whatsapp'),
    
    # Livre de paie
    path('livre/', views.livre_paie, name='livre_paie'),
    path('livre/telecharger-pdf/', views.telecharger_livre_paie_pdf, name='telecharger_livre_paie_pdf'),
    
    # Déclarations sociales
    path('declarations/', views.declarations_sociales, name='declarations_sociales'),
    
    # Éléments de salaire
    path('elements-salaire/', views.liste_elements_salaire, name='liste_elements_salaire'),
    path('elements-salaire/employe/<int:employe_id>/', views.elements_salaire_employe, name='elements_salaire_employe'),
    path('elements-salaire/ajouter/<int:employe_id>/', views.ajouter_element_salaire, name='ajouter_element_salaire'),
    path('elements-salaire/<int:pk>/modifier/', views.modifier_element_salaire, name='modifier_element_salaire'),
    path('elements-salaire/<int:pk>/supprimer/', views.supprimer_element_salaire, name='supprimer_element_salaire'),
    
    # Rubriques de paie
    path('rubriques/', views.liste_rubriques, name='liste_rubriques'),
    path('rubriques/creer/', views.creer_rubrique, name='creer_rubrique'),
    path('rubriques/<int:pk>/', views.detail_rubrique, name='detail_rubrique'),
    
    # Barème IRPP
    path('bareme-irpp/', bareme_irpp.bareme_irpp_liste, name='bareme_irpp_liste'),
    path('bareme-irpp/ajouter/', bareme_irpp.bareme_irpp_ajouter, name='bareme_irpp_ajouter'),
    path('bareme-irpp/<int:pk>/modifier/', bareme_irpp.bareme_irpp_modifier, name='bareme_irpp_modifier'),
    path('bareme-irpp/<int:pk>/supprimer/', bareme_irpp.bareme_irpp_supprimer, name='bareme_irpp_supprimer'),
    path('bareme-irpp/dupliquer/', bareme_irpp.bareme_irpp_dupliquer, name='bareme_irpp_dupliquer'),
    path('simulateur-irpp/', bareme_irpp.simulateur_irpp, name='simulateur_irpp'),
    path('api/calculer-irpp/', bareme_irpp.api_calculer_irpp, name='api_calculer_irpp'),
    
    # Alertes échéances
    path('echeances/', views.tableau_bord_echeances, name='tableau_bord_echeances'),
    path('echeances/<int:pk>/traiter/', views.marquer_alerte_traitee, name='marquer_alerte_traitee'),
    path('api/alertes-echeances/', views.api_alertes_echeances, name='api_alertes_echeances'),
    
    # Export CNSS
    path('export/cnss/excel/', views_export.export_cnss_excel, name='export_cnss_excel'),
    path('export/cnss/pdf/', views_export.export_cnss_pdf, name='export_cnss_pdf'),
    
    # Export DMU (Déclaration Mensuelle Unique)
    path('export/dmu/excel/', views_export.export_dmu_excel, name='export_dmu_excel'),
    path('export/dmu/pdf/', views_export.export_dmu_pdf, name='export_dmu_pdf'),
    
    # Historique des bulletins
    path('historique/', views.historique_bulletins, name='historique_bulletins'),
    path('historique/telecharger-masse/', views.telecharger_bulletins_masse, name='telecharger_bulletins_masse'),
    path('attestation/<int:employe_id>/', views.attestation_salaire, name='attestation_salaire'),
    
    # Simulation de paie
    path('simulation/', views.simulation_paie, name='simulation_paie'),
    
    # Gestion des prêts
    path('prets/', views_pret.liste_prets, name='liste_prets'),
    path('prets/creer/', views_pret.creer_pret, name='creer_pret'),
    path('prets/<int:pk>/', views_pret.detail_pret, name='detail_pret'),
    path('prets/<int:pk>/approuver/', views_pret.approuver_pret, name='approuver_pret'),
    path('prets/<int:pk>/rejeter/', views_pret.rejeter_pret, name='rejeter_pret'),
    path('prets/<int:pk>/rembourser/', views_pret.enregistrer_remboursement, name='enregistrer_remboursement'),
    path('prets/a-prelever/', views_pret.prets_a_prelever, name='prets_a_prelever'),
    
    # Notes de frais
    path('frais/', views_frais.liste_notes_frais, name='liste_notes_frais'),
    path('frais/creer/', views_frais.creer_note_frais, name='creer_note_frais'),
    path('frais/<int:pk>/', views_frais.detail_note_frais, name='detail_note_frais'),
    path('frais/<int:pk>/ajouter-ligne/', views_frais.ajouter_ligne_frais, name='ajouter_ligne_frais'),
    path('frais/<int:pk>/supprimer-ligne/<int:ligne_pk>/', views_frais.supprimer_ligne_frais, name='supprimer_ligne_frais'),
    path('frais/<int:pk>/soumettre/', views_frais.soumettre_note_frais, name='soumettre_note_frais'),
    path('frais/<int:pk>/valider/', views_frais.valider_note_frais, name='valider_note_frais'),
    path('frais/<int:pk>/rembourser/', views_frais.rembourser_note_frais, name='rembourser_note_frais'),
    path('frais/<int:pk>/supprimer/', views_frais.supprimer_note_frais, name='supprimer_note_frais'),
    path('frais/recap/', views_frais.recap_frais, name='recap_frais'),
    path('frais/categories/', views_frais.gestion_categories_frais, name='gestion_categories_frais'),
]
