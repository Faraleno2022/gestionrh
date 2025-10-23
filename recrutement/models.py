from django.db import models
from core.models import Poste, Service
from employes.models import Employe


class OffreEmploi(models.Model):
    """Offres d'emploi"""
    STATUTS = (
        ('ouverte', 'Ouverte'),
        ('fermee', 'Fermée'),
        ('pourvue', 'Pourvue'),
        ('annulee', 'Annulée'),
    )
    
    reference_offre = models.CharField(max_length=50, unique=True)
    intitule_poste = models.CharField(max_length=200)
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    type_contrat = models.CharField(max_length=20, blank=True, null=True)
    nombre_postes = models.IntegerField(default=1)
    date_publication = models.DateField(auto_now_add=True)
    date_limite_candidature = models.DateField(blank=True, null=True)
    date_cloture = models.DateField(blank=True, null=True)
    description_poste = models.TextField(blank=True, null=True)
    profil_recherche = models.TextField(blank=True, null=True)
    competences_requises = models.TextField(blank=True, null=True)
    experience_requise = models.IntegerField(blank=True, null=True)
    formation_requise = models.CharField(max_length=200, blank=True, null=True)
    salaire_propose_min = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    salaire_propose_max = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    avantages = models.TextField(blank=True, null=True)
    statut_offre = models.CharField(max_length=20, choices=STATUTS, default='ouverte')
    responsable_recrutement = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'offres_emploi'
        verbose_name = 'Offre d\'emploi'
        verbose_name_plural = 'Offres d\'emploi'
        ordering = ['-date_publication']
    
    def __str__(self):
        return f"{self.reference_offre} - {self.intitule_poste}"


class Candidature(models.Model):
    """Candidatures"""
    STATUTS = (
        ('recue', 'Reçue'),
        ('preselectionne', 'Présélectionnée'),
        ('entretien', 'Entretien'),
        ('retenue', 'Retenue'),
        ('rejetee', 'Rejetée'),
    )
    
    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name='candidatures')
    numero_candidature = models.CharField(max_length=50, unique=True)
    civilite = models.CharField(max_length=10, blank=True, null=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=200)
    date_naissance = models.DateField(blank=True, null=True)
    nationalite = models.CharField(max_length=50, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    formation_niveau = models.CharField(max_length=100, blank=True, null=True)
    experience_annees = models.IntegerField(blank=True, null=True)
    date_candidature = models.DateField(auto_now_add=True)
    cv_fichier = models.FileField(upload_to='candidatures/cv/', blank=True, null=True)
    lettre_motivation = models.FileField(upload_to='candidatures/lettres/', blank=True, null=True)
    statut_candidature = models.CharField(max_length=20, choices=STATUTS, default='recue')
    score_evaluation = models.IntegerField(blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)
    date_entretien = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'candidatures'
        verbose_name = 'Candidature'
        verbose_name_plural = 'Candidatures'
        ordering = ['-date_candidature']
    
    def __str__(self):
        return f"{self.numero_candidature} - {self.nom} {self.prenoms}"


class EntretienRecrutement(models.Model):
    """Entretiens de recrutement"""
    TYPES = (
        ('telephonique', 'Téléphonique'),
        ('presentiel', 'Présentiel'),
        ('visio', 'Visioconférence'),
        ('technique', 'Technique'),
        ('rh', 'RH'),
    )
    
    DECISIONS = (
        ('favorable', 'Favorable'),
        ('defavorable', 'Défavorable'),
        ('a_revoir', 'À revoir'),
    )
    
    candidature = models.ForeignKey(Candidature, on_delete=models.CASCADE, related_name='entretiens')
    type_entretien = models.CharField(max_length=50, choices=TYPES)
    date_entretien = models.DateTimeField()
    lieu_entretien = models.CharField(max_length=200, blank=True, null=True)
    intervieweurs = models.TextField(blank=True, null=True)
    duree_minutes = models.IntegerField(blank=True, null=True)
    evaluation_technique = models.IntegerField(blank=True, null=True)
    evaluation_comportementale = models.IntegerField(blank=True, null=True)
    evaluation_motivation = models.IntegerField(blank=True, null=True)
    note_globale = models.IntegerField(blank=True, null=True)
    decision = models.CharField(max_length=50, choices=DECISIONS, blank=True, null=True)
    commentaires = models.TextField(blank=True, null=True)
    recommandations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'entretiens_recrutement'
        verbose_name = 'Entretien de recrutement'
        verbose_name_plural = 'Entretiens de recrutement'
        ordering = ['-date_entretien']
    
    def __str__(self):
        return f"{self.candidature.nom} {self.candidature.prenoms} - {self.get_type_entretien_display()}"
