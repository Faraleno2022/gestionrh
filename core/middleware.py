"""
Middleware de sécurité personnalisé pour l'application
"""
import logging
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.conf import settings
import re

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Ajoute des en-têtes de sécurité supplémentaires
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Protection contre le clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Protection XSS
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Référer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class SQLInjectionProtectionMiddleware:
    """
    Protection contre les injections SQL
    """
    # Patterns suspects d'injection SQL
    SQL_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(--)",
        r"(;.*--)",
        r"(\bor\b.*=.*)",
        r"(\band\b.*=.*)",
        r"('.*or.*'.*=.*')",
        r"(exec\s*\()",
        r"(execute\s*\()",
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_PATTERNS]

    def __call__(self, request):
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if self._contains_sql_injection(value):
                logger.warning(f"Tentative d'injection SQL détectée dans GET: {key}={value} depuis {request.META.get('REMOTE_ADDR')}")
                return HttpResponseForbidden("Requête invalide détectée")
        
        # Vérifier les paramètres POST
        if request.method == 'POST':
            for key, value in request.POST.items():
                if isinstance(value, str) and self._contains_sql_injection(value):
                    logger.warning(f"Tentative d'injection SQL détectée dans POST: {key} depuis {request.META.get('REMOTE_ADDR')}")
                    return HttpResponseForbidden("Requête invalide détectée")
        
        return self.get_response(request)
    
    def _contains_sql_injection(self, value):
        """Vérifie si la valeur contient des patterns d'injection SQL"""
        if not isinstance(value, str):
            return False
        
        for pattern in self.patterns:
            if pattern.search(value):
                return True
        return False


class XSSProtectionMiddleware:
    """
    Protection contre les attaques XSS
    """
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
        r"<iframe",
        r"<embed",
        r"<object",
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_PATTERNS]

    def __call__(self, request):
        # Vérifier les paramètres GET
        for key, value in request.GET.items():
            if self._contains_xss(value):
                logger.warning(f"Tentative XSS détectée dans GET: {key}={value} depuis {request.META.get('REMOTE_ADDR')}")
                return HttpResponseForbidden("Requête invalide détectée")
        
        # Vérifier les paramètres POST
        if request.method == 'POST':
            for key, value in request.POST.items():
                if isinstance(value, str) and self._contains_xss(value):
                    logger.warning(f"Tentative XSS détectée dans POST: {key} depuis {request.META.get('REMOTE_ADDR')}")
                    return HttpResponseForbidden("Requête invalide détectée")
        
        return self.get_response(request)
    
    def _contains_xss(self, value):
        """Vérifie si la valeur contient des patterns XSS"""
        if not isinstance(value, str):
            return False
        
        for pattern in self.patterns:
            if pattern.search(value):
                return True
        return False


class IPWhitelistMiddleware:
    """
    Middleware pour restreindre l'accès à certaines IPs (optionnel)
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.whitelist = getattr(settings, 'IP_WHITELIST', [])
        self.enabled = getattr(settings, 'IP_WHITELIST_ENABLED', False)

    def __call__(self, request):
        if self.enabled and self.whitelist:
            client_ip = self._get_client_ip(request)
            if client_ip not in self.whitelist:
                logger.warning(f"Accès refusé pour IP non autorisée: {client_ip}")
                return HttpResponseForbidden("Accès non autorisé")
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Récupère l'IP réelle du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestLoggingMiddleware:
    """
    Log toutes les requêtes pour audit de sécurité
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log avant traitement
        if getattr(settings, 'SECURITY_LOGGING_ENABLED', True):
            logger.info(
                f"Request: {request.method} {request.path} "
                f"from {request.META.get('REMOTE_ADDR')} "
                f"User: {request.user if request.user.is_authenticated else 'Anonymous'}"
            )
        
        response = self.get_response(request)
        
        # Log après traitement si erreur
        if response.status_code >= 400:
            logger.warning(
                f"Response {response.status_code}: {request.method} {request.path} "
                f"from {request.META.get('REMOTE_ADDR')}"
            )
        
        return response


class EntrepriseQuotaMiddleware:
    """
    Middleware pour vérifier les quotas d'abonnement de l'entreprise
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier uniquement pour les utilisateurs authentifiés
        if request.user.is_authenticated and hasattr(request.user, 'entreprise'):
            entreprise = request.user.entreprise
            
            if entreprise:
                # Vérifier si l'entreprise est active
                if not entreprise.actif:
                    from django.shortcuts import redirect
                    from django.contrib import messages
                    messages.error(request, "Votre entreprise est désactivée. Contactez le support.")
                    return redirect('core:login')
                
                # Vérifier la date d'expiration
                if entreprise.date_expiration:
                    from django.utils import timezone
                    if timezone.now().date() > entreprise.date_expiration:
                        from django.shortcuts import redirect
                        from django.contrib import messages
                        messages.warning(request, "Votre abonnement a expiré. Veuillez le renouveler.")
                        # Permettre l'accès uniquement aux pages de renouvellement
                        if not (request.path.startswith('/payments/') or request.path.startswith('/renouvellement/')):
                            return redirect('payments:plans')
                
                # Vérifier le quota d'utilisateurs (seulement pour les admins qui créent des users)
                if request.path == '/manage-users/' and request.method == 'POST':
                    current_users = entreprise.utilisateurs.filter(actif=True).count()
                    if current_users >= entreprise.max_utilisateurs:
                        from django.contrib import messages
                        messages.error(
                            request,
                            f"Quota d'utilisateurs atteint ({entreprise.max_utilisateurs}). "
                            f"Veuillez upgrader votre plan."
                        )
                        from django.shortcuts import redirect
                        return redirect('core:manage_users')
        
        response = self.get_response(request)
        return response
