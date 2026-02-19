"""
Middleware de vérification de licence
Bloque l'accès si la licence n'est pas valide
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone


class LicenceMiddleware:
    """
    Middleware qui vérifie la validité de la licence à chaque requête
    """
    
    # URLs exemptées de la vérification de licence
    EXEMPT_URLS = [
        '/licence/',
        '/licence/activer/',
        '/licence/statut/',
        '/licence/expiree/',
        '/static/',
        '/media/',
        '/admin/',
        '/login/',
        '/api/',
        '/documentation-legale/',
        '/register-entreprise/',
        '/partenariat/',
    ]
    
    # URLs qui doivent correspondre exactement (pas startswith)
    EXEMPT_EXACT_URLS = [
        '/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier si l'URL est exemptée
        path = request.path
        
        # Vérification exacte (ex: '/')
        if path in self.EXEMPT_EXACT_URLS:
            return self.get_response(request)
        
        # Vérification par préfixe
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                return self.get_response(request)
        
        # Vérifier la licence
        from .models_licence import get_licence_active, LicenceLocale
        
        licence = get_licence_active()
        
        if not licence:
            # Pas de licence - rediriger vers activation
            if not path.startswith('/licence/'):
                return redirect('core:licence_activation')
        else:
            # Vérifier si la licence expire bientôt (7 jours)
            if licence.jours_restants <= 7 and licence.jours_restants > 0:
                if not request.session.get('licence_warning_shown'):
                    messages.warning(
                        request, 
                        f"⚠️ Votre licence expire dans {licence.jours_restants} jour(s). "
                        f"Contactez votre fournisseur pour renouveler."
                    )
                    request.session['licence_warning_shown'] = True
            
            # Licence expirée
            if licence.jours_restants <= 0 and licence.date_expiration:
                messages.error(request, "❌ Votre licence a expiré. Veuillez la renouveler.")
                return redirect('core:licence_expiree')
        
        # Ajouter la licence au request pour accès dans les vues
        request.licence = licence
        
        return self.get_response(request)
