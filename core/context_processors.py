from django.conf import settings
from .models import Societe


def company_info(request):
    """Ajoute les informations de la société au contexte"""
    try:
        societe = Societe.objects.filter(actif=True).first()
    except:
        societe = None
    
    return {
        'COMPANY_NAME': settings.COMPANY_NAME,
        'societe': societe,
    }
