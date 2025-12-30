from django.db import models
from core.models import Poste, Service, Entreprise
from employes.models import Employe


class OffreEmploi(models.Model):
    """Offres d'emploi"""
    STATUTS = (
        ('ouverte', 'Ouverte'),
        ('fermee', 'Fermée'),
        ('pourvue', 'Pourvue'),
        ('annulee', 'Annulée'),
    )
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='offres_emploi', null=True, blank=True)
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
    image = models.ImageField(upload_to='offres_emploi/', blank=True, null=True, help_text="Image de présentation de l'offre")
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
        ('embauche', 'Embauché'),
    )
    
    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name='candidatures')
    employe_cree = models.OneToOneField(Employe, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidature_origine', help_text="Employé créé suite à l'embauche")
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
    cv_fichier = models.FileField(upload_to='candidatures/cv/', blank=True, null=True, help_text="CV au format PDF")
    lettre_motivation = models.FileField(upload_to='candidatures/lettres/', blank=True, null=True, help_text="Lettre de motivation")
    autres_documents = models.FileField(upload_to='candidatures/autres/', blank=True, null=True, help_text="Autres documents (diplômes, certificats, etc.)")
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


class TestRecrutement(models.Model):
    """Tests de recrutement"""
    TYPES_TEST = (
        ('technique', 'Test technique'),
        ('psychotechnique', 'Test psychotechnique'),
        ('personnalite', 'Test de personnalité'),
        ('langue', 'Test de langue'),
        ('pratique', 'Test pratique'),
        ('cas_etude', 'Étude de cas'),
    )
    RESULTATS = (
        ('reussi', 'Réussi'),
        ('echoue', 'Échoué'),
        ('en_attente', 'En attente'),
    )
    
    candidature = models.ForeignKey(Candidature, on_delete=models.CASCADE, related_name='tests')
    type_test = models.CharField(max_length=30, choices=TYPES_TEST)
    intitule = models.CharField(max_length=200)
    date_test = models.DateTimeField()
    duree_minutes = models.IntegerField(null=True, blank=True)
    
    score_obtenu = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_max = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    seuil_reussite = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    
    resultat = models.CharField(max_length=20, choices=RESULTATS, default='en_attente')
    evaluateur = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True)
    commentaires = models.TextField(blank=True, null=True)
    fichier_test = models.FileField(upload_to='recrutement/tests/', blank=True, null=True)
    
    class Meta:
        db_table = 'tests_recrutement'
        verbose_name = 'Test de recrutement'
        verbose_name_plural = 'Tests de recrutement'
        ordering = ['-date_test']
    
    def __str__(self):
        return f"{self.candidature.nom} - {self.get_type_test_display()}"


class DecisionEmbauche(models.Model):
    """Décision d'embauche"""
    DECISIONS = (
        ('embauche', 'Embauche validée'),
        ('refus', 'Refus'),
        ('attente', 'En attente'),
        ('reserve', 'Mise en réserve'),
    )
    
    candidature = models.OneToOneField(Candidature, on_delete=models.CASCADE, related_name='decision_embauche')
    decision = models.CharField(max_length=20, choices=DECISIONS)
    date_decision = models.DateField()
    
    # Conditions d'embauche
    poste_propose = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, blank=True)
    service_affectation = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    type_contrat = models.CharField(max_length=20, blank=True, null=True)
    date_embauche_prevue = models.DateField(null=True, blank=True)
    salaire_propose = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Documents pré-embauche
    casier_judiciaire = models.BooleanField(default=False, help_text="Casier judiciaire fourni")
    certificat_medical = models.BooleanField(default=False, help_text="Certificat médical fourni")
    diplomes_verifies = models.BooleanField(default=False, help_text="Diplômes vérifiés")
    references_verifiees = models.BooleanField(default=False, help_text="Références vérifiées")
    
    # Validation
    valide_par = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, related_name='embauches_validees')
    motif_refus = models.TextField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'decisions_embauche'
        verbose_name = 'Décision d\'embauche'
        verbose_name_plural = 'Décisions d\'embauche'
        ordering = ['-date_decision']
    
    def __str__(self):
        return f"{self.candidature.nom} {self.candidature.prenoms} - {self.get_decision_display()}"


class CanalDiffusion(models.Model):
    """Canaux de diffusion des offres d'emploi"""
    TYPES_CANAL = (
        ('site_web', 'Site web entreprise'),
        ('linkedin', 'LinkedIn'),
        ('jobboard', 'Site d\'emploi'),
        ('presse', 'Presse'),
        ('agence', 'Agence de recrutement'),
        ('cooptation', 'Cooptation'),
        ('ecole', 'École/Université'),
        ('autre', 'Autre'),
    )
    
    offre = models.ForeignKey(OffreEmploi, on_delete=models.CASCADE, related_name='canaux_diffusion')
    type_canal = models.CharField(max_length=30, choices=TYPES_CANAL)
    nom_canal = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True)
    date_publication = models.DateField()
    date_retrait = models.DateField(null=True, blank=True)
    cout = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    nb_candidatures_recues = models.IntegerField(default=0)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'canaux_diffusion'
        verbose_name = 'Canal de diffusion'
        verbose_name_plural = 'Canaux de diffusion'
    
    def __str__(self):
        return f"{self.offre.reference_offre} - {self.nom_canal}"
