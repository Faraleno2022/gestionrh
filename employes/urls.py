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
]
