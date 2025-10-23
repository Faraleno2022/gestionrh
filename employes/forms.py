from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, Button, HTML
from crispy_forms.bootstrap import TabHolder, Tab
from .models import Employe, ContratEmploye


class EmployeForm(forms.ModelForm):
    """Formulaire de création/modification d'un employé"""
    
    class Meta:
        model = Employe
        fields = [
            # État civil
            'civilite', 'nom', 'prenoms', 'nom_jeune_fille', 'sexe',
            'situation_matrimoniale', 'nombre_enfants', 'photo',
            
            # Naissance
            'date_naissance', 'lieu_naissance', 'commune_naissance',
            'prefecture_naissance', 'nationalite',
            
            # Identification
            'type_piece_identite', 'numero_piece_identite',
            'date_delivrance_piece', 'date_expiration_piece',
            'num_cnss_individuel',
            
            # Contact
            'adresse_actuelle', 'commune_residence', 'prefecture_residence',
            'telephone_principal', 'telephone_secondaire',
            'email_personnel', 'email_professionnel',
            
            # Contact d'urgence
            'contact_urgence_nom', 'contact_urgence_lien',
            'contact_urgence_telephone',
            
            # Professionnel
            'matricule', 'etablissement', 'service', 'poste',
            'date_embauche', 'date_anciennete', 'type_contrat',
            'superieur_hierarchique',
            
            # Bancaire
            'mode_paiement', 'nom_banque', 'agence_banque',
            'numero_compte', 'rib', 'operateur_mobile_money',
            'numero_mobile_money'
        ]
        
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_delivrance_piece': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_expiration_piece': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_anciennete': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'adresse_actuelle': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre le matricule optionnel (sera généré automatiquement)
        self.fields['matricule'].required = False
        
        # Helper Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
        self.helper.layout = Layout(
            TabHolder(
                Tab('État civil',
                    Fieldset('Informations personnelles',
                        Row(
                            Column('civilite', css_class='col-md-2'),
                            Column('nom', css_class='col-md-5'),
                            Column('prenoms', css_class='col-md-5'),
                        ),
                        Row(
                            Column('nom_jeune_fille', css_class='col-md-4'),
                            Column('sexe', css_class='col-md-4'),
                            Column('situation_matrimoniale', css_class='col-md-4'),
                        ),
                        Row(
                            Column('nombre_enfants', css_class='col-md-4'),
                            Column('photo', css_class='col-md-8'),
                        ),
                    ),
                    Fieldset('Naissance',
                        Row(
                            Column('date_naissance', css_class='col-md-4'),
                            Column('lieu_naissance', css_class='col-md-8'),
                        ),
                        Row(
                            Column('commune_naissance', css_class='col-md-6'),
                            Column('prefecture_naissance', css_class='col-md-6'),
                        ),
                        'nationalite',
                    ),
                ),
                
                Tab('Identification',
                    Fieldset('Pièce d\'identité',
                        Row(
                            Column('type_piece_identite', css_class='col-md-6'),
                            Column('numero_piece_identite', css_class='col-md-6'),
                        ),
                        Row(
                            Column('date_delivrance_piece', css_class='col-md-6'),
                            Column('date_expiration_piece', css_class='col-md-6'),
                        ),
                    ),
                    Fieldset('Sécurité sociale',
                        'num_cnss_individuel',
                        HTML('<small class="form-text text-muted">Numéro CNSS obligatoire pour la paie</small>'),
                    ),
                ),
                
                Tab('Contact',
                    Fieldset('Adresse',
                        'adresse_actuelle',
                        Row(
                            Column('commune_residence', css_class='col-md-6'),
                            Column('prefecture_residence', css_class='col-md-6'),
                        ),
                    ),
                    Fieldset('Téléphones et emails',
                        Row(
                            Column('telephone_principal', css_class='col-md-6'),
                            Column('telephone_secondaire', css_class='col-md-6'),
                        ),
                        Row(
                            Column('email_personnel', css_class='col-md-6'),
                            Column('email_professionnel', css_class='col-md-6'),
                        ),
                    ),
                    Fieldset('Contact d\'urgence',
                        Row(
                            Column('contact_urgence_nom', css_class='col-md-6'),
                            Column('contact_urgence_lien', css_class='col-md-6'),
                        ),
                        'contact_urgence_telephone',
                    ),
                ),
                
                Tab('Professionnel',
                    Fieldset('Affectation',
                        'matricule',
                        HTML('<small class="form-text text-muted">Laisser vide pour génération automatique</small>'),
                        Row(
                            Column('etablissement', css_class='col-md-4'),
                            Column('service', css_class='col-md-4'),
                            Column('poste', css_class='col-md-4'),
                        ),
                        'superieur_hierarchique',
                    ),
                    Fieldset('Contrat',
                        Row(
                            Column('date_embauche', css_class='col-md-4'),
                            Column('date_anciennete', css_class='col-md-4'),
                            Column('type_contrat', css_class='col-md-4'),
                        ),
                        HTML('<small class="form-text text-muted">La date d\'ancienneté peut différer de la date d\'embauche</small>'),
                    ),
                ),
                
                Tab('Bancaire',
                    Fieldset('Mode de paiement',
                        'mode_paiement',
                    ),
                    Fieldset('Informations bancaires',
                        Row(
                            Column('nom_banque', css_class='col-md-6'),
                            Column('agence_banque', css_class='col-md-6'),
                        ),
                        Row(
                            Column('numero_compte', css_class='col-md-6'),
                            Column('rib', css_class='col-md-6'),
                        ),
                    ),
                    Fieldset('Mobile Money',
                        Row(
                            Column('operateur_mobile_money', css_class='col-md-6'),
                            Column('numero_mobile_money', css_class='col-md-6'),
                        ),
                    ),
                ),
            ),
            
            HTML('<hr>'),
            Row(
                Column(
                    Submit('submit', 'Enregistrer', css_class='btn btn-primary'),
                    css_class='col-md-6'
                ),
                Column(
                    Button('cancel', 'Annuler', css_class='btn btn-secondary',
                           onclick="window.history.back()"),
                    css_class='col-md-6 text-end'
                ),
            ),
        )
    
    def clean_num_cnss_individuel(self):
        """Validation du numéro CNSS"""
        num_cnss = self.cleaned_data.get('num_cnss_individuel')
        if num_cnss:
            # Vérifier l'unicité
            if self.instance.pk:
                # Mode édition
                if Employe.objects.exclude(pk=self.instance.pk).filter(
                    num_cnss_individuel=num_cnss
                ).exists():
                    raise forms.ValidationError('Ce numéro CNSS est déjà utilisé par un autre employé')
            else:
                # Mode création
                if Employe.objects.filter(num_cnss_individuel=num_cnss).exists():
                    raise forms.ValidationError('Ce numéro CNSS est déjà utilisé')
        return num_cnss
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Vérifier que la date de naissance est cohérente
        date_naissance = cleaned_data.get('date_naissance')
        date_embauche = cleaned_data.get('date_embauche')
        
        if date_naissance and date_embauche:
            age_embauche = (date_embauche - date_naissance).days // 365
            if age_embauche < 16:
                raise forms.ValidationError(
                    'L\'âge à l\'embauche doit être d\'au moins 16 ans'
                )
        
        # Vérifier les dates de pièce d'identité
        date_delivrance = cleaned_data.get('date_delivrance_piece')
        date_expiration = cleaned_data.get('date_expiration_piece')
        
        if date_delivrance and date_expiration:
            if date_expiration <= date_delivrance:
                raise forms.ValidationError(
                    'La date d\'expiration doit être postérieure à la date de délivrance'
                )
        
        return cleaned_data


class ContratForm(forms.ModelForm):
    """Formulaire de contrat d'employé"""
    
    class Meta:
        model = ContratEmploye
        fields = [
            'num_contrat', 'type_contrat', 'date_debut', 'date_fin',
            'duree_mois', 'motif_contrat', 'periode_essai_mois',
            'date_fin_essai', 'fichier_contrat', 'observations',
            'date_signature'
        ]
        
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin_essai': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_signature': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif_contrat': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'fichier_contrat': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset('Informations du contrat',
                Row(
                    Column('num_contrat', css_class='col-md-6'),
                    Column('type_contrat', css_class='col-md-6'),
                ),
                Row(
                    Column('date_debut', css_class='col-md-6'),
                    Column('date_fin', css_class='col-md-6'),
                ),
                'duree_mois',
                'motif_contrat',
            ),
            Fieldset('Période d\'essai',
                Row(
                    Column('periode_essai_mois', css_class='col-md-6'),
                    Column('date_fin_essai', css_class='col-md-6'),
                ),
            ),
            Fieldset('Document',
                'fichier_contrat',
                'date_signature',
                'observations',
            ),
            Submit('submit', 'Enregistrer le contrat', css_class='btn btn-primary'),
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        type_contrat = cleaned_data.get('type_contrat')
        date_fin = cleaned_data.get('date_fin')
        
        # Pour un CDD, la date de fin est obligatoire
        if type_contrat == 'CDD' and not date_fin:
            raise forms.ValidationError(
                'La date de fin est obligatoire pour un contrat CDD'
            )
        
        # Vérifier que la date de fin est après la date de début
        date_debut = cleaned_data.get('date_debut')
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise forms.ValidationError(
                    'La date de fin doit être postérieure à la date de début'
                )
        
        return cleaned_data


class EmployeSearchForm(forms.Form):
    """Formulaire de recherche d'employés"""
    search = forms.CharField(
        required=False,
        label='Rechercher',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom, prénom, matricule, N° CNSS...'
        })
    )
    
    statut = forms.ChoiceField(
        required=False,
        label='Statut',
        choices=[('', 'Tous')] + list(Employe.STATUTS),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    type_contrat = forms.ChoiceField(
        required=False,
        label='Type de contrat',
        choices=[('', 'Tous')] + list(Employe.TYPES_CONTRATS),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sexe = forms.ChoiceField(
        required=False,
        label='Sexe',
        choices=[('', 'Tous'), ('M', 'Masculin'), ('F', 'Féminin')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
