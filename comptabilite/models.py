from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class PlanComptable(models.Model):
    """Plan comptable SYSCOHADA"""
    CLASSES = [
        ('1', 'Classe 1 - Comptes de ressources durables'),
        ('2', 'Classe 2 - Comptes d\'actif immobilisé'),
        ('3', 'Classe 3 - Comptes de stocks'),
        ('4', 'Classe 4 - Comptes de tiers'),
        ('5', 'Classe 5 - Comptes de trésorerie'),
        ('6', 'Classe 6 - Comptes de charges'),
        ('7', 'Classe 7 - Comptes de produits'),
        ('8', 'Classe 8 - Comptes des autres charges'),
        ('9', 'Classe 9 - Comptes analytiques'),
    ]
    
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='comptes_comptables')
    numero_compte = models.CharField(max_length=20, verbose_name='N° Compte')
    intitule = models.CharField(max_length=200, verbose_name='Intitulé')
    classe = models.CharField(max_length=1, choices=CLASSES)
    compte_parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_comptes')
    est_actif = models.BooleanField(default=True)
    solde_debiteur = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    solde_crediteur = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'plan_comptable'
        verbose_name = 'Compte comptable'
        verbose_name_plural = 'Plan comptable'
        unique_together = ['entreprise', 'numero_compte']
        ordering = ['numero_compte']
    
    def __str__(self):
        return f"{self.numero_compte} - {self.intitule}"
    
    @property
    def solde(self):
        return self.solde_debiteur - self.solde_crediteur


class Journal(models.Model):
    """Journaux comptables"""
    TYPES_JOURNAL = [
        ('AC', 'Achats'),
        ('VT', 'Ventes'),
        ('BQ', 'Banque'),
        ('CA', 'Caisse'),
        ('OD', 'Opérations diverses'),
        ('AN', 'À nouveau'),
        ('SA', 'Salaires'),
    ]
    
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='journaux')
    code = models.CharField(max_length=5, verbose_name='Code journal')
    libelle = models.CharField(max_length=100, verbose_name='Libellé')
    type_journal = models.CharField(max_length=2, choices=TYPES_JOURNAL)
    compte_contrepartie = models.ForeignKey(PlanComptable, on_delete=models.SET_NULL, null=True, blank=True)
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'journaux_comptables'
        verbose_name = 'Journal'
        verbose_name_plural = 'Journaux'
        unique_together = ['entreprise', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.libelle}"


class ExerciceComptable(models.Model):
    """Exercice comptable (année fiscale)"""
    STATUTS = [
        ('ouvert', 'Ouvert'),
        ('cloture', 'Clôturé'),
    ]
    
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='exercices')
    libelle = models.CharField(max_length=100, verbose_name='Libellé')
    date_debut = models.DateField(verbose_name='Date début')
    date_fin = models.DateField(verbose_name='Date fin')
    statut = models.CharField(max_length=10, choices=STATUTS, default='ouvert')
    est_courant = models.BooleanField(default=False, verbose_name='Exercice courant')
    
    class Meta:
        db_table = 'exercices_comptables'
        verbose_name = 'Exercice comptable'
        verbose_name_plural = 'Exercices comptables'
        ordering = ['-date_debut']
    
    def __str__(self):
        return self.libelle


class PieceComptable(models.Model):
    """Pièces comptables (factures, reçus, etc.)"""
    TYPES_PIECE = [
        ('FA', 'Facture achat'),
        ('FV', 'Facture vente'),
        ('RC', 'Reçu caisse'),
        ('RB', 'Relevé banque'),
        ('OD', 'Opération diverse'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='pieces_comptables')
    numero = models.CharField(max_length=50, verbose_name='N° Pièce')
    type_piece = models.CharField(max_length=2, choices=TYPES_PIECE)
    date_piece = models.DateField(verbose_name='Date pièce')
    libelle = models.CharField(max_length=200)
    tiers = models.ForeignKey('Tiers', on_delete=models.SET_NULL, null=True, blank=True)
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    fichier = models.FileField(upload_to='pieces_comptables/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pieces_comptables'
        verbose_name = 'Pièce comptable'
        verbose_name_plural = 'Pièces comptables'
        ordering = ['-date_piece']
    
    def __str__(self):
        return f"{self.numero} - {self.libelle}"


class EcritureComptable(models.Model):
    """Écritures comptables"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='ecritures')
    exercice = models.ForeignKey(ExerciceComptable, on_delete=models.CASCADE, related_name='ecritures')
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name='ecritures')
    piece = models.ForeignKey(PieceComptable, on_delete=models.SET_NULL, null=True, blank=True, related_name='ecritures')
    numero_ecriture = models.CharField(max_length=20, verbose_name='N° Écriture')
    date_ecriture = models.DateField(verbose_name='Date écriture')
    libelle = models.CharField(max_length=200, verbose_name='Libellé')
    est_validee = models.BooleanField(default=False, verbose_name='Validée')
    date_validation = models.DateTimeField(null=True, blank=True)
    validee_par = models.ForeignKey('core.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ecritures_comptables'
        verbose_name = 'Écriture comptable'
        verbose_name_plural = 'Écritures comptables'
        ordering = ['-date_ecriture', '-numero_ecriture']
    
    def __str__(self):
        return f"{self.numero_ecriture} - {self.libelle}"
    
    @property
    def total_debit(self):
        return sum(l.montant_debit for l in self.lignes.all())
    
    @property
    def total_credit(self):
        return sum(l.montant_credit for l in self.lignes.all())
    
    @property
    def est_equilibree(self):
        return self.total_debit == self.total_credit


class LigneEcriture(models.Model):
    """Lignes d'écritures comptables"""
    ecriture = models.ForeignKey(EcritureComptable, on_delete=models.CASCADE, related_name='lignes')
    compte = models.ForeignKey(PlanComptable, on_delete=models.CASCADE, related_name='lignes_ecritures')
    libelle = models.CharField(max_length=200, blank=True)
    montant_debit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    montant_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        db_table = 'lignes_ecritures'
        verbose_name = 'Ligne d\'écriture'
        verbose_name_plural = 'Lignes d\'écritures'
    
    def __str__(self):
        return f"{self.compte.numero_compte} - D:{self.montant_debit} C:{self.montant_credit}"


class Tiers(models.Model):
    """Tiers (clients, fournisseurs)"""
    TYPES_TIERS = [
        ('client', 'Client'),
        ('fournisseur', 'Fournisseur'),
        ('mixte', 'Client et Fournisseur'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='tiers')
    code = models.CharField(max_length=20, verbose_name='Code tiers')
    raison_sociale = models.CharField(max_length=200, verbose_name='Raison sociale')
    type_tiers = models.CharField(max_length=15, choices=TYPES_TIERS)
    nif = models.CharField(max_length=50, blank=True, null=True, verbose_name='NIF')
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    compte_comptable = models.ForeignKey(PlanComptable, on_delete=models.SET_NULL, null=True, blank=True)
    plafond_credit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    solde = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tiers_comptables'
        verbose_name = 'Tiers'
        verbose_name_plural = 'Tiers'
        unique_together = ['entreprise', 'code']
        ordering = ['raison_sociale']
    
    def __str__(self):
        return f"{self.code} - {self.raison_sociale}"


class Facture(models.Model):
    """Factures clients et fournisseurs"""
    TYPES_FACTURE = [
        ('achat', 'Facture d\'achat'),
        ('vente', 'Facture de vente'),
    ]
    STATUTS = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='factures')
    numero = models.CharField(max_length=50, verbose_name='N° Facture')
    type_facture = models.CharField(max_length=10, choices=TYPES_FACTURE)
    tiers = models.ForeignKey(Tiers, on_delete=models.CASCADE, related_name='factures')
    date_facture = models.DateField(verbose_name='Date facture')
    date_echeance = models.DateField(verbose_name='Date échéance', null=True, blank=True)
    reference_externe = models.CharField(max_length=100, blank=True, null=True, verbose_name='Réf. externe')
    montant_ht = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    montant_tva = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    montant_paye = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    statut = models.CharField(max_length=15, choices=STATUTS, default='brouillon')
    ecriture = models.ForeignKey(EcritureComptable, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    fichier = models.FileField(upload_to='factures/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'factures'
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-date_facture']
    
    def __str__(self):
        return f"{self.numero} - {self.tiers.raison_sociale}"
    
    @property
    def reste_a_payer(self):
        return self.montant_ttc - self.montant_paye


class LigneFacture(models.Model):
    """Lignes de facture"""
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    designation = models.CharField(max_length=200)
    quantite = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18.00'))
    montant_ht = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    montant_tva = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    compte_comptable = models.ForeignKey(PlanComptable, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'lignes_factures'
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de factures'
    
    def save(self, *args, **kwargs):
        self.montant_ht = self.quantite * self.prix_unitaire
        self.montant_tva = self.montant_ht * self.taux_tva / 100
        self.montant_ttc = self.montant_ht + self.montant_tva
        super().save(*args, **kwargs)


class Reglement(models.Model):
    """Règlements (paiements)"""
    MODES_PAIEMENT = [
        ('especes', 'Espèces'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement bancaire'),
        ('mobile', 'Mobile Money'),
        ('carte', 'Carte bancaire'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='reglements')
    numero = models.CharField(max_length=50, verbose_name='N° Règlement')
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='reglements')
    date_reglement = models.DateField(verbose_name='Date règlement')
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    mode_paiement = models.CharField(max_length=15, choices=MODES_PAIEMENT)
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name='Référence paiement')
    ecriture = models.ForeignKey(EcritureComptable, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reglements'
        verbose_name = 'Règlement'
        verbose_name_plural = 'Règlements'
        ordering = ['-date_reglement']
    
    def __str__(self):
        return f"{self.numero} - {self.montant} GNF"


class TauxTVA(models.Model):
    """Taux de TVA configurables"""
    entreprise = models.ForeignKey('core.Entreprise', on_delete=models.CASCADE, related_name='taux_tva')
    libelle = models.CharField(max_length=50)
    taux = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    compte_tva_collectee = models.ForeignKey(PlanComptable, on_delete=models.SET_NULL, null=True, blank=True, related_name='tva_collectee')
    compte_tva_deductible = models.ForeignKey(PlanComptable, on_delete=models.SET_NULL, null=True, blank=True, related_name='tva_deductible')
    est_defaut = models.BooleanField(default=False)
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'taux_tva'
        verbose_name = 'Taux de TVA'
        verbose_name_plural = 'Taux de TVA'
    
    def __str__(self):
        return f"{self.libelle} ({self.taux}%)"
