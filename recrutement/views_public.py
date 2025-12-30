"""
Vues publiques pour les candidatures - accessibles sans authentification
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import date
import uuid

from .models import OffreEmploi, Candidature


def offre_detail_public(request, pk):
    """Détail d'une offre d'emploi - vue publique"""
    offre = get_object_or_404(OffreEmploi, pk=pk, statut_offre='ouverte')
    
    # Vérifier si l'offre n'est pas expirée
    if offre.date_limite_candidature and offre.date_limite_candidature < date.today():
        messages.error(request, "Cette offre d'emploi a expiré.")
        return redirect('/')
    
    return render(request, 'recrutement/public/offre_detail.html', {
        'offre': offre,
    })


def postuler(request, pk):
    """Formulaire de candidature publique"""
    offre = get_object_or_404(OffreEmploi, pk=pk, statut_offre='ouverte')
    
    # Vérifier si la date limite n'est pas dépassée
    if offre.date_limite_candidature and offre.date_limite_candidature < date.today():
        messages.error(request, "La date limite de candidature est dépassée.")
        return redirect('recrutement:offre_public', pk=pk)
    
    if request.method == 'POST':
        # Générer un numéro de candidature unique
        numero = f"CAND-{offre.reference_offre}-{uuid.uuid4().hex[:6].upper()}"
        
        # Créer la candidature
        candidature = Candidature(
            offre=offre,
            numero_candidature=numero,
            civilite=request.POST.get('civilite', ''),
            nom=request.POST.get('nom', ''),
            prenoms=request.POST.get('prenoms', ''),
            email=request.POST.get('email', ''),
            telephone=request.POST.get('telephone', ''),
            date_naissance=request.POST.get('date_naissance') or None,
            nationalite=request.POST.get('nationalite', ''),
            adresse=request.POST.get('adresse', ''),
            formation_niveau=request.POST.get('formation_niveau', ''),
            experience_annees=request.POST.get('experience_annees') or None,
            statut_candidature='recue',
        )
        
        # Gérer les fichiers uploadés
        if 'cv_fichier' in request.FILES:
            candidature.cv_fichier = request.FILES['cv_fichier']
        if 'lettre_motivation' in request.FILES:
            candidature.lettre_motivation = request.FILES['lettre_motivation']
        if 'autres_documents' in request.FILES:
            candidature.autres_documents = request.FILES['autres_documents']
        
        candidature.save()
        
        messages.success(
            request, 
            f"Votre candidature a été enregistrée avec succès! "
            f"Référence: {numero}. L'entreprise {offre.entreprise.nom_entreprise} vous contactera."
        )
        return redirect('recrutement:candidature_confirmee', numero=numero)
    
    return render(request, 'recrutement/public/postuler.html', {
        'offre': offre,
    })


def candidature_confirmee(request, numero):
    """Page de confirmation après candidature"""
    candidature = get_object_or_404(Candidature, numero_candidature=numero)
    
    return render(request, 'recrutement/public/confirmation.html', {
        'candidature': candidature,
    })
