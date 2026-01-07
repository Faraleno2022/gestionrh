from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
from decimal import Decimal

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
            messages.success(request, f"Écriture {ecriture.numero_ecriture} créée.")
            return redirect('comptabilite:ecriture_detail', pk=ecriture.pk)
    else:
        form = EcritureForm(entreprise=entreprise)
    
    comptes = PlanComptable.objects.filter(entreprise=entreprise, est_actif=True)
    
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
            messages.success(request, "Écriture modifiée avec succès.")
            return redirect('comptabilite:ecriture_detail', pk=pk)
    else:
        form = EcritureForm(instance=ecriture, entreprise=request.user.entreprise)
    
    comptes = PlanComptable.objects.filter(entreprise=request.user.entreprise, est_actif=True)
    
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
    
    comptes = PlanComptable.objects.filter(entreprise=entreprise, est_actif=True)
    
    context = {
        'lignes': lignes,
        'comptes': comptes,
    }
    return render(request, 'comptabilite/etats/grand_livre.html', context)


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
    
    return render(request, 'comptabilite/etats/balance.html', {'comptes': comptes})


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
    
    # Actif (classes 2, 3, 4 débiteur, 5)
    actif = PlanComptable.objects.filter(
        entreprise=entreprise,
        classe__in=['2', '3', '5'],
        est_actif=True
    ).annotate(
        total_debit=Sum('lignes_ecritures__montant_debit'),
        total_credit=Sum('lignes_ecritures__montant_credit')
    )
    
    # Passif (classes 1, 4 créditeur)
    passif = PlanComptable.objects.filter(
        entreprise=entreprise,
        classe='1',
        est_actif=True
    ).annotate(
        total_debit=Sum('lignes_ecritures__montant_debit'),
        total_credit=Sum('lignes_ecritures__montant_credit')
    )
    
    context = {
        'actif': actif,
        'passif': passif,
    }
    return render(request, 'comptabilite/etats/bilan.html', context)


@login_required
@compta_required
def compte_resultat(request):
    """Compte de résultat"""
    entreprise = request.user.entreprise
    
    # Charges (classe 6)
    charges = PlanComptable.objects.filter(
        entreprise=entreprise,
        classe='6',
        est_actif=True
    ).annotate(
        total_debit=Sum('lignes_ecritures__montant_debit'),
        total_credit=Sum('lignes_ecritures__montant_credit')
    )
    
    # Produits (classe 7)
    produits = PlanComptable.objects.filter(
        entreprise=entreprise,
        classe='7',
        est_actif=True
    ).annotate(
        total_debit=Sum('lignes_ecritures__montant_debit'),
        total_credit=Sum('lignes_ecritures__montant_credit')
    )
    
    context = {
        'charges': charges,
        'produits': produits,
    }
    return render(request, 'comptabilite/etats/compte_resultat.html', context)
