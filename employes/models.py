from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from core.models import Etablissement, Service, Poste
from django.utils import timezone


class Employe(models.Model):
    """Modèle principal des employés"""
    CIVILITES = (
        ('M.', 'Monsieur'),
        ('Mme', 'Madame'),
        ('Mlle', 'Mademoiselle'),
    )
    
    SEXES = (
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    )
    
    SITUATIONS_MATRIMONIALES = (
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf(ve)'),
    )
    
    TYPES_PIECES = (
        ('CNI', 'Carte Nationale d\'Identité'),
        ('passeport', 'Passeport'),
    )
    
    TYPES_CONTRATS = (
        ('CDI', 'Contrat à Durée Indéterminée'),
        ('CDD', 'Contrat à Durée Déterminée'),
        ('stage', 'Stage'),
        ('temporaire', 'Temporaire'),
    )
    
    STATUTS = (
        ('actif', 'Actif'),
        ('suspendu', 'Suspendu'),
        ('demissionnaire', 'Démissionnaire'),
        ('licencie', 'Licencié'),
        ('retraite', 'Retraité'),
    )
    
    MODES_PAIEMENT = (
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
    )
    
    # Identification
    matricule = models.CharField(max_length=20, unique=True)
    
    # État civil
    civilite = models.CharField(max_length=10, choices=CIVILITES, blank=True, null=True)
    nom = models.CharField(max_length=100)
    prenoms = models.CharField(max_length=200)
    nom_jeune_fille = models.CharField(max_length=100, blank=True, null=True)
    sexe = models.CharField(max_length=1, choices=SEXES)
    situation_matrimoniale = models.CharField(max_length=20, choices=SITUATIONS_MATRIMONIALES, blank=True, null=True)
    nombre_enfants = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    photo = models.ImageField(upload_to='employes/photos/', blank=True, null=True)
    
    # Naissance
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100, blank=True, null=True)
    commune_naissance = models.CharField(max_length=100, blank=True, null=True)
    prefecture_naissance = models.CharField(max_length=100, blank=True, null=True)
    departement = models.CharField(max_length=100, blank=True, null=True)
    nationalite = models.CharField(max_length=50, default='Guinéenne')
    
    # Pièce d'identité
    type_piece_identite = models.CharField(max_length=20, choices=TYPES_PIECES, blank=True, null=True)
    numero_piece_identite = models.CharField(max_length=50, blank=True, null=True)
    date_delivrance_piece = models.DateField(blank=True, null=True)
    date_expiration_piece = models.DateField(blank=True, null=True)
    num_cnss_individuel = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='N° CNSS')
    
    # Contact
    adresse_actuelle = models.TextField(blank=True, null=True)
    commune_residence = models.CharField(max_length=100, blank=True, null=True)
    prefecture_residence = models.CharField(max_length=100, blank=True, null=True)
    telephone_principal = models.CharField(max_length=20, blank=True, null=True)
    telephone_secondaire = models.CharField(max_length=20, blank=True, null=True)
    email_personnel = models.EmailField(blank=True, null=True)
    email_professionnel = models.EmailField(blank=True, null=True)
    
    # Contact d'urgence
    contact_urgence_nom = models.CharField(max_length=100, blank=True, null=True)
    contact_urgence_lien = models.CharField(max_length=50, blank=True, null=True)
    contact_urgence_telephone = models.CharField(max_length=20, blank=True, null=True)
    
    # Informations professionnelles
    etablissement = models.ForeignKey(Etablissement, on_delete=models.SET_NULL, null=True, related_name='employes')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='employes')
    poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, related_name='employes')
    date_embauche = models.DateField()
    date_anciennete = models.DateField(blank=True, null=True)
    type_contrat = models.CharField(max_length=20, choices=TYPES_CONTRATS)
    date_debut_contrat = models.DateField(blank=True, null=True)
    date_fin_contrat = models.DateField(blank=True, null=True)
    num_contrat = models.CharField(max_length=50, blank=True, null=True)
    statut_employe = models.CharField(max_length=20, choices=STATUTS, default='actif')
    date_depart = models.DateField(blank=True, null=True)
    motif_depart = models.CharField(max_length=50, blank=True, null=True)
    superieur_hierarchique = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordonnes')
    
    # Informations bancaires
    mode_paiement = models.CharField(max_length=20, choices=MODES_PAIEMENT, default='virement')
    nom_banque = models.CharField(max_length=100, blank=True, null=True)
    agence_banque = models.CharField(max_length=100, blank=True, null=True)
    numero_compte = models.CharField(max_length=50, blank=True, null=True)
    rib = models.CharField(max_length=50, blank=True, null=True, verbose_name='RIB')
    operateur_mobile_money = models.CharField(max_length=50, blank=True, null=True)
    numero_mobile_money = models.CharField(max_length=20, blank=True, null=True)
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    utilisateur_creation = models.ForeignKey('core.Utilisateur', on_delete=models.SET_NULL, null=True, related_name='employes_crees')
    utilisateur_modification = models.ForeignKey('core.Utilisateur', on_delete=models.SET_NULL, null=True, related_name='employes_modifies')
    
    class Meta:
        db_table = 'employes'
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'
        ordering = ['matricule']
    
    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenoms}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenoms}"
    
    @property
    def age(self):
        if self.date_naissance:
            today = timezone.now().date()
            return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
        return None
    
    @property
    def anciennete_annees(self):
        if self.date_embauche:
            today = timezone.now().date()
            return today.year - self.date_embauche.year
        return None


class ContratEmploye(models.Model):
    """Contrats des employés"""
    STATUTS = (
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('rompu', 'Rompu'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='contrats')
    num_contrat = models.CharField(max_length=50, unique=True)
    type_contrat = models.CharField(max_length=20, choices=Employe.TYPES_CONTRATS)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    duree_mois = models.IntegerField(blank=True, null=True)
    motif_contrat = models.TextField(blank=True, null=True)
    periode_essai_mois = models.IntegerField(blank=True, null=True)
    date_fin_essai = models.DateField(blank=True, null=True)
    statut_contrat = models.CharField(max_length=20, choices=STATUTS, default='en_cours')
    renouvellements = models.IntegerField(default=0)
    fichier_contrat = models.FileField(upload_to='contrats/', blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    date_signature = models.DateField(blank=True, null=True)
    
    class Meta:
        db_table = 'contrats_employes'
        verbose_name = 'Contrat employé'
        verbose_name_plural = 'Contrats employés'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.num_contrat} - {self.employe.nom_complet}"


class FormationEmploye(models.Model):
    """Formations des employés"""
    TYPES_FORMATION = (
        ('initiale', 'Formation initiale'),
        ('continue', 'Formation continue'),
        ('certification', 'Certification'),
    )
    
    RESULTATS = (
        ('acquis', 'Acquis'),
        ('non_acquis', 'Non acquis'),
        ('en_cours', 'En cours'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='formations')
    type_formation = models.CharField(max_length=50, choices=TYPES_FORMATION)
    intitule_formation = models.CharField(max_length=200)
    organisme_formation = models.CharField(max_length=200, blank=True, null=True)
    diplome_obtenu = models.CharField(max_length=100, blank=True, null=True)
    niveau = models.CharField(max_length=50, blank=True, null=True)
    specialite = models.CharField(max_length=100, blank=True, null=True)
    date_debut = models.DateField(blank=True, null=True)
    date_fin = models.DateField(blank=True, null=True)
    duree_heures = models.IntegerField(blank=True, null=True)
    cout_formation = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    lieu_formation = models.CharField(max_length=100, blank=True, null=True)
    resultat = models.CharField(max_length=50, choices=RESULTATS, blank=True, null=True)
    fichier_attestation = models.FileField(upload_to='formations/', blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'formations_employes'
        verbose_name = 'Formation employé'
        verbose_name_plural = 'Formations employés'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.intitule_formation}"


class CarriereEmploye(models.Model):
    """Mouvements de carrière"""
    TYPES_MOUVEMENT = (
        ('promotion', 'Promotion'),
        ('mutation', 'Mutation'),
        ('reclassement', 'Reclassement'),
        ('detachement', 'Détachement'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='carrieres')
    type_mouvement = models.CharField(max_length=50, choices=TYPES_MOUVEMENT)
    date_mouvement = models.DateField()
    ancien_poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, related_name='anciens_employes')
    nouveau_poste = models.ForeignKey(Poste, on_delete=models.SET_NULL, null=True, related_name='nouveaux_employes')
    ancien_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='anciens_employes')
    nouveau_service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='nouveaux_employes')
    ancien_etablissement = models.ForeignKey(Etablissement, on_delete=models.SET_NULL, null=True, related_name='anciens_employes')
    nouveau_etablissement = models.ForeignKey(Etablissement, on_delete=models.SET_NULL, null=True, related_name='nouveaux_employes')
    ancienne_categorie = models.CharField(max_length=50, blank=True, null=True)
    nouvelle_categorie = models.CharField(max_length=50, blank=True, null=True)
    ancienne_classification = models.CharField(max_length=10, blank=True, null=True)
    nouvelle_classification = models.CharField(max_length=10, blank=True, null=True)
    ancien_salaire = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    nouveau_salaire = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    motif = models.TextField(blank=True, null=True)
    decision_reference = models.CharField(max_length=100, blank=True, null=True)
    date_decision = models.DateField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'carrieres_employes'
        verbose_name = 'Carrière employé'
        verbose_name_plural = 'Carrières employés'
        ordering = ['-date_mouvement']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.get_type_mouvement_display()} - {self.date_mouvement}"


class EvaluationEmploye(models.Model):
    """Évaluations des employés"""
    PERIODES = (
        ('annuelle', 'Annuelle'),
        ('semestrielle', 'Semestrielle'),
    )
    
    APPRECIATIONS = (
        ('excellent', 'Excellent'),
        ('bien', 'Bien'),
        ('satisfaisant', 'Satisfaisant'),
        ('insuffisant', 'Insuffisant'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='evaluations')
    annee_evaluation = models.IntegerField()
    periode = models.CharField(max_length=20, choices=PERIODES)
    date_evaluation = models.DateField()
    evaluateur = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, related_name='evaluations_effectuees')
    objectifs_atteints = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    competences_techniques = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    competences_comportementales = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    note_globale = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    appreciation = models.CharField(max_length=20, choices=APPRECIATIONS, blank=True, null=True)
    points_forts = models.TextField(blank=True, null=True)
    points_amelioration = models.TextField(blank=True, null=True)
    plan_developpement = models.TextField(blank=True, null=True)
    recommandations = models.TextField(blank=True, null=True)
    date_prochain_entretien = models.DateField(blank=True, null=True)
    
    class Meta:
        db_table = 'evaluations_employes'
        verbose_name = 'Évaluation employé'
        verbose_name_plural = 'Évaluations employés'
        ordering = ['-date_evaluation']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.annee_evaluation} - {self.get_periode_display()}"


class DocumentEmploye(models.Model):
    """Documents des employés"""
    TYPES_DOCUMENT = (
        ('cv', 'CV'),
        ('diplome', 'Diplôme'),
        ('attestation', 'Attestation'),
        ('certificat', 'Certificat'),
        ('piece_identite', 'Pièce d\'identité'),
        ('acte_naissance', 'Acte de naissance'),
        ('certificat_medical', 'Certificat médical'),
        ('contrat', 'Contrat de travail'),
        ('avenant', 'Avenant au contrat'),
        ('attestation_travail', 'Attestation de travail'),
        ('fiche_paie', 'Fiche de paie'),
        ('photo', 'Photo d\'identité'),
        ('autre', 'Autre document'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='documents')
    type_document = models.CharField(max_length=50, choices=TYPES_DOCUMENT)
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    fichier = models.FileField(upload_to='documents_employes/')
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_document = models.DateField(blank=True, null=True, help_text="Date du document")
    date_expiration = models.DateField(blank=True, null=True, help_text="Date d'expiration si applicable")
    taille_fichier = models.IntegerField(blank=True, null=True, help_text="Taille en octets")
    ajoute_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    confidentiel = models.BooleanField(default=False)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'documents_employes'
        verbose_name = 'Document employé'
        verbose_name_plural = 'Documents employés'
        ordering = ['-date_ajout']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.get_type_document_display()} - {self.titre}"
    
    def get_extension(self):
        """Retourne l'extension du fichier"""
        import os
        return os.path.splitext(self.fichier.name)[1].lower()
    
    def get_icon(self):
        """Retourne l'icône Bootstrap selon le type de fichier"""
        ext = self.get_extension()
        icons = {
            '.pdf': 'bi-file-pdf text-danger',
            '.doc': 'bi-file-word text-primary',
            '.docx': 'bi-file-word text-primary',
            '.xls': 'bi-file-excel text-success',
            '.xlsx': 'bi-file-excel text-success',
            '.jpg': 'bi-file-image text-info',
            '.jpeg': 'bi-file-image text-info',
            '.png': 'bi-file-image text-info',
            '.zip': 'bi-file-zip text-warning',
            '.rar': 'bi-file-zip text-warning',
        }
        return icons.get(ext, 'bi-file-earmark text-secondary')
    
    def get_taille_lisible(self):
        """Retourne la taille du fichier en format lisible"""
        if not self.taille_fichier:
            return "N/A"
        
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if self.taille_fichier < 1024.0:
                return f"{self.taille_fichier:.1f} {unit}"
            self.taille_fichier /= 1024.0
        return f"{self.taille_fichier:.1f} To"
    
    def save(self, *args, **kwargs):
        """Calculer la taille du fichier avant la sauvegarde"""
        if self.fichier and not self.taille_fichier:
            self.taille_fichier = self.fichier.size
        super().save(*args, **kwargs)
