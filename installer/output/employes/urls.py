from django.urls import path
from . import views

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
]
