from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from .models import LogActivite, Utilisateur


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


def register_entreprise(request):
    """Vue d'inscription d'une nouvelle entreprise"""
    from .forms import EntrepriseRegistrationForm
    
    if request.method == 'POST':
        form = EntrepriseRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            entreprise = form.save()
            
            # Connecter automatiquement l'administrateur
            admin_user = entreprise.utilisateurs.filter(est_admin_entreprise=True).first()
            if admin_user:
                login(request, admin_user)
                messages.success(
                    request,
                    f'Entreprise {entreprise.nom_entreprise} créée avec succès! Bienvenue {admin_user.get_full_name()}!'
                )
                return redirect('dashboard:index')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = EntrepriseRegistrationForm()
    
    return render(request, 'core/register_entreprise.html', {'form': form})


@login_required
def reauth_view(request):
    """Vue de réauthentification"""
    from .forms import ReauthForm
    
    if request.method == 'POST':
        form = ReauthForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            
            # Vérifier le mot de passe
            if request.user.check_password(password):
                # Mettre à jour la dernière réauthentification
                request.user.last_reauth = timezone.now()
                request.user.save(update_fields=['last_reauth'])
                
                log_activity(request, 'Réauthentification réussie', 'core')
                messages.success(request, 'Réauthentification réussie!')
                
                # Rediriger vers la page demandée
                next_url = request.session.get('reauth_next', 'dashboard:index')
                if 'reauth_next' in request.session:
                    del request.session['reauth_next']
                return redirect(next_url)
            else:
                messages.error(request, 'Mot de passe incorrect.')
    else:
        form = ReauthForm()
    
    return render(request, 'core/reauth.html', {'form': form})


@login_required
def manage_users(request):
    """Vue de gestion des utilisateurs de l'entreprise"""
    from .forms import UserInvitationForm
    from .decorators import entreprise_active_required
    
    # Vérifier que l'utilisateur est admin de son entreprise
    if not request.user.est_admin_entreprise:
        messages.error(request, "Vous n'avez pas les permissions pour gérer les utilisateurs.")
        return redirect('dashboard:index')
    
    # Vérifier le quota d'utilisateurs
    entreprise = request.user.entreprise
    current_users = entreprise.utilisateurs.filter(actif=True).count()
    quota_reached = current_users >= entreprise.max_utilisateurs
    
    if request.method == 'POST':
        if quota_reached:
            messages.error(
                request,
                f"Quota d'utilisateurs atteint ({entreprise.max_utilisateurs}). "
                f"Veuillez upgrader votre plan."
            )
            return redirect('core:manage_users')
        
        form = UserInvitationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.entreprise = request.user.entreprise
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            log_activity(request, f'Création utilisateur {user.username}', 'core')
            messages.success(request, f'Utilisateur {user.username} créé avec succès!')
            return redirect('core:manage_users')
    else:
        form = UserInvitationForm()
    
    # Liste des utilisateurs de l'entreprise
    users = request.user.entreprise.utilisateurs.all().order_by('-date_joined')
    
    return render(request, 'core/manage_users.html', {
        'form': form,
        'users': users,
        'quota_reached': quota_reached,
        'current_users': current_users,
        'max_users': entreprise.max_utilisateurs,
    })


@login_required
def send_invitation(request):
    """Envoyer une invitation par email à un nouvel utilisateur"""
    from django.core.mail import send_mail
    from django.contrib.sites.shortcuts import get_current_site
    from django.utils.crypto import get_random_string
    
    if not request.user.est_admin_entreprise:
        messages.error(request, "Vous n'avez pas les permissions pour inviter des utilisateurs.")
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        profil_id = request.POST.get('profil')
        
        # Vérifier le quota
        entreprise = request.user.entreprise
        current_users = entreprise.utilisateurs.filter(actif=True).count()
        if current_users >= entreprise.max_utilisateurs:
            messages.error(request, "Quota d'utilisateurs atteint.")
            return redirect('core:manage_users')
        
        # Générer un token d'invitation
        token = get_random_string(32)
        
        # Créer l'utilisateur inactif
        from .models import ProfilUtilisateur
        profil = get_object_or_404(ProfilUtilisateur, pk=profil_id)
        
        username = email.split('@')[0]
        # S'assurer que le username est unique
        base_username = username
        counter = 1
        while Utilisateur.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = Utilisateur.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            entreprise=entreprise,
            profil=profil,
            actif=False,  # Inactif jusqu'à activation
            is_active=False
        )
        user.set_password(token)  # Mot de passe temporaire
        user.save()
        
        # Envoyer l'email d'invitation
        current_site = get_current_site(request)
        activation_link = f"http://{current_site.domain}/activate/{token}/"
        
        subject = f"Invitation à rejoindre {entreprise.nom_entreprise}"
        message = f"""
Bonjour {first_name} {last_name},

Vous avez été invité(e) à rejoindre {entreprise.nom_entreprise} sur Gestionnaire RH Guinée.

Pour activer votre compte, cliquez sur le lien ci-dessous:
{activation_link}

Votre nom d'utilisateur: {username}

Cordialement,
L'équipe {entreprise.nom_entreprise}
        """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@gestionrh.gn',
                [email],
                fail_silently=False,
            )
            
            log_activity(request, f'Invitation envoyée à {email}', 'core')
            messages.success(request, f'Invitation envoyée à {email}!')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'envoi de l\'email: {str(e)}')
            user.delete()  # Supprimer l'utilisateur si l'email échoue
        
        return redirect('core:manage_users')
    
    # GET: Afficher le formulaire
    from .models import ProfilUtilisateur
    profils = ProfilUtilisateur.objects.filter(actif=True)
    
    return render(request, 'core/send_invitation.html', {
        'profils': profils
    })


@login_required
def admin_dashboard(request):
    """Tableau de bord pour les administrateurs d'entreprise"""
    if not request.user.est_admin_entreprise:
        messages.error(request, "Accès réservé aux administrateurs d'entreprise.")
        return redirect('dashboard:index')
    
    entreprise = request.user.entreprise
    
    # Statistiques de l'entreprise
    from employes.models import Employe
    from paie.models import BulletinPaie, PeriodePaie
    from temps_travail.models import Conge
    
    stats = {
        'entreprise': entreprise,
        'total_users': entreprise.utilisateurs.count(),
        'active_users': entreprise.utilisateurs.filter(actif=True).count(),
        'quota_users': entreprise.max_utilisateurs,
        'total_employes': Employe.objects.count(),
        'employes_actifs': Employe.objects.filter(statut_employe='actif').count(),
        'bulletins_mois': 0,
        'conges_en_attente': Conge.objects.filter(statut_demande='En attente').count(),
    }
    
    # Bulletins du mois en cours
    periode_actuelle = PeriodePaie.objects.filter(statut_periode='ouverte').first()
    if periode_actuelle:
        stats['bulletins_mois'] = BulletinPaie.objects.filter(periode=periode_actuelle).count()
    
    # Activités récentes
    recent_logs = LogActivite.objects.filter(
        utilisateur__entreprise=entreprise
    ).select_related('utilisateur').order_by('-date_action')[:20]
    
    # Utilisateurs récents
    recent_users = entreprise.utilisateurs.all().order_by('-date_joined')[:5]
    
    return render(request, 'core/admin_dashboard.html', {
        'stats': stats,
        'recent_logs': recent_logs,
        'recent_users': recent_users,
    })


@login_required
def entreprise_settings(request):
    """Paramètres de l'entreprise (logo, informations, etc.)"""
    if not request.user.est_admin_entreprise:
        messages.error(request, "Accès réservé aux administrateurs d'entreprise.")
        return redirect('dashboard:index')
    
    entreprise = request.user.entreprise
    from .forms import EntrepriseSettingsForm
    
    if request.method == 'POST':
        form = EntrepriseSettingsForm(request.POST, request.FILES, instance=entreprise)
        if form.is_valid():
            form.save()
            log_activity(request, 'Modification paramètres entreprise', 'core')
            messages.success(request, 'Paramètres de l\'entreprise mis à jour avec succès!')
            return redirect('core:entreprise_settings')
    else:
        form = EntrepriseSettingsForm(instance=entreprise)
    
    return render(request, 'core/entreprise_settings.html', {
        'form': form,
        'entreprise': entreprise,
    })
