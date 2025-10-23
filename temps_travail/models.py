from django.db import models
from django.core.validators import MinValueValidator
from employes.models import Employe


class JourFerie(models.Model):
    """Jours fériés"""
    TYPES = (
        ('national', 'National'),
        ('religieux', 'Religieux'),
        ('local', 'Local'),
    )
    
    libelle = models.CharField(max_length=100)
    date_jour_ferie = models.DateField()
    annee = models.IntegerField()
    type_ferie = models.CharField(max_length=50, choices=TYPES)
    recurrent = models.BooleanField(default=False)
    jour_recuperation = models.DateField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'calendrier_jours_feries'
        verbose_name = 'Jour férié'
        verbose_name_plural = 'Jours fériés'
        ordering = ['date_jour_ferie']
    
    def __str__(self):
        return f"{self.libelle} - {self.date_jour_ferie}"


class Conge(models.Model):
    """Congés des employés"""
    TYPES = (
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('maternite', 'Congé maternité'),
        ('paternite', 'Congé paternité'),
        ('sans_solde', 'Congé sans solde'),
    )
    
    STATUTS = (
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='conges')
    type_conge = models.CharField(max_length=50, choices=TYPES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    nombre_jours = models.IntegerField(validators=[MinValueValidator(1)])
    annee_reference = models.IntegerField(blank=True, null=True)
    motif = models.TextField(blank=True, null=True)
    justificatif = models.FileField(upload_to='conges/', blank=True, null=True)
    statut_demande = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    date_demande = models.DateField(auto_now_add=True)
    approbateur = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, related_name='conges_approuves')
    date_approbation = models.DateField(blank=True, null=True)
    commentaire_approbateur = models.TextField(blank=True, null=True)
    remplacant = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True, blank=True, related_name='remplacements')
    
    class Meta:
        db_table = 'conges'
        verbose_name = 'Congé'
        verbose_name_plural = 'Congés'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.get_type_conge_display()} ({self.date_debut})"


class SoldeConge(models.Model):
    """Soldes de congés"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='soldes_conges')
    annee = models.IntegerField()
    conges_acquis = models.DecimalField(max_digits=5, decimal_places=2, default=26.00)
    conges_pris = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    conges_restants = models.DecimalField(max_digits=5, decimal_places=2, default=26.00)
    conges_reports = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    date_mise_a_jour = models.DateField(auto_now=True)
    
    class Meta:
        db_table = 'soldes_conges'
        verbose_name = 'Solde de congé'
        verbose_name_plural = 'Soldes de congés'
        unique_together = ['employe', 'annee']
        ordering = ['-annee']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.annee} ({self.conges_restants} jours)"


class Pointage(models.Model):
    """Pointages quotidiens"""
    STATUTS = (
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('retard', 'Retard'),
        ('absence_justifiee', 'Absence justifiée'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='pointages')
    date_pointage = models.DateField()
    heure_entree = models.TimeField(blank=True, null=True)
    heure_sortie = models.TimeField(blank=True, null=True)
    heures_travaillees = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    heures_supplementaires = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, default=0)
    statut_pointage = models.CharField(max_length=20, choices=STATUTS, default='present')
    motif_absence = models.CharField(max_length=50, blank=True, null=True)
    justificatif = models.FileField(upload_to='pointages/', blank=True, null=True)
    valide = models.BooleanField(default=False)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'pointages'
        verbose_name = 'Pointage'
        verbose_name_plural = 'Pointages'
        unique_together = ['employe', 'date_pointage']
        ordering = ['-date_pointage']
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.date_pointage}"


class Absence(models.Model):
    """Absences des employés"""
    TYPES = (
        ('maladie', 'Maladie'),
        ('accident_travail', 'Accident de travail'),
        ('absence_injustifiee', 'Absence injustifiée'),
        ('permission', 'Permission'),
    )
    
    IMPACTS = (
        ('paye', 'Payé'),
        ('non_paye', 'Non payé'),
        ('partiellement_paye', 'Partiellement payé'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='absences')
    date_absence = models.DateField()
    type_absence = models.CharField(max_length=50, choices=TYPES)
    duree_jours = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    justifie = models.BooleanField(default=False)
    justificatif = models.FileField(upload_to='absences/', blank=True, null=True)
    impact_paie = models.CharField(max_length=20, choices=IMPACTS, default='paye')
    taux_maintien_salaire = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'absences'
        verbose_name = 'Absence'
        verbose_name_plural = 'Absences'
        ordering = ['-date_absence']
    
    def __str__(self):
        return f"{self.employe.nom} {self.employe.prenoms} - {self.get_type_absence_display()} ({self.date_absence})"


class ArretTravail(models.Model):
    """Arrêts de travail (maladie, accident)"""
    TYPES = (
        ('maladie', 'Maladie'),
        ('accident_travail', 'Accident de travail'),
        ('maladie_professionnelle', 'Maladie professionnelle'),
    )
    
    ORGANISMES = (
        ('inam', 'INAM'),
        ('employeur', 'Employeur'),
        ('mixte', 'Mixte'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='arrets_travail')
    type_arret = models.CharField(max_length=50, choices=TYPES)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    duree_jours = models.IntegerField(blank=True, null=True)
    medecin_prescripteur = models.CharField(max_length=100, blank=True)
    numero_certificat = models.CharField(max_length=50, blank=True)
    organisme_payeur = models.CharField(max_length=50, choices=ORGANISMES, default='inam')
    taux_indemnisation = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, help_text="% du salaire")
    montant_indemnites = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    prolongation = models.BooleanField(default=False)
    arret_initial = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='prolongations')
    fichier_certificat = models.FileField(upload_to='arrets_travail/', blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'arrets_travail'
        verbose_name = 'Arrêt de travail'
        verbose_name_plural = 'Arrêts de travail'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.employe.nom} {self.employe.prenoms} - {self.get_type_arret_display()} ({self.date_debut})"


class HoraireTravail(models.Model):
    """Horaires de travail"""
    TYPES = (
        ('normal', 'Normal'),
        ('equipe', 'Équipe'),
        ('nuit', 'Nuit'),
        ('flexible', 'Flexible'),
    )
    
    code_horaire = models.CharField(max_length=20, unique=True)
    libelle_horaire = models.CharField(max_length=100)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    heure_pause_debut = models.TimeField(blank=True, null=True)
    heure_pause_fin = models.TimeField(blank=True, null=True)
    heures_jour = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    type_horaire = models.CharField(max_length=20, choices=TYPES, default='normal')
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'horaires_travail'
        verbose_name = 'Horaire de travail'
        verbose_name_plural = 'Horaires de travail'
        ordering = ['code_horaire']
    
    def __str__(self):
        return f"{self.code_horaire} - {self.libelle_horaire} ({self.heure_debut}-{self.heure_fin})"


class AffectationHoraire(models.Model):
    """Affectation des horaires aux employés"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='affectations_horaires')
    horaire = models.ForeignKey(HoraireTravail, on_delete=models.CASCADE, related_name='affectations')
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'affectation_horaires'
        verbose_name = 'Affectation horaire'
        verbose_name_plural = 'Affectations horaires'
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.employe.nom} {self.employe.prenoms} - {self.horaire.libelle_horaire}"
