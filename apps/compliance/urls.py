# apps/compliance/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL pattern for the list of compliance checks
    path('', views.compliance_check_list_view, name='compliance_check_list'),

    # URL pattern for initiating a new compliance check
    path('initiate/', views.compliance_check_initiate_view, name='compliance_check_initiate'),

    # URL pattern for viewing details of a specific compliance check
    path('<int:pk>/', views.compliance_check_detail_view, name='compliance_check_detail'),

    # URL pattern for answering questions for a specific compliance check
    path('<int:pk>/answer/', views.compliance_check_answer_questions_view, name='compliance_check_answer_questions'),

    # URL pattern to trigger Credas check for a compliance check
    path('<int:pk>/trigger-credas/', views.compliance_check_trigger_credas_view, name='compliance_check_trigger_credas'),

    # URL pattern to trigger PEPs and sanctions check for a compliance check
    path('<int:pk>/trigger-peps-sanctions/', views.compliance_check_trigger_peps_sanctions_view, name='compliance_check_trigger_peps_sanctions'),

    # Add URL patterns for other compliance-related views here
    path('<int:pk>/evaluate/', views.compliance_check_evaluate_view, name='compliance_check_evaluate'),
    path('<int:pk>/report/', views.compliance_check_report_view, name='compliance_check_report'),

    # URL patterns for webhooks (if implementing)
    path('webhooks/credas/', views.credas_webhook_view, name='credas_webhook'),
    path('webhooks/peps-sanctions/', views.peps_sanctions_webhook_view, name='peps_sanctions_webhook'),
]
