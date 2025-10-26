from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class Entreprise(models.Model):
    """Modèle pour gérer plusieurs entreprises"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom_entreprise = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    nif = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='NIF')
    num_cnss = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='N° CNSS')
    adresse = models.TextField(blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=50, default='Guinée')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    logo = models.ImageField(upload_to='entreprises/logos/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateField(blank=True, null=True, help_text='Date d\'expiration de l\'abonnement')
    actif = models.BooleanField(default=True)
    plan_abonnement = models.CharField(max_length=50, default='gratuit', choices=[
        ('gratuit', 'Gratuit'),
        ('basique', 'Basique'),
        ('premium', 'Premium'),
        ('entreprise', 'Entreprise'),
    ])
    max_utilisateurs = models.IntegerField(default=5, help_text='Nombre maximum d\'utilisateurs')
    
    class Meta:
        db_table = 'entreprises'
        verbose_name = 'Entreprise'
        verbose_name_plural = 'Entreprises'
        ordering = ['nom_entreprise']
    
    def __str__(self):
        return self.nom_entreprise


class ProfilUtilisateur(models.Model):
    """Profils d'utilisateurs avec niveaux d'accès"""
    NIVEAUX_ACCES = (
        (1, 'Consultation'),
        (2, 'Opérateur'),
        (3, 'Manager'),
        (4, 'RH'),
        (5, 'Administrateur'),
    )
    
    nom_profil = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    niveau_acces = models.IntegerField(choices=NIVEAUX_ACCES, default=1)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'profils_utilisateurs'
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'
        ordering = ['niveau_acces']
    
    def __str__(self):
        return self.nom_profil


class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé avec support multi-entreprise"""
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='utilisateurs', null=True)
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.SET_NULL, null=True, related_name='utilisateurs')
    est_admin_entreprise = models.BooleanField(default=False, help_text='Administrateur de l\'entreprise')
    actif = models.BooleanField(default=True)
    date_derniere_connexion = models.DateTimeField(null=True, blank=True)
    tentatives_connexion = models.IntegerField(default=0)
    photo = models.ImageField(upload_to='utilisateurs/', blank=True, null=True)
    require_reauth = models.BooleanField(default=False, help_text='Nécessite une réauthentification pour accéder aux menus')
    last_reauth = models.DateTimeField(null=True, blank=True, help_text='Dernière réauthentification')
    
    # Fix for groups and user_permissions clash
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='utilisateur_set',
        related_query_name='utilisateur',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='utilisateur_set',
        related_query_name='utilisateur',
    )
    
    class Meta:
        db_table = 'utilisateurs'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def enregistrer_connexion(self):
        """Enregistre la date de dernière connexion"""
        self.date_derniere_connexion = timezone.now()
        self.tentatives_connexion = 0
        self.save(update_fields=['date_derniere_connexion', 'tentatives_connexion'])


class DroitAcces(models.Model):
    """Droits d'accès par module pour chaque profil"""
    MODULES = (
        ('employes', 'Employés'),
        ('paie', 'Paie'),
        ('temps_travail', 'Temps de travail'),
        ('conges', 'Congés'),
        ('formation', 'Formation'),
        ('recrutement', 'Recrutement'),
        ('dashboard', 'Tableau de bord'),
        ('rapports', 'Rapports'),
        ('parametres', 'Paramètres'),
    )
    
    profil = models.ForeignKey(ProfilUtilisateur, on_delete=models.CASCADE, related_name='droits')
    module = models.CharField(max_length=50, choices=MODULES)
    lecture = models.BooleanField(default=False)
    ecriture = models.BooleanField(default=False)
    modification = models.BooleanField(default=False)
    suppression = models.BooleanField(default=False)
    validation = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'droits_acces'
        verbose_name = 'Droit d\'accès'
        verbose_name_plural = 'Droits d\'accès'
        unique_together = ['profil', 'module']
    
    def __str__(self):
        return f"{self.profil.nom_profil} - {self.get_module_display()}"


class LogActivite(models.Model):
    """Journal des activités utilisateurs"""
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='logs')
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=50, blank=True, null=True)
    table_concernee = models.CharField(max_length=50, blank=True, null=True)
    id_enregistrement = models.IntegerField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date_action = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'logs_activite'
        verbose_name = 'Log d\'activité'
        verbose_name_plural = 'Logs d\'activité'
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.utilisateur} - {self.action} - {self.date_action}"


class Societe(models.Model):
    """Informations sur la société"""
    raison_sociale = models.CharField(max_length=200)
    forme_juridique = models.CharField(max_length=50, blank=True, null=True)
    nif = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='NIF')
    num_cnss_employeur = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name='N° CNSS Employeur')
    num_inam = models.CharField(max_length=50, blank=True, null=True, verbose_name='N° INAM')
    adresse = models.TextField(blank=True, null=True)
    commune = models.CharField(max_length=100, blank=True, null=True)
    prefecture = models.CharField(max_length=100, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=50, default='Guinée')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='societe/', blank=True, null=True)
    date_creation = models.DateField(blank=True, null=True)
    capital_social = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    secteur_activite = models.CharField(max_length=100, blank=True, null=True)
    code_ape = models.CharField(max_length=10, blank=True, null=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'societe'
        verbose_name = 'Société'
        verbose_name_plural = 'Sociétés'
    
    def __str__(self):
        return self.raison_sociale


class Etablissement(models.Model):
    """Établissements de la société"""
    TYPES = (
        ('siege', 'Siège'),
        ('agence', 'Agence'),
        ('succursale', 'Succursale'),
        ('usine', 'Usine'),
    )
    
    societe = models.ForeignKey(Societe, on_delete=models.CASCADE, related_name='etablissements')
    code_etablissement = models.CharField(max_length=20, unique=True)
    nom_etablissement = models.CharField(max_length=200)
    type_etablissement = models.CharField(max_length=50, choices=TYPES, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    commune = models.CharField(max_length=100, blank=True, null=True)
    prefecture = models.CharField(max_length=100, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    responsable = models.CharField(max_length=100, blank=True, null=True)
    date_ouverture = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'etablissements'
        verbose_name = 'Établissement'
        verbose_name_plural = 'Établissements'
        ordering = ['nom_etablissement']
    
    def __str__(self):
        return f"{self.code_etablissement} - {self.nom_etablissement}"


class Service(models.Model):
    """Services/Départements"""
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='services', null=True, blank=True)
    code_service = models.CharField(max_length=20, unique=True)
    nom_service = models.CharField(max_length=100)
    service_parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sous_services')
    niveau_hierarchique = models.IntegerField(default=1)
    responsable_service = models.ForeignKey('employes.Employe', on_delete=models.SET_NULL, null=True, blank=True, related_name='services_geres')
    description = models.TextField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'services'
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['nom_service']
    
    def __str__(self):
        return f"{self.code_service} - {self.nom_service}"


class Poste(models.Model):
    """Postes de travail"""
    CATEGORIES = (
        ('cadre', 'Cadre'),
        ('agent_maitrise', 'Agent de maîtrise'),
        ('employe', 'Employé'),
        ('ouvrier', 'Ouvrier'),
    )
    
    code_poste = models.CharField(max_length=20, unique=True)
    intitule_poste = models.CharField(max_length=100)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='postes')
    categorie_professionnelle = models.CharField(max_length=50, choices=CATEGORIES, blank=True, null=True)
    classification = models.CharField(max_length=10, blank=True, null=True, help_text='A1, B2, C3, etc.')
    niveau_requis = models.CharField(max_length=100, blank=True, null=True)
    experience_requise = models.IntegerField(blank=True, null=True, help_text='En années')
    description_poste = models.TextField(blank=True, null=True)
    responsabilites = models.TextField(blank=True, null=True)
    competences_requises = models.TextField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'postes'
        verbose_name = 'Poste'
        verbose_name_plural = 'Postes'
        ordering = ['intitule_poste']
    
    def __str__(self):
        return f"{self.code_poste} - {self.intitule_poste}"
