from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from employes.models import Employe
from core.models import Utilisateur


class PeriodePaie(models.Model):
    """Périodes de paie"""
    STATUTS = (
        ('ouverte', 'Ouverte'),
        ('calculee', 'Calculée'),
        ('validee', 'Validée'),
        ('cloturee', 'Clôturée'),
        ('payee', 'Payée'),
    )
    
    annee = models.IntegerField()
    mois = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    libelle = models.CharField(max_length=50, blank=True, null=True)
    date_debut = models.DateField()
    date_fin = models.DateField()
    date_paiement = models.DateField(blank=True, null=True)
    statut_periode = models.CharField(max_length=20, choices=STATUTS, default='ouverte')
    nombre_jours_travailles = models.IntegerField(default=22)
    nombre_heures_mois = models.DecimalField(max_digits=6, decimal_places=2, default=173.33)
    date_cloture = models.DateTimeField(blank=True, null=True)
    utilisateur_cloture = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='periodes_cloturees')
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'periodes_paie'
        verbose_name = 'Période de paie'
        verbose_name_plural = 'Périodes de paie'
        unique_together = ['annee', 'mois']
        ordering = ['-annee', '-mois']
    
    def __str__(self):
        mois_fr = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                   'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        mois_nom = mois_fr[self.mois] if 1 <= self.mois <= 12 else str(self.mois)
        return f"{mois_nom} {self.annee}"


class RubriquePaie(models.Model):
    """Rubriques de paie"""
    TYPES = (
        ('gain', 'Gain'),
        ('retenue', 'Retenue'),
        ('cotisation', 'Cotisation'),
        ('information', 'Information'),
    )
    
    code_rubrique = models.CharField(max_length=20, unique=True)
    libelle_rubrique = models.CharField(max_length=200)
    type_rubrique = models.CharField(max_length=20, choices=TYPES)
    formule_calcul = models.TextField(blank=True, null=True)
    taux_rubrique = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    montant_fixe = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    soumis_cnss = models.BooleanField(default=False)
    soumis_irg = models.BooleanField(default=False)
    ordre_calcul = models.IntegerField(default=100)
    ordre_affichage = models.IntegerField(default=100)
    affichage_bulletin = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'rubriques_paie'
        verbose_name = 'Rubrique de paie'
        verbose_name_plural = 'Rubriques de paie'
        ordering = ['ordre_calcul']
    
    def __str__(self):
        return f"{self.code_rubrique} - {self.libelle_rubrique}"


class BulletinPaie(models.Model):
    """Bulletins de paie"""
    STATUTS = (
        ('brouillon', 'Brouillon'),
        ('calcule', 'Calculé'),
        ('valide', 'Validé'),
        ('paye', 'Payé'),
    )
    
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='bulletins')
    periode = models.ForeignKey(PeriodePaie, on_delete=models.CASCADE, related_name='bulletins')
    numero_bulletin = models.CharField(max_length=50, unique=True)
    mois_paie = models.IntegerField()
    annee_paie = models.IntegerField()
    
    # Montants
    salaire_brut = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cnss_employe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    irg = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_a_payer = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cnss_employeur = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    statut_bulletin = models.CharField(max_length=20, choices=STATUTS, default='brouillon')
    date_calcul = models.DateTimeField(blank=True, null=True)
    observations = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'bulletins_paie'
        verbose_name = 'Bulletin de paie'
        verbose_name_plural = 'Bulletins de paie'
        unique_together = ['employe', 'periode']
        ordering = ['-annee_paie', '-mois_paie']
    
    def __str__(self):
        return f"{self.numero_bulletin} - {self.employe.nom} {self.employe.prenoms}"


class ParametrePaie(models.Model):
    """Paramètres généraux de la paie"""
    TYPES_BULLETIN = (
        ('standard', 'Standard'),
        ('simplifie', 'Simplifié'),
        ('detaille', 'Détaillé'),
    )
    
    TYPES_PAIEMENT = (
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('espece', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
    )
    
    # Période en cours
    mois_en_cours = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    annee_en_cours = models.IntegerField()
    date_debut_periode = models.DateField()
    date_fin_periode = models.DateField()
    
    # Paramètres de calcul
    regulation_active = models.BooleanField(default=True, help_text="Activer la régulation automatique")
    plafond_abattement_irg = models.DecimalField(max_digits=15, decimal_places=2, default=300000, help_text="Plafond abattement IRG en GNF")
    taux_abattement_irg = models.DecimalField(max_digits=5, decimal_places=2, default=20.00, help_text="Taux d'abattement IRG en %")
    
    # Configuration
    type_bulletin_defaut = models.CharField(max_length=20, choices=TYPES_BULLETIN, default='standard')
    type_paiement_defaut = models.CharField(max_length=20, choices=TYPES_PAIEMENT, default='virement')
    nombre_max_rubriques = models.IntegerField(default=100)
    
    # Acomptes
    acompte_regulier_actif = models.BooleanField(default=True)
    acompte_exceptionnel_actif = models.BooleanField(default=True)
    montant_max_acompte_pct = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="% max du salaire")
    
    # Devise
    devise = models.CharField(max_length=3, default='GNF')
    
    # Suppression automatique
    suppression_auto_non_presents = models.BooleanField(default=False, help_text="Supprimer les salariés non présents en clôture annuelle")
    
    # Gestion historique
    conserver_historique_admin = models.BooleanField(default=True)
    duree_conservation_mois = models.IntegerField(default=120, help_text="Durée de conservation en mois")
    
    # Coordonnées société (pour bulletins)
    nom_societe = models.CharField(max_length=200, blank=True)
    adresse_societe = models.TextField(blank=True)
    telephone_societe = models.CharField(max_length=20, blank=True)
    email_societe = models.CharField(max_length=100, blank=True)
    nif_societe = models.CharField(max_length=50, blank=True, help_text="Numéro d'Identification Fiscale")
    num_cnss_employeur = models.CharField(max_length=50, blank=True)
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    utilisateur_modification = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'parametres_paie'
        verbose_name = 'Paramètre de paie'
        verbose_name_plural = 'Paramètres de paie'
    
    def __str__(self):
        return f"Paramètres Paie {self.mois_en_cours}/{self.annee_en_cours}"


class Constante(models.Model):
    """Constantes de calcul de paie"""
    TYPES_VALEUR = (
        ('montant', 'Montant'),
        ('pourcentage', 'Pourcentage'),
        ('nombre', 'Nombre'),
    )
    
    CATEGORIES = (
        ('cnss', 'CNSS'),
        ('irg', 'IRG'),
        ('inam', 'INAM'),
        ('general', 'Général'),
        ('temps', 'Temps de travail'),
    )
    
    code = models.CharField(max_length=20, unique=True, help_text="Code mémo de la constante")
    libelle = models.CharField(max_length=200)
    valeur = models.DecimalField(max_digits=15, decimal_places=4)
    type_valeur = models.CharField(max_length=20, choices=TYPES_VALEUR)
    categorie = models.CharField(max_length=50, choices=CATEGORIES, default='general')
    unite = models.CharField(max_length=20, blank=True, help_text="%, GNF, jours, heures")
    
    date_debut_validite = models.DateField()
    date_fin_validite = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'constantes'
        verbose_name = 'Constante'
        verbose_name_plural = 'Constantes'
        ordering = ['categorie', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.libelle} ({self.valeur} {self.unite})"


class TrancheIRG(models.Model):
    """Tranches du barème IRG"""
    numero_tranche = models.IntegerField()
    borne_inferieure = models.DecimalField(max_digits=15, decimal_places=2)
    borne_superieure = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Null = illimité")
    taux_irg = models.DecimalField(max_digits=5, decimal_places=2, help_text="Taux en %")
    annee_validite = models.IntegerField()
    date_debut_validite = models.DateField()
    date_fin_validite = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tranches_irg'
        verbose_name = 'Tranche IRG'
        verbose_name_plural = 'Tranches IRG'
        ordering = ['annee_validite', 'numero_tranche']
    
    def __str__(self):
        if self.borne_superieure:
            return f"Tranche {self.numero_tranche}: {self.borne_inferieure:,.0f} - {self.borne_superieure:,.0f} GNF ({self.taux_irg}%)"
        return f"Tranche {self.numero_tranche}: > {self.borne_inferieure:,.0f} GNF ({self.taux_irg}%)"


class Variable(models.Model):
    """Variables de paie"""
    TYPES_VARIABLE = (
        ('numerique', 'Numérique'),
        ('texte', 'Texte'),
        ('booleen', 'Booléen'),
        ('date', 'Date'),
    )
    
    PORTEES = (
        ('global', 'Global'),
        ('employe', 'Par employé'),
        ('periode', 'Par période'),
    )
    
    code = models.CharField(max_length=20, unique=True, help_text="Code mémo de la variable")
    libelle = models.CharField(max_length=100)
    type_variable = models.CharField(max_length=20, choices=TYPES_VARIABLE)
    portee = models.CharField(max_length=20, choices=PORTEES)
    valeur_defaut = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'variables'
        verbose_name = 'Variable'
        verbose_name_plural = 'Variables'
        ordering = ['portee', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.libelle}"


class ElementSalaire(models.Model):
    """Éléments de salaire fixes par employé"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='elements_salaire')
    rubrique = models.ForeignKey(RubriquePaie, on_delete=models.CASCADE, related_name='elements_employes')
    
    # Montant ou taux
    montant = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Montant fixe")
    taux = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Taux en %")
    
    # Base de calcul (si taux)
    base_calcul = models.CharField(max_length=50, blank=True, help_text="Ex: SALAIRE_BASE, BRUT, etc.")
    
    # Validité
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    # Récurrence
    recurrent = models.BooleanField(default=True, help_text="Appliqué chaque mois")
    
    class Meta:
        db_table = 'elements_salaire'
        verbose_name = 'Élément de salaire'
        verbose_name_plural = 'Éléments de salaire'
        ordering = ['employe', 'rubrique__ordre_calcul']
    
    def __str__(self):
        if self.montant:
            return f"{self.employe.matricule} - {self.rubrique.code_rubrique}: {self.montant:,.0f} GNF"
        elif self.taux:
            return f"{self.employe.matricule} - {self.rubrique.code_rubrique}: {self.taux}%"
        return f"{self.employe.matricule} - {self.rubrique.code_rubrique}"


class LigneBulletin(models.Model):
    """Lignes de détail d'un bulletin de paie"""
    bulletin = models.ForeignKey(BulletinPaie, on_delete=models.CASCADE, related_name='lignes')
    rubrique = models.ForeignKey(RubriquePaie, on_delete=models.CASCADE)
    
    # Calcul
    base = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Base de calcul")
    taux = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Taux appliqué")
    nombre = models.DecimalField(max_digits=10, decimal_places=2, default=1, help_text="Quantité (heures, jours, etc.)")
    montant = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Montant calculé")
    
    # Ordre d'affichage
    ordre = models.IntegerField(default=100)
    
    # Informations complémentaires
    libelle_personnalise = models.CharField(max_length=200, blank=True, help_text="Libellé spécifique pour ce bulletin")
    commentaire = models.CharField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'lignes_bulletin'
        verbose_name = 'Ligne de bulletin'
        verbose_name_plural = 'Lignes de bulletin'
        ordering = ['bulletin', 'ordre']
    
    def __str__(self):
        return f"{self.bulletin.numero_bulletin} - {self.rubrique.code_rubrique}: {self.montant:,.0f}"


class CumulPaie(models.Model):
    """Cumuls de paie par employé et par année"""
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='cumuls_paie')
    annee = models.IntegerField()
    
    # Cumuls bruts
    cumul_brut = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumul_imposable = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumul_net = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cumuls cotisations
    cumul_cnss_employe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumul_cnss_employeur = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cumul_irg = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Cumuls par rubrique (JSON pour flexibilité)
    cumuls_rubriques = models.JSONField(default=dict, blank=True, help_text="Cumuls détaillés par rubrique")
    
    # Nombre de bulletins
    nombre_bulletins = models.IntegerField(default=0)
    
    # Dates de mise à jour
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cumuls_paie'
        verbose_name = 'Cumul de paie'
        verbose_name_plural = 'Cumuls de paie'
        unique_together = ['employe', 'annee']
        ordering = ['-annee', 'employe']
    
    def __str__(self):
        return f"{self.employe.matricule} - {self.annee}: {self.cumul_net:,.0f} GNF"


class HistoriquePaie(models.Model):
    """Historique des modifications de paie"""
    TYPES_ACTION = (
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('validation', 'Validation'),
        ('cloture', 'Clôture'),
        ('recalcul', 'Recalcul'),
    )
    
    bulletin = models.ForeignKey(BulletinPaie, on_delete=models.CASCADE, related_name='historique', null=True, blank=True)
    periode = models.ForeignKey(PeriodePaie, on_delete=models.CASCADE, related_name='historique', null=True, blank=True)
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, related_name='historique_paie', null=True, blank=True)
    
    type_action = models.CharField(max_length=20, choices=TYPES_ACTION)
    description = models.TextField()
    
    # Valeurs avant/après (JSON)
    valeurs_avant = models.JSONField(null=True, blank=True)
    valeurs_apres = models.JSONField(null=True, blank=True)
    
    # Utilisateur et date
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date_action = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'historique_paie'
        verbose_name = 'Historique de paie'
        verbose_name_plural = 'Historiques de paie'
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.type_action} - {self.date_action.strftime('%d/%m/%Y %H:%M')}"
