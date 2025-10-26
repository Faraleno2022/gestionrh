from django.conf import settings
from .models import Societe, Entreprise


def company_info(request):
    """Ajoute les informations de la société au contexte"""
    try:
        societe = Societe.objects.filter(actif=True).first()
    except:
        societe = None
    
    # Ajouter le logo de l'entreprise de l'utilisateur connecté
    entreprise_logo = None
    entreprise_nom = None
    
    if request.user.is_authenticated and hasattr(request.user, 'entreprise'):
        if request.user.entreprise:
            entreprise_logo = request.user.entreprise.logo
            entreprise_nom = request.user.entreprise.nom_entreprise
    
    return {
        'COMPANY_NAME': settings.COMPANY_NAME,
        'societe': societe,
        'entreprise_logo': entreprise_logo,
        'entreprise_nom': entreprise_nom,
    }
