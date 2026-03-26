"""
Commande de management : creer_demo
Crée des données de démonstration réalistes pour présenter GuineeRH à des clients
potentiels en Guinée. Idempotente : utilise get_or_create partout.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from datetime import date
from decimal import Decimal
import uuid


class Command(BaseCommand):
    help = 'Crée des données de démonstration réalistes pour GuineeRH'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('========================================'))
        self.stdout.write(self.style.SUCCESS('  GuineeRH — Création données démo'))
        self.stdout.write(self.style.SUCCESS('========================================'))

        entreprise = self._creer_entreprise()
        utilisateur = self._creer_utilisateur(entreprise)
        societe = self._creer_societe(entreprise)
        etablissement = self._creer_etablissement(societe)
        services, postes = self._creer_structure(etablissement)
        rubriques = self._creer_rubriques(entreprise)
        employes = self._creer_employes(entreprise, etablissement, services, postes, utilisateur)
        periode = self._creer_periode(entreprise, utilisateur)
        self._creer_bulletins(employes, rubriques, periode, entreprise)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('========================================'))
        self.stdout.write(self.style.SUCCESS('  Demo creee avec succes !'))
        self.stdout.write(self.style.SUCCESS('  Login : demo@guineerh.com'))
        self.stdout.write(self.style.SUCCESS('  Mot de passe : Demo2026!'))
        self.stdout.write(self.style.SUCCESS('========================================'))

    # ------------------------------------------------------------------
    # Entreprise
    # ------------------------------------------------------------------
    def _creer_entreprise(self):
        from core.models import Entreprise
        entreprise, created = Entreprise.objects.get_or_create(
            nif='NIF-DEMO-001',
            defaults={
                'nom_entreprise': 'SOGUIPHONE SARL',
                'slug': 'soguiphone-sarl',
                'secteur_activite': 'Télécommunications',
                'num_cnss': 'CNSS-DEMO-001',
                'adresse': 'Commune de Kaloum, Avenue de la République, Conakry',
                'ville': 'Conakry',
                'pays': 'Guinée',
                'telephone': '+224 624 00 00 00',
                'email': 'rh@soguiphone.gn',
                'actif': True,
                'plan_abonnement': 'pro',
                'module_paie': True,
                'module_conges': True,
                'max_employes': 200,
                'max_utilisateurs': 20,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  [OK] Entreprise SOGUIPHONE SARL creee'))
        else:
            self.stdout.write(self.style.WARNING('  [--] Entreprise SOGUIPHONE SARL deja existante'))
        return entreprise

    # ------------------------------------------------------------------
    # Utilisateur admin démo
    # ------------------------------------------------------------------
    def _creer_utilisateur(self, entreprise):
        from core.models import Utilisateur
        utilisateur, created = Utilisateur.objects.get_or_create(
            username='demo@guineerh.com',
            defaults={
                'email': 'demo@guineerh.com',
                'first_name': 'Admin',
                'last_name': 'Demo',
                'entreprise': entreprise,
                'est_admin_entreprise': True,
                'is_staff': True,
                'actif': True,
            }
        )
        if created:
            utilisateur.set_password('Demo2026!')
            utilisateur.save()
            self.stdout.write(self.style.SUCCESS('  [OK] Utilisateur demo@guineerh.com cree'))
        else:
            self.stdout.write(self.style.WARNING('  [--] Utilisateur demo@guineerh.com deja existant'))
        return utilisateur

    # ------------------------------------------------------------------
    # Société (Societe dans core)
    # ------------------------------------------------------------------
    def _creer_societe(self, entreprise):
        from core.models import Societe
        societe, created = Societe.objects.get_or_create(
            nif='NIF-DEMO-001',
            defaults={
                'entreprise': entreprise,
                'raison_sociale': 'SOGUIPHONE SARL',
                'forme_juridique': 'SARL',
                'num_cnss_employeur': 'CNSS-DEMO-001',
                'adresse': 'Commune de Kaloum, Avenue de la République',
                'ville': 'Conakry',
                'pays': 'Guinée',
                'telephone': '+224 624 00 00 00',
                'email': 'rh@soguiphone.gn',
                'secteur_activite': 'Télécommunications',
                'actif': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  [OK] Societe SOGUIPHONE SARL creee'))
        else:
            self.stdout.write(self.style.WARNING('  [--] Societe deja existante'))
        return societe

    # ------------------------------------------------------------------
    # Etablissement
    # ------------------------------------------------------------------
    def _creer_etablissement(self, societe):
        from core.models import Etablissement
        etablissement, created = Etablissement.objects.get_or_create(
            code_etablissement='SGPH-SIEGE',
            defaults={
                'societe': societe,
                'nom_etablissement': 'Siège Social SOGUIPHONE',
                'type_etablissement': 'siege',
                'adresse': 'Commune de Kaloum, Avenue de la République',
                'ville': 'Conakry',
                'actif': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  [OK] Etablissement Siege Social cree'))
        else:
            self.stdout.write(self.style.WARNING('  [--] Etablissement deja existant'))
        return etablissement

    # ------------------------------------------------------------------
    # Structure (Services + Postes)
    # ------------------------------------------------------------------
    def _creer_structure(self, etablissement):
        from core.models import Service, Poste

        def get_or_create_service(code, nom):
            svc, created = Service.objects.get_or_create(
                code_service=code,
                defaults={
                    'etablissement': etablissement,
                    'nom_service': nom,
                    'actif': True,
                }
            )
            return svc

        def get_or_create_poste(code, intitule, categorie):
            poste, created = Poste.objects.get_or_create(
                code_poste=code,
                defaults={
                    'intitule_poste': intitule,
                    'categorie_professionnelle': categorie,
                    'actif': True,
                }
            )
            return poste

        svc_direction = get_or_create_service('SGPH-DIR', 'Direction Générale')
        svc_rh = get_or_create_service('SGPH-RH', 'Ressources Humaines')
        svc_commercial = get_or_create_service('SGPH-COM', 'Commercial & Ventes')
        svc_technique = get_or_create_service('SGPH-TECH', 'Technique & Réseaux')

        poste_dg = get_or_create_poste('DG-001', 'Directeur Général', 'cadre')
        poste_rh = get_or_create_poste('RH-001', 'Responsable RH Senior', 'cadre')
        poste_com = get_or_create_poste('COM-001', 'Chargé Commercial', 'agent_maitrise')
        poste_tech = get_or_create_poste('TECH-001', 'Technicien Réseaux', 'employe')
        poste_stg = get_or_create_poste('STG-001', 'Stagiaire', 'employe')

        self.stdout.write(self.style.SUCCESS('  [OK] Structure (services + postes) prete'))

        services = {
            'direction': svc_direction,
            'rh': svc_rh,
            'commercial': svc_commercial,
            'technique': svc_technique,
        }
        postes = {
            'dg': poste_dg,
            'rh': poste_rh,
            'commercial': poste_com,
            'technicien': poste_tech,
            'stagiaire': poste_stg,
        }
        return services, postes

    # ------------------------------------------------------------------
    # Rubriques de paie
    # ------------------------------------------------------------------
    def _creer_rubriques(self, entreprise):
        from paie.models import RubriquePaie

        def creer_rubrique(code, libelle, type_r, categorie, mode, soumis_cnss, soumis_irg,
                           montant=None, taux=None, ordre=100, inclus_brut=True, exonere_rts=False):
            rubrique, created = RubriquePaie.objects.get_or_create(
                entreprise=entreprise,
                code_rubrique=code,
                defaults={
                    'libelle_rubrique': libelle,
                    'type_rubrique': type_r,
                    'categorie_rubrique': categorie,
                    'mode_calcul': mode,
                    'soumis_cnss': soumis_cnss,
                    'soumis_irg': soumis_irg,
                    'montant_fixe': Decimal(str(montant)) if montant else None,
                    'taux_rubrique': Decimal(str(taux)) if taux else None,
                    'ordre_calcul': ordre,
                    'ordre_affichage': ordre,
                    'inclus_brut': inclus_brut,
                    'exonere_rts': exonere_rts,
                    'actif': True,
                    'affichage_bulletin': True,
                }
            )
            return rubrique

        rubriques = {
            'salaire_base': creer_rubrique(
                'SAL-BASE', 'Salaire de Base', 'gain', 'salaire_base', 'fixe',
                True, True, ordre=10
            ),
            'indemnite_transport': creer_rubrique(
                'IND-TRANS', 'Indemnité de Transport', 'gain', 'indemnite', 'fixe',
                False, False, montant=200000, ordre=20, exonere_rts=True
            ),
            'indemnite_logement': creer_rubrique(
                'IND-LOG', 'Indemnité de Logement', 'gain', 'indemnite', 'fixe',
                False, False, montant=0, ordre=30, exonere_rts=True
            ),
            'prime_performance': creer_rubrique(
                'PRIME-PERF', 'Prime de Performance', 'gain', 'prime', 'fixe',
                True, True, ordre=40
            ),
            'cnss_salarie': creer_rubrique(
                'CNSS-SAL', 'Cotisation CNSS (salarié 5%)', 'retenue', 'cotisation',
                'pourcentage_brut', False, False, taux=5.0, ordre=60, inclus_brut=False
            ),
            'rts': creer_rubrique(
                'RTS', 'Retenue à la Source (RTS)', 'retenue', 'retenue', 'formule',
                False, False, ordre=70, inclus_brut=False
            ),
        }

        self.stdout.write(self.style.SUCCESS('  [OK] Rubriques de paie creees'))
        return rubriques

    # ------------------------------------------------------------------
    # Employés
    # ------------------------------------------------------------------
    def _creer_employes(self, entreprise, etablissement, services, postes, utilisateur):
        from employes.models import Employe
        from paie.models import ElementSalaire, RubriquePaie

        rubriques_base = RubriquePaie.objects.filter(
            entreprise=entreprise, code_rubrique='SAL-BASE'
        ).first()
        rubrique_transport = RubriquePaie.objects.filter(
            entreprise=entreprise, code_rubrique='IND-TRANS'
        ).first()
        rubrique_logement = RubriquePaie.objects.filter(
            entreprise=entreprise, code_rubrique='IND-LOG'
        ).first()
        rubrique_prime = RubriquePaie.objects.filter(
            entreprise=entreprise, code_rubrique='PRIME-PERF'
        ).first()

        profils = [
            {
                'matricule': 'SGPH-001',
                'civilite': 'M.',
                'nom': 'CAMARA',
                'prenoms': 'Alpha Oumar',
                'sexe': 'M',
                'date_naissance': date(1975, 3, 15),
                'lieu_naissance': 'Conakry',
                'type_contrat': 'CDI',
                'date_embauche': date(2010, 1, 15),
                'situation_matrimoniale': 'marie',
                'nombre_enfants': 3,
                'service': services['direction'],
                'poste': postes['dg'],
                'salaire_base': Decimal('8500000'),
                'transport': Decimal('500000'),
                'logement': Decimal('1000000'),
                'prime': Decimal('850000'),
                'nationalite': 'Guinéenne',
                'telephone_principal': '+224 622 11 22 33',
                'email_professionnel': 'a.camara@soguiphone.gn',
                'mode_paiement': 'virement',
                'nom_banque': 'Ecobank Guinée',
            },
            {
                'matricule': 'SGPH-002',
                'civilite': 'Mme',
                'nom': 'DIALLO',
                'prenoms': 'Fatoumata',
                'sexe': 'F',
                'date_naissance': date(1985, 7, 22),
                'lieu_naissance': 'Labé',
                'type_contrat': 'CDI',
                'date_embauche': date(2015, 3, 1),
                'situation_matrimoniale': 'marie',
                'nombre_enfants': 2,
                'service': services['rh'],
                'poste': postes['rh'],
                'salaire_base': Decimal('3200000'),
                'transport': Decimal('250000'),
                'logement': Decimal('400000'),
                'prime': Decimal('320000'),
                'nationalite': 'Guinéenne',
                'telephone_principal': '+224 628 44 55 66',
                'email_professionnel': 'f.diallo@soguiphone.gn',
                'mode_paiement': 'virement',
                'nom_banque': 'Banque Islamique de Guinée',
            },
            {
                'matricule': 'SGPH-003',
                'civilite': 'M.',
                'nom': 'BALDE',
                'prenoms': 'Mamadou Cellou',
                'sexe': 'M',
                'date_naissance': date(1990, 11, 5),
                'lieu_naissance': 'Kindia',
                'type_contrat': 'CDI',
                'date_embauche': date(2018, 6, 1),
                'situation_matrimoniale': 'marie',
                'nombre_enfants': 1,
                'service': services['commercial'],
                'poste': postes['commercial'],
                'salaire_base': Decimal('2800000'),
                'transport': Decimal('250000'),
                'logement': Decimal('0'),
                'prime': Decimal('400000'),
                'nationalite': 'Guinéenne',
                'telephone_principal': '+224 655 77 88 99',
                'email_professionnel': 'm.balde@soguiphone.gn',
                'mode_paiement': 'mobile_money',
                'operateur_mobile_money': 'Orange Money',
            },
            {
                'matricule': 'SGPH-004',
                'civilite': 'M.',
                'nom': 'KOUROUMA',
                'prenoms': 'Sekou',
                'sexe': 'M',
                'date_naissance': date(1993, 4, 18),
                'lieu_naissance': 'Nzérékoré',
                'type_contrat': 'CDI',
                'date_embauche': date(2020, 9, 15),
                'situation_matrimoniale': 'celibataire',
                'nombre_enfants': 0,
                'service': services['technique'],
                'poste': postes['technicien'],
                'salaire_base': Decimal('2100000'),
                'transport': Decimal('200000'),
                'logement': Decimal('0'),
                'prime': Decimal('150000'),
                'nationalite': 'Guinéenne',
                'telephone_principal': '+224 661 33 44 55',
                'email_professionnel': 's.kourouma@soguiphone.gn',
                'mode_paiement': 'mobile_money',
                'operateur_mobile_money': 'MTN MoMo',
            },
            {
                'matricule': 'SGPH-005',
                'civilite': 'Mlle',
                'nom': 'SOUMAH',
                'prenoms': 'Aminata',
                'sexe': 'F',
                'date_naissance': date(2003, 1, 30),
                'lieu_naissance': 'Conakry',
                'type_contrat': 'stage',
                'date_embauche': date(2026, 1, 6),
                'situation_matrimoniale': 'celibataire',
                'nombre_enfants': 0,
                'service': services['rh'],
                'poste': postes['stagiaire'],
                'salaire_base': Decimal('700000'),
                'transport': Decimal('100000'),
                'logement': Decimal('0'),
                'prime': Decimal('0'),
                'nationalite': 'Guinéenne',
                'telephone_principal': '+224 625 99 00 11',
                'email_professionnel': 'a.soumah@soguiphone.gn',
                'mode_paiement': 'mobile_money',
                'operateur_mobile_money': 'Orange Money',
            },
        ]

        employes = []
        for p in profils:
            defaults = {
                'entreprise': entreprise,
                'civilite': p['civilite'],
                'nom': p['nom'],
                'prenoms': p['prenoms'],
                'sexe': p['sexe'],
                'date_naissance': p['date_naissance'],
                'lieu_naissance': p['lieu_naissance'],
                'type_contrat': p['type_contrat'],
                'date_embauche': p['date_embauche'],
                'date_debut_contrat': p['date_embauche'],
                'situation_matrimoniale': p['situation_matrimoniale'],
                'nombre_enfants': p['nombre_enfants'],
                'etablissement': etablissement,
                'service': p['service'],
                'poste': p['poste'],
                'statut_employe': 'actif',
                'nationalite': p['nationalite'],
                'telephone_principal': p['telephone_principal'],
                'email_professionnel': p['email_professionnel'],
                'mode_paiement': p['mode_paiement'],
                'utilisateur_creation': utilisateur,
            }
            if p.get('nom_banque'):
                defaults['nom_banque'] = p['nom_banque']
            if p.get('operateur_mobile_money'):
                defaults['operateur_mobile_money'] = p['operateur_mobile_money']
                defaults['numero_mobile_money'] = p['telephone_principal']

            employe, created = Employe.objects.get_or_create(
                matricule=p['matricule'],
                defaults=defaults
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  [OK] Employe cree : {employe.nom} {employe.prenoms}'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'  [--] Employe deja existant : {employe.nom} {employe.prenoms}'
                ))

            # Elements de salaire
            if rubriques_base:
                ElementSalaire.objects.get_or_create(
                    employe=employe,
                    rubrique=rubriques_base,
                    date_debut=p['date_embauche'],
                    defaults={
                        'montant': p['salaire_base'],
                        'actif': True,
                        'recurrent': True,
                    }
                )
            if rubrique_transport and p['transport'] > 0:
                ElementSalaire.objects.get_or_create(
                    employe=employe,
                    rubrique=rubrique_transport,
                    date_debut=p['date_embauche'],
                    defaults={
                        'montant': p['transport'],
                        'actif': True,
                        'recurrent': True,
                    }
                )
            if rubrique_logement and p['logement'] > 0:
                ElementSalaire.objects.get_or_create(
                    employe=employe,
                    rubrique=rubrique_logement,
                    date_debut=p['date_embauche'],
                    defaults={
                        'montant': p['logement'],
                        'actif': True,
                        'recurrent': True,
                    }
                )
            if rubrique_prime and p['prime'] > 0:
                ElementSalaire.objects.get_or_create(
                    employe=employe,
                    rubrique=rubrique_prime,
                    date_debut=p['date_embauche'],
                    defaults={
                        'montant': p['prime'],
                        'actif': True,
                        'recurrent': True,
                    }
                )
            employe._salaire_base_demo = p['salaire_base']
            employe._transport_demo = p['transport']
            employe._logement_demo = p['logement']
            employe._prime_demo = p['prime']
            employes.append(employe)

        return employes

    # ------------------------------------------------------------------
    # Période de paie Mars 2026
    # ------------------------------------------------------------------
    def _creer_periode(self, entreprise, utilisateur):
        from paie.models import PeriodePaie
        periode, created = PeriodePaie.objects.get_or_create(
            entreprise=entreprise,
            annee=2026,
            mois=3,
            defaults={
                'libelle': 'Mars 2026',
                'date_debut': date(2026, 3, 1),
                'date_fin': date(2026, 3, 31),
                'date_paiement': date(2026, 3, 28),
                'statut_periode': 'validee',
                'nombre_jours_travailles': 22,
                'nombre_heures_mois': Decimal('173.33'),
                'utilisateur_cloture': utilisateur,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  [OK] Periode Mars 2026 creee'))
        else:
            self.stdout.write(self.style.WARNING('  [--] Periode Mars 2026 deja existante'))
        return periode

    # ------------------------------------------------------------------
    # Bulletins de paie
    # ------------------------------------------------------------------
    def _creer_bulletins(self, employes, rubriques, periode, entreprise):
        from paie.models import BulletinPaie, LigneBulletin, RubriquePaie

        rub_cnss = RubriquePaie.objects.filter(
            entreprise=entreprise, code_rubrique='CNSS-SAL'
        ).first()
        rub_rts = RubriquePaie.objects.filter(
            entreprise=entreprise, code_rubrique='RTS'
        ).first()
        rub_base = rubriques.get('salaire_base')
        rub_transport = rubriques.get('indemnite_transport')
        rub_logement = rubriques.get('indemnite_logement')
        rub_prime = rubriques.get('prime_performance')

        taux_cnss = Decimal('0.05')

        # Barème RTS simplifié Guinée (annualisé puis mensuel)
        def calculer_rts(base_imposable_mensuelle):
            """Calcul RTS simplifié selon barème Guinée (base mensuelle)."""
            b = base_imposable_mensuelle
            if b <= 0:
                return Decimal('0')
            # Tranches mensuelles approximatives
            if b <= 1_000_000:
                return Decimal('0')
            elif b <= 3_000_000:
                return (b - Decimal('1000000')) * Decimal('0.10')
            elif b <= 5_000_000:
                return Decimal('200000') + (b - Decimal('3000000')) * Decimal('0.15')
            elif b <= 10_000_000:
                return Decimal('500000') + (b - Decimal('5000000')) * Decimal('0.20')
            else:
                return Decimal('1500000') + (b - Decimal('10000000')) * Decimal('0.25')

        compteur = 1
        for employe in employes:
            numero = f'BP-DEMO-2026-03-{compteur:03d}'
            bulletin, created = BulletinPaie.objects.get_or_create(
                employe=employe,
                periode=periode,
                defaults={'numero_bulletin': numero}
            )

            if not created:
                self.stdout.write(self.style.WARNING(
                    f'  [--] Bulletin deja existant pour {employe.nom}'
                ))
                compteur += 1
                continue

            # Récupérer les montants stockés sur l'objet employe
            sal_base = getattr(employe, '_salaire_base_demo', Decimal('0'))
            transport = getattr(employe, '_transport_demo', Decimal('0'))
            logement = getattr(employe, '_logement_demo', Decimal('0'))
            prime = getattr(employe, '_prime_demo', Decimal('0'))

            brut = sal_base + transport + logement + prime

            # CNSS salarié : 5% du brut imposable CNSS (base + prime, hors indemnités exo)
            base_cnss = sal_base + prime
            cnss_sal = (base_cnss * taux_cnss).quantize(Decimal('1'))
            cnss_emp = (base_cnss * Decimal('0.18')).quantize(Decimal('1'))

            # Base imposable RTS = brut - indemnités exo - CNSS salarié
            base_rts = brut - transport - logement - cnss_sal
            rts = calculer_rts(base_rts).quantize(Decimal('1'))

            net = brut - cnss_sal - rts

            # Mise à jour bulletin
            bulletin.numero_bulletin = numero
            bulletin.mois_paie = 3
            bulletin.annee_paie = 2026
            bulletin.salaire_base = sal_base
            bulletin.salaire_brut = brut
            bulletin.cnss_employe = cnss_sal
            bulletin.cnss_employeur = cnss_emp
            bulletin.irg = rts
            bulletin.base_rts = base_rts
            bulletin.net_a_payer = net
            bulletin.statut_bulletin = 'valide'
            bulletin.date_calcul = timezone.now()
            bulletin.heures_normales = Decimal('173.33')
            bulletin.save()

            # Lignes de bulletin
            def ajouter_ligne(rubrique, montant_val, base_val=None, taux_val=None, ordre=100):
                if rubrique and montant_val != Decimal('0'):
                    LigneBulletin.objects.get_or_create(
                        bulletin=bulletin,
                        rubrique=rubrique,
                        defaults={
                            'base': base_val or montant_val,
                            'taux': taux_val,
                            'montant': montant_val,
                            'ordre': ordre,
                        }
                    )

            ajouter_ligne(rub_base, sal_base, ordre=10)
            ajouter_ligne(rub_transport, transport, ordre=20)
            ajouter_ligne(rub_logement, logement, ordre=30)
            ajouter_ligne(rub_prime, prime, ordre=40)
            ajouter_ligne(rub_cnss, cnss_sal, base_val=base_cnss,
                         taux_val=Decimal('5.0000'), ordre=60)
            ajouter_ligne(rub_rts, rts, base_val=base_rts, ordre=70)

            self.stdout.write(self.style.SUCCESS(
                f'  [OK] Bulletin {numero} : {employe.nom} '
                f'| Brut={brut:,.0f} | CNSS={cnss_sal:,.0f} '
                f'| RTS={rts:,.0f} | Net={net:,.0f} GNF'
            ))
            compteur += 1
