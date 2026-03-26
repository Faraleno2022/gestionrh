"""
Vues pour les paramètres de calcul de paie personnalisés.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.decorators import reauth_required, entreprise_active_required
from .models import ParametresCalculPaie, HistoriqueParametresPaie
from .formules import tester_formule, valider_formule, EXEMPLES_FORMULES


def _utilisateur_peut_modifier(user):
    """Retourne True si l'utilisateur peut modifier les paramètres de calcul."""
    if user.is_superuser:
        return True
    if getattr(user, 'est_admin_entreprise', False):
        return True
    # Profil niveau 5 (Administrateur)
    profil = getattr(user, 'profil', None)
    if profil and getattr(profil, 'niveau_acces', 0) >= 5:
        return True
    return False


def _enregistrer_historique(params, user, champ, ancienne, nouvelle, raison=''):
    """Crée une entrée d'historique si la valeur a changé."""
    if str(ancienne) != str(nouvelle):
        HistoriqueParametresPaie.objects.create(
            parametres=params,
            modifie_par=user,
            champ_modifie=champ,
            ancienne_valeur=str(ancienne),
            nouvelle_valeur=str(nouvelle),
            raison=raison,
        )


@login_required
@entreprise_active_required
@reauth_required
def parametres_calcul_paie(request):
    """
    Affiche et enregistre les paramètres du moteur de calcul de paie
    pour l'entreprise de l'utilisateur connecté.
    """
    entreprise = request.user.entreprise
    params, _ = ParametresCalculPaie.objects.get_or_create(entreprise=entreprise)

    peut_modifier = _utilisateur_peut_modifier(request.user)

    if request.method == 'POST':
        if not peut_modifier:
            messages.error(request, "Vous n'avez pas les droits pour modifier ces paramètres.")
            return redirect('paie:parametres_calcul')

        raison = request.POST.get('raison', '').strip()

        # --- Indemnités forfaitaires ---
        nouveau_mode_exo = request.POST.get('mode_exoneration_indemnites', 'plafond_pct')
        _enregistrer_historique(
            params, request.user,
            'mode_exoneration_indemnites',
            params.mode_exoneration_indemnites,
            nouveau_mode_exo, raison,
        )
        params.mode_exoneration_indemnites = nouveau_mode_exo

        pct_raw = request.POST.get('plafond_exoneration_pct', '25')
        try:
            from decimal import Decimal
            nouveau_pct = Decimal(pct_raw)
        except Exception:
            nouveau_pct = Decimal('25')
        _enregistrer_historique(
            params, request.user,
            'plafond_exoneration_pct',
            params.plafond_exoneration_pct,
            nouveau_pct, raison,
        )
        params.plafond_exoneration_pct = nouveau_pct

        nouvelle_formule_exo = request.POST.get('formule_exoneration', '').strip()
        _enregistrer_historique(
            params, request.user,
            'formule_exoneration',
            params.formule_exoneration,
            nouvelle_formule_exo, raison,
        )
        params.formule_exoneration = nouvelle_formule_exo

        # --- Base VF/TA ---
        nouveau_mode_vf = request.POST.get('mode_base_vf', 'brut')
        _enregistrer_historique(
            params, request.user,
            'mode_base_vf',
            params.mode_base_vf,
            nouveau_mode_vf, raison,
        )
        params.mode_base_vf = nouveau_mode_vf

        nouvelle_formule_vf = request.POST.get('formule_base_vf', '').strip()
        _enregistrer_historique(
            params, request.user,
            'formule_base_vf',
            params.formule_base_vf,
            nouvelle_formule_vf, raison,
        )
        params.formule_base_vf = nouvelle_formule_vf

        # --- Base RTS ---
        nouveau_utiliser_rts = request.POST.get('utiliser_formule_base_rts') == 'on'
        _enregistrer_historique(
            params, request.user,
            'utiliser_formule_base_rts',
            params.utiliser_formule_base_rts,
            nouveau_utiliser_rts, raison,
        )
        params.utiliser_formule_base_rts = nouveau_utiliser_rts

        nouvelle_formule_rts = request.POST.get('formule_base_rts', '').strip()
        _enregistrer_historique(
            params, request.user,
            'formule_base_rts',
            params.formule_base_rts,
            nouvelle_formule_rts, raison,
        )
        params.formule_base_rts = nouvelle_formule_rts

        params.save()
        messages.success(request, "Paramètres de calcul enregistrés avec succès.")
        return redirect('paie:parametres_calcul')

    contexte = {
        'params': params,
        'peut_modifier': peut_modifier,
        'modes_exoneration': ParametresCalculPaie.MODE_EXONERATION,
        'modes_base_vf': ParametresCalculPaie.MODE_BASE_VF,
        'variables_disponibles': [
            ('brut', 'Salaire brut total'),
            ('cnss', 'Cotisation CNSS salarié'),
            ('indemnites', 'Total des indemnités forfaitaires'),
            ('salaire_base', 'Salaire de base'),
            ('primes', 'Total des primes'),
            ('heures_sup', 'Total heures supplémentaires'),
            ('anciennete_mois', 'Ancienneté en mois'),
            ('anciennete_ans', 'Ancienneté en années'),
            ('nb_enfants', 'Nombre d\'enfants'),
            ('nb_conjoints', 'Nombre de conjoints'),
            ('plafond_cnss', 'Plafond CNSS (2 500 000 GNF)'),
        ],
        'exemples_formules': {
            'exoneration': [
                ('Plafond 25% (CGI strict)', 'min(indemnites, brut * 0.25)'),
                ('Plafond 30%', 'min(indemnites, brut * 0.30)'),
                ('Exonération conditionnelle', 'indemnites if indemnites <= brut * 0.25 else brut * 0.25'),
            ],
            'base_vf': [
                ('Brut direct', 'brut'),
                ('Brut moins abattement', 'brut - 150000 if brut >= 2500000 else brut'),
                ('94% du brut', 'brut * 0.94'),
            ],
            'base_rts': [
                ('Formule standard', 'brut - cnss - min(indemnites, brut * 0.25)'),
                ('Avec plafond 30%', 'brut - cnss - min(indemnites, brut * 0.30)'),
            ],
        },
        'nb_historique': HistoriqueParametresPaie.objects.filter(parametres=params).count(),
    }
    return render(request, 'paie/parametres_calcul.html', contexte)


@login_required
@entreprise_active_required
def historique_parametres_paie(request):
    """
    Affiche l'historique des modifications des paramètres de calcul de paie.
    """
    entreprise = request.user.entreprise
    params = get_object_or_404(ParametresCalculPaie, entreprise=entreprise)
    historique = HistoriqueParametresPaie.objects.filter(
        parametres=params
    ).select_related('modifie_par').order_by('-date_modification')

    contexte = {
        'params': params,
        'historique': historique,
        'peut_modifier': _utilisateur_peut_modifier(request.user),
    }
    return render(request, 'paie/historique_parametres.html', contexte)


@login_required
@require_POST
def tester_formule_ajax(request):
    """
    Vue AJAX : teste une formule de paie avec des valeurs d'exemple
    et retourne le résultat en JSON.
    """
    try:
        body = json.loads(request.body)
        formule = body.get('formule', '').strip()
    except (json.JSONDecodeError, AttributeError):
        formule = request.POST.get('formule', '').strip()

    if not formule:
        return JsonResponse({'succes': False, 'erreur': 'Formule vide'})

    resultat = tester_formule(formule)
    if resultat.get('succes'):
        resultat['resultat'] = float(resultat['resultat'])
    return JsonResponse(resultat)


@login_required
@require_POST
def valider_formule_ajax(request):
    """
    Vue AJAX : valide une formule (détection d'erreurs et avertissements).
    Retourne JSON avec valide, erreurs, avertissements et resultat_test.
    """
    try:
        body = json.loads(request.body)
        formule = body.get('formule', '').strip()
    except (json.JSONDecodeError, AttributeError):
        formule = request.POST.get('formule', '').strip()

    if not formule:
        return JsonResponse({'valide': False, 'erreurs': ['Formule vide'], 'avertissements': []})

    resultat = valider_formule(formule)
    if resultat.get('resultat_test') is not None:
        resultat['resultat_test'] = float(resultat['resultat_test'])
    return JsonResponse(resultat)
