from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import LogActivite


def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(request, action, module=None, table=None, id_enreg=None, details=None):
    """Enregistre une activité dans les logs"""
    if request.user.is_authenticated:
        LogActivite.objects.create(
            utilisateur=request.user,
            action=action,
            module=module,
            table_concernee=table,
            id_enregistrement=id_enreg,
            details=details,
            adresse_ip=get_client_ip(request)
        )


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.actif:
                login(request, user)
                user.enregistrer_connexion()
                log_activity(request, 'Connexion', 'core')
                messages.success(request, f'Bienvenue {user.get_full_name()}!')
                return redirect('dashboard:index')
            else:
                messages.error(request, 'Votre compte est désactivé.')
        else:
            messages.error(request, 'Identifiants incorrects.')
    
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    log_activity(request, 'Déconnexion', 'core')
    logout(request)
    messages.info(request, 'Vous avez été déconnecté.')
    return redirect('core:login')


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Mise à jour du profil
            user = request.user
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', user.email)
            user.telephone = request.POST.get('telephone', '')
            
            # Gestion de la photo
            if 'photo' in request.FILES:
                user.photo = request.FILES['photo']
            
            user.save()
            
            log_activity(request, 'Modification profil', 'core')
            messages.success(request, 'Profil mis à jour avec succès')
            
        elif action == 'change_password':
            # Changement de mot de passe
            from django.contrib.auth import update_session_auth_hash
            
            old_password = request.POST.get('old_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if not request.user.check_password(old_password):
                messages.error(request, 'Mot de passe actuel incorrect')
            elif new_password1 != new_password2:
                messages.error(request, 'Les nouveaux mots de passe ne correspondent pas')
            elif len(new_password1) < 8:
                messages.error(request, 'Le mot de passe doit contenir au moins 8 caractères')
            else:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                
                log_activity(request, 'Changement mot de passe', 'core')
                messages.success(request, 'Mot de passe changé avec succès')
        
        return redirect('core:profile')
    
    return render(request, 'core/profile.html')


def index_view(request):
    """Page d'accueil - redirige vers le dashboard si connecté"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return redirect('core:login')


def csrf_failure(request, reason=""):
    """Vue personnalisée pour les erreurs CSRF"""
    return render(request, 'core/csrf_failure.html', {
        'reason': reason
    }, status=403)
