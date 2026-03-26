"""
Vues pour les paramètres de calcul de paie personnalisés.
"""
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.decorators import reauth_required, entreprise_active_required
from .models import ParametresCalculPaie
from .formules import tester_formule


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
    # Rechargement depuis la relation directe (related_name='parametres_calcul_paie')

    if request.method == 'POST':
        # Indemnités forfaitaires
        params.mode_exoneration_indemnites = request.POST.get(
            'mode_exoneration_indemnites', 'plafond_pct'
        )
        pct_raw = request.POST.get('plafond_exoneration_pct', '25')
        try:
            from decimal import Decimal
            params.plafond_exoneration_pct = Decimal(pct_raw)
        except Exception:
            params.plafond_exoneration_pct = Decimal('25')
        params.formule_exoneration = request.POST.get('formule_exoneration', '').strip()

        # Base VF/TA
        params.mode_base_vf = request.POST.get('mode_base_vf', 'brut')
        params.formule_base_vf = request.POST.get('formule_base_vf', '').strip()

        # Base RTS
        params.utiliser_formule_base_rts = (
            request.POST.get('utiliser_formule_base_rts') == 'on'
        )
        params.formule_base_rts = request.POST.get('formule_base_rts', '').strip()

        params.save()
        messages.success(request, "Paramètres de calcul enregistrés avec succès.")
        return redirect('paie:parametres_calcul')

    contexte = {
        'params': params,
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
    }
    return render(request, 'paie/parametres_calcul.html', contexte)


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
