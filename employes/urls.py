from django.urls import path
from . import views
from . import views_evaluation

app_name = 'employes'

urlpatterns = [
    # Liste et CRUD employés
    path('', views.EmployeListView.as_view(), name='list'),
    path('create/', views.EmployeCreateView.as_view(), name='create'),
    path('<int:pk>/', views.EmployeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.EmployeUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.EmployeDeleteView.as_view(), name='delete'),
    
    # Export
    path('export/excel/', views.employe_export_excel, name='export_excel'),
    
    # Contrats
    path('<int:employe_id>/contrat/create/', views.employe_contrat_create, name='contrat_create'),
    
    # Documents
    path('<int:employe_id>/document/upload/', views.employe_document_upload, name='document_upload'),
    path('document/<int:document_id>/delete/', views.employe_document_delete, name='document_delete'),

    # Évaluations (performance)
    path('<int:employe_id>/evaluations/', views.evaluation_list, name='evaluation_list'),
    path('<int:employe_id>/evaluations/create/', views.evaluation_create, name='evaluation_create'),
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluations/<int:pk>/delete/', views.evaluation_delete, name='evaluation_delete'),

    # Sanctions disciplinaires
    path('<int:employe_id>/sanctions/', views.sanction_list, name='sanction_list'),
    path('<int:employe_id>/sanctions/create/', views.sanction_create, name='sanction_create'),
    path('sanctions/<int:pk>/', views.sanction_detail, name='sanction_detail'),
    path('sanctions/<int:pk>/delete/', views.sanction_delete, name='sanction_delete'),
    
    # Campagnes d'évaluation de performance
    path('campagnes/', views_evaluation.liste_campagnes, name='liste_campagnes'),
    path('campagnes/creer/', views_evaluation.creer_campagne, name='creer_campagne'),
    path('campagnes/<int:pk>/', views_evaluation.detail_campagne, name='detail_campagne'),
    path('campagnes/<int:pk>/lancer/', views_evaluation.lancer_campagne, name='lancer_campagne'),
    path('campagnes/synthese/', views_evaluation.synthese_evaluations, name='synthese_evaluations'),
    
    # Évaluations de performance (nouveau système)
    path('performance/<int:pk>/', views_evaluation.detail_evaluation, name='detail_evaluation_perf'),
    path('performance/<int:pk>/modifier/', views_evaluation.modifier_evaluation, name='modifier_evaluation'),
    path('performance/<int:evaluation_id>/objectif/', views_evaluation.ajouter_objectif, name='ajouter_objectif'),
    path('performance/objectif/<int:pk>/evaluer/', views_evaluation.evaluer_objectif, name='evaluer_objectif'),
    path('performance/<int:evaluation_id>/competence/', views_evaluation.ajouter_competence, name='ajouter_competence'),
]
