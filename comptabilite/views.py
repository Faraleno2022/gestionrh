from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from decimal import Decimal
from collections import OrderedDict
import io

from .models import (
    PlanComptable, Journal, ExerciceComptable, EcritureComptable,
    LigneEcriture, Tiers, Facture, LigneFacture, Reglement, TauxTVA, PieceComptable
)
from .forms import (
    PlanComptableForm, JournalForm, ExerciceForm, EcritureForm,
    TiersForm, FactureForm, ReglementForm
)


def compta_required(view_func):
    """Décorateur pour vérifier l'accès au module comptabilité"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.entreprise:
            messages.error(request, "Vous devez être associé à une entreprise.")
            return redirect('core:index')
        if not request.user.entreprise.has_compta:
            messages.error(request, "Votre entreprise n'a pas accès au module comptabilité.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@compta_required
def dashboard(request):
    """Dashboard principal comptabilité"""
    entreprise = request.user.entreprise
    
    # Statistiques
    exercice_courant = ExerciceComptable.objects.filter(
        entreprise=entreprise, est_courant=True
    ).first()
    
    stats = {
        'nb_ecritures': EcritureComptable.objects.filter(entreprise=entreprise).count(),
        'nb_factures_impayees': Facture.objects.filter(
            entreprise=entreprise, statut__in=['validee']
        ).count(),
        'nb_tiers': Tiers.objects.filter(entreprise=entreprise, est_actif=True).count(),
        'nb_comptes': PlanComptable.objects.filter(entreprise=entreprise, est_actif=True).count(),
    }
    
    # Dernières écritures
    dernieres_ecritures = EcritureComptable.objects.filter(
        entreprise=entreprise
    ).select_related('journal').order_by('-date_creation')[:5]
    
    # Factures en attente
    factures_en_attente = Facture.objects.filter(
        entreprise=entreprise, statut='validee'
    ).select_related('tiers').order_by('date_echeance')[:5]
    
    context = {
        'stats': stats,
        'exercice_courant': exercice_courant,
        'dernieres_ecritures': dernieres_ecritures,
        'factures_en_attente': factures_en_attente,
    }
    return render(request, 'comptabilite/dashboard.html', context)


# ==================== PLAN COMPTABLE ====================

@login_required
@compta_required
def plan_comptable_list(request):
    """Liste du plan comptable"""
    entreprise = request.user.entreprise
    classe = request.GET.get('classe', '')
    search = request.GET.get('q', '')
    
    comptes = PlanComptable.objects.filter(entreprise=entreprise)
    
    if classe:
        comptes = comptes.filter(classe=classe)
    if search:
        comptes = comptes.filter(
            Q(numero_compte__icontains=search) | Q(intitule__icontains=search)
        )
    
    comptes = comptes.order_by('numero_compte')
    
    paginator = Paginator(comptes, 50)
    page = request.GET.get('page', 1)
    comptes = paginator.get_page(page)
    
    context = {
        'comptes': comptes,
        'classes': PlanComptable.CLASSES,
        'classe_selectionnee': classe,
        'search': search,
    }
    return render(request, 'comptabilite/plan_comptable/list.html', context)


@login_required
@compta_required
def plan_comptable_create(request):
    """Créer un compte comptable"""
    if request.method == 'POST':
        form = PlanComptableForm(request.POST, entreprise=request.user.entreprise)
        if form.is_valid():
            compte = form.save(commit=False)
            compte.entreprise = request.user.entreprise
            compte.classe = compte.numero_compte[0] if compte.numero_compte else '1'
            compte.save()
            messages.success(request, f"Compte {compte.numero_compte} créé avec succès.")
            return redirect('comptabilite:plan_comptable_list')
    else:
        form = PlanComptableForm(entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/plan_comptable/form.html', {'form': form})


@login_required
@compta_required
def plan_comptable_detail(request, pk):
    """Détail d'un compte comptable"""
    compte = get_object_or_404(PlanComptable, pk=pk, entreprise=request.user.entreprise)
    
    # Mouvements du compte
    lignes = LigneEcriture.objects.filter(
        compte=compte
    ).select_related('ecriture', 'ecriture__journal').order_by('-ecriture__date_ecriture')[:50]
    
    context = {
        'compte': compte,
        'lignes': lignes,
    }
    return render(request, 'comptabilite/plan_comptable/detail.html', context)


@login_required
@compta_required
def plan_comptable_update(request, pk):
    """Modifier un compte comptable"""
    compte = get_object_or_404(PlanComptable, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        form = PlanComptableForm(request.POST, instance=compte, entreprise=request.user.entreprise)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte modifié avec succès.")
            return redirect('comptabilite:plan_comptable_list')
    else:
        form = PlanComptableForm(instance=compte, entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/plan_comptable/form.html', {'form': form, 'compte': compte})


# ==================== JOURNAUX ====================

@login_required
@compta_required
def journal_list(request):
    """Liste des journaux"""
    journaux = Journal.objects.filter(entreprise=request.user.entreprise)
    return render(request, 'comptabilite/journaux/list.html', {'journaux': journaux})


@login_required
@compta_required
def journal_create(request):
    """Créer un journal"""
    if request.method == 'POST':
        form = JournalForm(request.POST, entreprise=request.user.entreprise)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.entreprise = request.user.entreprise
            journal.save()
            messages.success(request, f"Journal {journal.code} créé avec succès.")
            return redirect('comptabilite:journal_list')
    else:
        form = JournalForm(entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/journaux/form.html', {'form': form})


@login_required
@compta_required
def journal_update(request, pk):
    """Modifier un journal"""
    journal = get_object_or_404(Journal, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        form = JournalForm(request.POST, instance=journal, entreprise=request.user.entreprise)
        if form.is_valid():
            form.save()
            messages.success(request, "Journal modifié avec succès.")
            return redirect('comptabilite:journal_list')
    else:
        form = JournalForm(instance=journal, entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/journaux/form.html', {'form': form, 'journal': journal})


# ==================== EXERCICES ====================

@login_required
@compta_required
def exercice_list(request):
    """Liste des exercices comptables"""
    exercices = ExerciceComptable.objects.filter(entreprise=request.user.entreprise)
    return render(request, 'comptabilite/exercices/list.html', {'exercices': exercices})


@login_required
@compta_required
def exercice_create(request):
    """Créer un exercice"""
    if request.method == 'POST':
        form = ExerciceForm(request.POST)
        if form.is_valid():
            exercice = form.save(commit=False)
            exercice.entreprise = request.user.entreprise
            exercice.save()
            messages.success(request, f"Exercice {exercice.libelle} créé avec succès.")
            return redirect('comptabilite:exercice_list')
    else:
        form = ExerciceForm()
    
    return render(request, 'comptabilite/exercices/form.html', {'form': form})


@login_required
@compta_required
def exercice_update(request, pk):
    """Modifier un exercice"""
    exercice = get_object_or_404(ExerciceComptable, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        form = ExerciceForm(request.POST, instance=exercice)
        if form.is_valid():
            form.save()
            messages.success(request, "Exercice modifié avec succès.")
            return redirect('comptabilite:exercice_list')
    else:
        form = ExerciceForm(instance=exercice)
    
    return render(request, 'comptabilite/exercices/form.html', {'form': form, 'exercice': exercice})


# ==================== ÉCRITURES ====================

@login_required
@compta_required
def ecriture_list(request):
    """Liste des écritures comptables"""
    entreprise = request.user.entreprise
    journal_id = request.GET.get('journal', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    ecritures = EcritureComptable.objects.filter(
        entreprise=entreprise
    ).select_related('journal', 'exercice')
    
    if journal_id:
        ecritures = ecritures.filter(journal_id=journal_id)
    if date_debut:
        ecritures = ecritures.filter(date_ecriture__gte=date_debut)
    if date_fin:
        ecritures = ecritures.filter(date_ecriture__lte=date_fin)
    
    ecritures = ecritures.order_by('-date_ecriture', '-numero_ecriture')
    
    paginator = Paginator(ecritures, 25)
    page = request.GET.get('page', 1)
    ecritures = paginator.get_page(page)
    
    journaux = Journal.objects.filter(entreprise=entreprise, est_actif=True)
    
    context = {
        'ecritures': ecritures,
        'journaux': journaux,
    }
    return render(request, 'comptabilite/ecritures/list.html', context)


@login_required
@compta_required
def ecriture_create(request):
    """Créer une écriture comptable"""
    entreprise = request.user.entreprise
    
    if request.method == 'POST':
        form = EcritureForm(request.POST, entreprise=entreprise)
        if form.is_valid():
            ecriture = form.save(commit=False)
            ecriture.entreprise = entreprise
            ecriture.save()
            
            # Traiter les lignes d'écriture
            comptes_ids = request.POST.getlist('compte[]')
            libelles = request.POST.getlist('libelle_ligne[]')
            debits = request.POST.getlist('debit[]')
            credits = request.POST.getlist('credit[]')
            
            for i, compte_id in enumerate(comptes_ids):
                if compte_id:
                    debit = Decimal(debits[i]) if debits[i] else Decimal('0')
                    credit = Decimal(credits[i]) if credits[i] else Decimal('0')
                    
                    if debit > 0 or credit > 0:
                        LigneEcriture.objects.create(
                            ecriture=ecriture,
                            compte_id=compte_id,
                            libelle=libelles[i] if i < len(libelles) else '',
                            montant_debit=debit,
                            montant_credit=credit
                        )
            
            messages.success(request, f"Écriture {ecriture.numero_ecriture} créée avec {ecriture.lignes.count()} lignes.")
            return redirect('comptabilite:ecriture_detail', pk=ecriture.pk)
    else:
        form = EcritureForm(entreprise=entreprise)
    
    comptes = PlanComptable.objects.filter(entreprise=entreprise, est_actif=True).order_by('numero_compte')
    
    context = {
        'form': form,
        'comptes': comptes,
    }
    return render(request, 'comptabilite/ecritures/form.html', context)


@login_required
@compta_required
def ecriture_detail(request, pk):
    """Détail d'une écriture"""
    ecriture = get_object_or_404(
        EcritureComptable.objects.prefetch_related('lignes__compte'),
        pk=pk, entreprise=request.user.entreprise
    )
    return render(request, 'comptabilite/ecritures/detail.html', {'ecriture': ecriture})


@login_required
@compta_required
def ecriture_update(request, pk):
    """Modifier une écriture"""
    ecriture = get_object_or_404(EcritureComptable, pk=pk, entreprise=request.user.entreprise)
    
    if ecriture.est_validee:
        messages.error(request, "Impossible de modifier une écriture validée.")
        return redirect('comptabilite:ecriture_detail', pk=pk)
    
    if request.method == 'POST':
        form = EcritureForm(request.POST, instance=ecriture, entreprise=request.user.entreprise)
        if form.is_valid():
            form.save()
            
            # Supprimer les anciennes lignes et recréer
            ecriture.lignes.all().delete()
            
            comptes_ids = request.POST.getlist('compte[]')
            libelles = request.POST.getlist('libelle_ligne[]')
            debits = request.POST.getlist('debit[]')
            credits = request.POST.getlist('credit[]')
            
            for i, compte_id in enumerate(comptes_ids):
                if compte_id:
                    debit = Decimal(debits[i]) if debits[i] else Decimal('0')
                    credit = Decimal(credits[i]) if credits[i] else Decimal('0')
                    
                    if debit > 0 or credit > 0:
                        LigneEcriture.objects.create(
                            ecriture=ecriture,
                            compte_id=compte_id,
                            libelle=libelles[i] if i < len(libelles) else '',
                            montant_debit=debit,
                            montant_credit=credit
                        )
            
            messages.success(request, "Écriture modifiée avec succès.")
            return redirect('comptabilite:ecriture_detail', pk=pk)
    else:
        form = EcritureForm(instance=ecriture, entreprise=request.user.entreprise)
    
    comptes = PlanComptable.objects.filter(entreprise=request.user.entreprise, est_actif=True).order_by('numero_compte')
    
    context = {
        'form': form,
        'ecriture': ecriture,
        'comptes': comptes,
    }
    return render(request, 'comptabilite/ecritures/form.html', context)


@login_required
@compta_required
def ecriture_valider(request, pk):
    """Valider une écriture"""
    ecriture = get_object_or_404(EcritureComptable, pk=pk, entreprise=request.user.entreprise)
    
    if not ecriture.est_equilibree:
        messages.error(request, "L'écriture n'est pas équilibrée.")
        return redirect('comptabilite:ecriture_detail', pk=pk)
    
    ecriture.est_validee = True
    ecriture.date_validation = timezone.now()
    ecriture.validee_par = request.user
    ecriture.save()
    
    messages.success(request, "Écriture validée avec succès.")
    return redirect('comptabilite:ecriture_detail', pk=pk)


# ==================== TIERS ====================

@login_required
@compta_required
def tiers_list(request):
    """Liste des tiers"""
    entreprise = request.user.entreprise
    type_tiers = request.GET.get('type', '')
    search = request.GET.get('q', '')
    
    tiers = Tiers.objects.filter(entreprise=entreprise)
    
    if type_tiers:
        tiers = tiers.filter(type_tiers=type_tiers)
    if search:
        tiers = tiers.filter(
            Q(code__icontains=search) | Q(raison_sociale__icontains=search)
        )
    
    paginator = Paginator(tiers, 25)
    page = request.GET.get('page', 1)
    tiers = paginator.get_page(page)
    
    context = {
        'tiers': tiers,
        'types_tiers': Tiers.TYPES_TIERS,
    }
    return render(request, 'comptabilite/tiers/list.html', context)


@login_required
@compta_required
def tiers_create(request):
    """Créer un tiers"""
    if request.method == 'POST':
        form = TiersForm(request.POST, entreprise=request.user.entreprise)
        if form.is_valid():
            tiers = form.save(commit=False)
            tiers.entreprise = request.user.entreprise
            tiers.save()
            messages.success(request, f"Tiers {tiers.raison_sociale} créé avec succès.")
            return redirect('comptabilite:tiers_list')
    else:
        form = TiersForm(entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/tiers/form.html', {'form': form})


@login_required
@compta_required
def tiers_detail(request, pk):
    """Détail d'un tiers"""
    tiers = get_object_or_404(Tiers, pk=pk, entreprise=request.user.entreprise)
    factures = Facture.objects.filter(tiers=tiers).order_by('-date_facture')[:10]
    
    context = {
        'tiers': tiers,
        'factures': factures,
    }
    return render(request, 'comptabilite/tiers/detail.html', context)


@login_required
@compta_required
def tiers_update(request, pk):
    """Modifier un tiers"""
    tiers = get_object_or_404(Tiers, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        form = TiersForm(request.POST, instance=tiers, entreprise=request.user.entreprise)
        if form.is_valid():
            form.save()
            messages.success(request, "Tiers modifié avec succès.")
            return redirect('comptabilite:tiers_detail', pk=pk)
    else:
        form = TiersForm(instance=tiers, entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/tiers/form.html', {'form': form, 'tiers': tiers})


# ==================== FACTURES ====================

@login_required
@compta_required
def facture_list(request):
    """Liste des factures"""
    entreprise = request.user.entreprise
    type_facture = request.GET.get('type', '')
    statut = request.GET.get('statut', '')
    
    factures = Facture.objects.filter(entreprise=entreprise).select_related('tiers')
    
    if type_facture:
        factures = factures.filter(type_facture=type_facture)
    if statut:
        factures = factures.filter(statut=statut)
    
    paginator = Paginator(factures, 25)
    page = request.GET.get('page', 1)
    factures = paginator.get_page(page)
    
    context = {
        'factures': factures,
        'types_facture': Facture.TYPES_FACTURE,
        'statuts': Facture.STATUTS,
    }
    return render(request, 'comptabilite/factures/list.html', context)


@login_required
@compta_required
def facture_create(request):
    """Créer une facture"""
    type_facture = request.GET.get('type', 'vente')
    
    if request.method == 'POST':
        form = FactureForm(request.POST, entreprise=request.user.entreprise)
        if form.is_valid():
            facture = form.save(commit=False)
            facture.entreprise = request.user.entreprise
            facture.save()
            messages.success(request, f"Facture {facture.numero} créée.")
            return redirect('comptabilite:facture_detail', pk=facture.pk)
    else:
        form = FactureForm(entreprise=request.user.entreprise, initial={'type_facture': type_facture})
    
    return render(request, 'comptabilite/factures/form.html', {'form': form})


@login_required
@compta_required
def facture_detail(request, pk):
    """Détail d'une facture"""
    facture = get_object_or_404(
        Facture.objects.prefetch_related('lignes', 'reglements'),
        pk=pk, entreprise=request.user.entreprise
    )
    return render(request, 'comptabilite/factures/detail.html', {'facture': facture})


@login_required
@compta_required
def facture_update(request, pk):
    """Modifier une facture"""
    facture = get_object_or_404(Facture, pk=pk, entreprise=request.user.entreprise)
    
    if facture.statut != 'brouillon':
        messages.error(request, "Seules les factures en brouillon peuvent être modifiées.")
        return redirect('comptabilite:facture_detail', pk=pk)
    
    if request.method == 'POST':
        form = FactureForm(request.POST, instance=facture, entreprise=request.user.entreprise)
        if form.is_valid():
            form.save()
            messages.success(request, "Facture modifiée avec succès.")
            return redirect('comptabilite:facture_detail', pk=pk)
    else:
        form = FactureForm(instance=facture, entreprise=request.user.entreprise)
    
    return render(request, 'comptabilite/factures/form.html', {'form': form, 'facture': facture})


@login_required
@compta_required
def facture_valider(request, pk):
    """Valider une facture"""
    facture = get_object_or_404(Facture, pk=pk, entreprise=request.user.entreprise)
    
    if facture.statut != 'brouillon':
        messages.error(request, "Cette facture ne peut pas être validée.")
        return redirect('comptabilite:facture_detail', pk=pk)
    
    facture.statut = 'validee'
    facture.save()
    
    messages.success(request, "Facture validée avec succès.")
    return redirect('comptabilite:facture_detail', pk=pk)


@login_required
@compta_required
def facture_print(request, pk):
    """Imprimer une facture"""
    facture = get_object_or_404(
        Facture.objects.prefetch_related('lignes'),
        pk=pk, entreprise=request.user.entreprise
    )
    return render(request, 'comptabilite/factures/print.html', {'facture': facture})


# ==================== RÈGLEMENTS ====================

@login_required
@compta_required
def reglement_list(request):
    """Liste des règlements"""
    reglements = Reglement.objects.filter(
        entreprise=request.user.entreprise
    ).select_related('facture', 'facture__tiers')
    
    paginator = Paginator(reglements, 25)
    page = request.GET.get('page', 1)
    reglements = paginator.get_page(page)
    
    return render(request, 'comptabilite/reglements/list.html', {'reglements': reglements})


@login_required
@compta_required
def reglement_create(request):
    """Créer un règlement"""
    facture_id = request.GET.get('facture', '')
    
    if request.method == 'POST':
        form = ReglementForm(request.POST, entreprise=request.user.entreprise)
        if form.is_valid():
            reglement = form.save(commit=False)
            reglement.entreprise = request.user.entreprise
            reglement.save()
            
            # Mettre à jour le montant payé sur la facture
            facture = reglement.facture
            facture.montant_paye += reglement.montant
            if facture.montant_paye >= facture.montant_ttc:
                facture.statut = 'payee'
            facture.save()
            
            messages.success(request, "Règlement enregistré avec succès.")
            return redirect('comptabilite:facture_detail', pk=facture.pk)
    else:
        initial = {}
        if facture_id:
            initial['facture'] = facture_id
        form = ReglementForm(entreprise=request.user.entreprise, initial=initial)
    
    return render(request, 'comptabilite/reglements/form.html', {'form': form})


@login_required
@compta_required
def reglement_detail(request, pk):
    """Détail d'un règlement"""
    reglement = get_object_or_404(
        Reglement.objects.select_related('facture', 'facture__tiers'),
        pk=pk, entreprise=request.user.entreprise
    )
    return render(request, 'comptabilite/reglements/detail.html', {'reglement': reglement})


# ==================== ÉTATS FINANCIERS ====================

@login_required
@compta_required
def grand_livre(request):
    """Grand livre comptable"""
    entreprise = request.user.entreprise
    compte_id = request.GET.get('compte', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    lignes = LigneEcriture.objects.filter(
        ecriture__entreprise=entreprise,
        ecriture__est_validee=True
    ).select_related('compte', 'ecriture', 'ecriture__journal')
    
    if compte_id:
        lignes = lignes.filter(compte_id=compte_id)
    if date_debut:
        lignes = lignes.filter(ecriture__date_ecriture__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(ecriture__date_ecriture__lte=date_fin)
    
    lignes = lignes.order_by('compte__numero_compte', 'ecriture__date_ecriture')
    
    # Regrouper les lignes par compte avec totaux
    from collections import OrderedDict
    comptes_groupes = OrderedDict()
    for ligne in lignes:
        compte = ligne.compte
        if compte.pk not in comptes_groupes:
            comptes_groupes[compte.pk] = {
                'compte': compte,
                'lignes': [],
                'total_debit': Decimal('0'),
                'total_credit': Decimal('0'),
            }
        comptes_groupes[compte.pk]['lignes'].append(ligne)
        comptes_groupes[compte.pk]['total_debit'] += ligne.montant_debit or Decimal('0')
        comptes_groupes[compte.pk]['total_credit'] += ligne.montant_credit or Decimal('0')
    
    comptes = PlanComptable.objects.filter(entreprise=entreprise, est_actif=True).order_by('numero_compte')
    
    context = {
        'comptes_groupes': comptes_groupes.values(),
        'comptes': comptes,
        'compte_id': compte_id,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    return render(request, 'comptabilite/etats/grand_livre.html', context)


def _get_grand_livre_data(request):
    """Helper pour récupérer les données du grand livre"""
    entreprise = request.user.entreprise
    compte_id = request.GET.get('compte', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    lignes = LigneEcriture.objects.filter(
        ecriture__entreprise=entreprise,
        ecriture__est_validee=True
    ).select_related('compte', 'ecriture', 'ecriture__journal')
    
    if compte_id:
        lignes = lignes.filter(compte_id=compte_id)
    if date_debut:
        lignes = lignes.filter(ecriture__date_ecriture__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(ecriture__date_ecriture__lte=date_fin)
    
    lignes = lignes.order_by('compte__numero_compte', 'ecriture__date_ecriture')
    
    comptes_groupes = OrderedDict()
    for ligne in lignes:
        compte = ligne.compte
        if compte.pk not in comptes_groupes:
            comptes_groupes[compte.pk] = {
                'compte': compte,
                'lignes': [],
                'total_debit': Decimal('0'),
                'total_credit': Decimal('0'),
            }
        comptes_groupes[compte.pk]['lignes'].append(ligne)
        comptes_groupes[compte.pk]['total_debit'] += ligne.montant_debit or Decimal('0')
        comptes_groupes[compte.pk]['total_credit'] += ligne.montant_credit or Decimal('0')
    
    return comptes_groupes, entreprise, date_debut, date_fin


@login_required
@compta_required
def grand_livre_excel(request):
    """Export Excel du Grand Livre"""
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter
    
    comptes_groupes, entreprise, date_debut, date_fin = _get_grand_livre_data(request)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Grand Livre"
    
    # Styles
    header_font = Font(bold=True, size=14)
    title_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="FFD699", end_color="FFD699", fill_type="solid")
    total_fill = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    # En-tête
    ws.merge_cells('A1:F1')
    ws['A1'] = entreprise.nom_entreprise
    ws['A1'].font = header_font
    ws['A1'].alignment = Alignment(horizontal='center')
    
    ws.merge_cells('A2:F2')
    periode = f"GRAND LIVRE - Du {date_debut or '--'} au {date_fin or '--'}"
    ws['A2'] = periode
    ws['A2'].alignment = Alignment(horizontal='center')
    
    row = 4
    for groupe in comptes_groupes.values():
        compte = groupe['compte']
        
        # En-tête du compte
        ws.merge_cells(f'A{row}:F{row}')
        ws[f'A{row}'] = f"{compte.numero_compte} - {compte.intitule}"
        ws[f'A{row}'].font = title_font
        ws[f'A{row}'].fill = header_fill
        row += 1
        
        # En-têtes colonnes
        headers = ['Date', 'Journal', 'N° Pièce', 'Libellé', 'Débit', 'Crédit']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.border = thin_border
        row += 1
        
        # Lignes
        for ligne in groupe['lignes']:
            ws.cell(row=row, column=1, value=ligne.ecriture.date_ecriture.strftime('%d/%m/%Y')).border = thin_border
            ws.cell(row=row, column=2, value=ligne.ecriture.journal.code).border = thin_border
            ws.cell(row=row, column=3, value=ligne.ecriture.numero_ecriture).border = thin_border
            ws.cell(row=row, column=4, value=ligne.libelle or ligne.ecriture.libelle).border = thin_border
            cell_d = ws.cell(row=row, column=5, value=float(ligne.montant_debit) if ligne.montant_debit else None)
            cell_d.border = thin_border
            cell_d.number_format = '#,##0'
            cell_c = ws.cell(row=row, column=6, value=float(ligne.montant_credit) if ligne.montant_credit else None)
            cell_c.border = thin_border
            cell_c.number_format = '#,##0'
            row += 1
        
        # Total compte
        ws.merge_cells(f'A{row}:D{row}')
        ws[f'A{row}'] = f"Total compte {compte.numero_compte}"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = total_fill
        ws[f'A{row}'].alignment = Alignment(horizontal='right')
        cell_td = ws.cell(row=row, column=5, value=float(groupe['total_debit']))
        cell_td.font = Font(bold=True)
        cell_td.fill = total_fill
        cell_td.number_format = '#,##0'
        cell_tc = ws.cell(row=row, column=6, value=float(groupe['total_credit']))
        cell_tc.font = Font(bold=True)
        cell_tc.fill = total_fill
        cell_tc.number_format = '#,##0'
        row += 2
    
    # Ajuster largeurs colonnes
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 40
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 15
    
    # Réponse
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="grand_livre_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)
    return response


@login_required
@compta_required
def grand_livre_pdf(request):
    """Export PDF du Grand Livre"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    comptes_groupes, entreprise, date_debut, date_fin = _get_grand_livre_data(request)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=10)
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, alignment=1, spaceAfter=20)
    compte_style = ParagraphStyle('Compte', parent=styles['Heading3'], fontSize=11, backColor=colors.HexColor('#FFD699'), spaceAfter=5)
    
    elements = []
    
    # En-tête
    elements.append(Paragraph(entreprise.nom_entreprise, title_style))
    periode = f"GRAND LIVRE COMPTABLE - Du {date_debut or '--/--/----'} au {date_fin or '--/--/----'}"
    elements.append(Paragraph(periode, subtitle_style))
    
    for groupe in comptes_groupes.values():
        compte = groupe['compte']
        
        # Titre du compte
        elements.append(Paragraph(f"<b>{compte.numero_compte}</b> - {compte.intitule}", compte_style))
        
        # Table des lignes
        data = [['Date', 'Journal', 'N° Pièce', 'Libellé', 'Débit', 'Crédit']]
        for ligne in groupe['lignes']:
            data.append([
                ligne.ecriture.date_ecriture.strftime('%d/%m/%Y'),
                ligne.ecriture.journal.code,
                ligne.ecriture.numero_ecriture,
                (ligne.libelle or ligne.ecriture.libelle)[:50],
                f"{ligne.montant_debit:,.0f}" if ligne.montant_debit else '',
                f"{ligne.montant_credit:,.0f}" if ligne.montant_credit else '',
            ])
        
        # Ligne total
        data.append([
            '', '', '', f"Total compte {compte.numero_compte}",
            f"{groupe['total_debit']:,.0f}",
            f"{groupe['total_credit']:,.0f}"
        ])
        
        table = Table(data, colWidths=[2.5*cm, 2*cm, 3*cm, 10*cm, 3.5*cm, 3.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EF7707')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (4, 0), (5, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.5*cm))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="grand_livre_{timezone.now().strftime("%Y%m%d")}.pdf"'
    return response


@login_required
@compta_required
def balance(request):
    """Balance générale"""
    entreprise = request.user.entreprise
    
    comptes = PlanComptable.objects.filter(
        entreprise=entreprise, est_actif=True
    ).annotate(
        total_debit=Sum('lignes_ecritures__montant_debit'),
        total_credit=Sum('lignes_ecritures__montant_credit')
    ).order_by('numero_compte')
    
    # Calculer les totaux
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    total_solde_debit = Decimal('0')
    total_solde_credit = Decimal('0')
    
    for c in comptes:
        d = c.total_debit or Decimal('0')
        cr = c.total_credit or Decimal('0')
        total_debit += d
        total_credit += cr
        if d > cr:
            total_solde_debit += (d - cr)
        else:
            total_solde_credit += (cr - d)
    
    context = {
        'comptes': comptes,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'total_solde_debit': total_solde_debit,
        'total_solde_credit': total_solde_credit,
        'today': timezone.now().date(),
    }
    return render(request, 'comptabilite/etats/balance.html', context)


@login_required
@compta_required
def journal_general(request):
    """Journal général"""
    entreprise = request.user.entreprise
    journal_id = request.GET.get('journal', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    ecritures = EcritureComptable.objects.filter(
        entreprise=entreprise,
        est_validee=True
    ).prefetch_related('lignes__compte').select_related('journal')
    
    if journal_id:
        ecritures = ecritures.filter(journal_id=journal_id)
    if date_debut:
        ecritures = ecritures.filter(date_ecriture__gte=date_debut)
    if date_fin:
        ecritures = ecritures.filter(date_ecriture__lte=date_fin)
    
    ecritures = ecritures.order_by('date_ecriture', 'numero_ecriture')
    
    journaux = Journal.objects.filter(entreprise=entreprise, est_actif=True)
    
    context = {
        'ecritures': ecritures,
        'journaux': journaux,
    }
    return render(request, 'comptabilite/etats/journal_general.html', context)


@login_required
@compta_required
def bilan(request):
    """Bilan comptable"""
    entreprise = request.user.entreprise
    
    exercice = ExerciceComptable.objects.filter(entreprise=entreprise, est_courant=True).first()
    
    def get_comptes_avec_solde(classes):
        comptes = PlanComptable.objects.filter(
            entreprise=entreprise,
            classe__in=classes,
            est_actif=True
        ).annotate(
            total_debit=Sum('lignes_ecritures__montant_debit'),
            total_credit=Sum('lignes_ecritures__montant_credit')
        ).order_by('numero_compte')
        
        result = []
        for c in comptes:
            d = c.total_debit or Decimal('0')
            cr = c.total_credit or Decimal('0')
            solde = d - cr if d > cr else cr - d
            if solde > 0:
                result.append({'numero_compte': c.numero_compte, 'intitule': c.intitule, 'solde': solde, 'debiteur': d > cr})
        return result
    
    # Actif immobilisé (classe 2)
    actif_immobilise = get_comptes_avec_solde(['2'])
    
    # Actif circulant (classes 3, 4 débiteur, 5)
    actif_circulant = get_comptes_avec_solde(['3', '5'])
    # Ajouter comptes classe 4 débiteurs
    comptes_4 = PlanComptable.objects.filter(entreprise=entreprise, classe='4', est_actif=True).annotate(
        total_debit=Sum('lignes_ecritures__montant_debit'),
        total_credit=Sum('lignes_ecritures__montant_credit')
    )
    for c in comptes_4:
        d = c.total_debit or Decimal('0')
        cr = c.total_credit or Decimal('0')
        if d > cr:
            actif_circulant.append({'numero_compte': c.numero_compte, 'intitule': c.intitule, 'solde': d - cr, 'debiteur': True})
    
    # Capitaux propres (classe 1)
    capitaux_propres = get_comptes_avec_solde(['1'])
    
    # Dettes (classe 4 créditeur)
    dettes = []
    for c in comptes_4:
        d = c.total_debit or Decimal('0')
        cr = c.total_credit or Decimal('0')
        if cr > d:
            dettes.append({'numero_compte': c.numero_compte, 'intitule': c.intitule, 'solde': cr - d, 'debiteur': False})
    
    # Totaux
    total_actif = sum(c['solde'] for c in actif_immobilise) + sum(c['solde'] for c in actif_circulant)
    total_passif = sum(c['solde'] for c in capitaux_propres) + sum(c['solde'] for c in dettes)
    ecart = total_actif - total_passif
    
    context = {
        'actif_immobilise': actif_immobilise,
        'actif_circulant': actif_circulant,
        'capitaux_propres': capitaux_propres,
        'dettes': dettes,
        'total_actif': total_actif,
        'total_passif': total_passif,
        'ecart': ecart,
        'exercice': exercice,
        'today': timezone.now().date(),
    }
    return render(request, 'comptabilite/etats/bilan.html', context)


@login_required
@compta_required
def compte_resultat(request):
    """Compte de résultat"""
    entreprise = request.user.entreprise
    exercice = ExerciceComptable.objects.filter(entreprise=entreprise, est_courant=True).first()
    
    def get_comptes_classe(classe_prefix):
        comptes = PlanComptable.objects.filter(
            entreprise=entreprise,
            numero_compte__startswith=classe_prefix,
            est_actif=True
        ).annotate(
            total_debit=Sum('lignes_ecritures__montant_debit'),
            total_credit=Sum('lignes_ecritures__montant_credit')
        ).order_by('numero_compte')
        
        result = []
        for c in comptes:
            d = c.total_debit or Decimal('0')
            cr = c.total_credit or Decimal('0')
            solde = d - cr if d > cr else cr - d
            if solde > 0:
                result.append({'numero_compte': c.numero_compte, 'intitule': c.intitule, 'solde': solde})
        return result
    
    # Charges d'exploitation (60-65)
    charges_exploitation = get_comptes_classe('60') + get_comptes_classe('61') + get_comptes_classe('62') + get_comptes_classe('63') + get_comptes_classe('64') + get_comptes_classe('65')
    
    # Charges financières (66-67)
    charges_financieres = get_comptes_classe('66') + get_comptes_classe('67')
    
    # Produits d'exploitation (70-75)
    produits_exploitation = get_comptes_classe('70') + get_comptes_classe('71') + get_comptes_classe('72') + get_comptes_classe('73') + get_comptes_classe('74') + get_comptes_classe('75')
    
    # Produits financiers (76-77)
    produits_financiers = get_comptes_classe('76') + get_comptes_classe('77')
    
    # Totaux
    total_charges = sum(c['solde'] for c in charges_exploitation) + sum(c['solde'] for c in charges_financieres)
    total_produits = sum(c['solde'] for c in produits_exploitation) + sum(c['solde'] for c in produits_financiers)
    resultat = total_produits - total_charges
    
    context = {
        'charges_exploitation': charges_exploitation,
        'charges_financieres': charges_financieres,
        'produits_exploitation': produits_exploitation,
        'produits_financiers': produits_financiers,
        'total_charges': total_charges,
        'total_produits': total_produits,
        'resultat': resultat,
        'exercice': exercice,
        'today': timezone.now().date(),
    }
    return render(request, 'comptabilite/etats/compte_resultat.html', context)
