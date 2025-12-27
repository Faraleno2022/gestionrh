from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta

from employes.models import Employe
from paie.models import BulletinPaie, PeriodePaie
from temps_travail.models import Conge, Pointage


@login_required
def index(request):
    """Tableau de bord principal"""
    context = {}
    
    # Statistiques employés
    employes_actifs = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    )
    context['total_employes'] = employes_actifs.count()
    context['employes_hommes'] = employes_actifs.filter(sexe='M').count()
    context['employes_femmes'] = employes_actifs.filter(sexe='F').count()
    
    # Répartition par type de contrat
    context['employes_cdi'] = employes_actifs.filter(type_contrat='CDI').count()
    context['employes_cdd'] = employes_actifs.filter(type_contrat='CDD').count()
    context['employes_stage'] = employes_actifs.filter(type_contrat='Stage').count()
    
    # Congés en cours
    aujourd_hui = timezone.now().date()
    conges_en_cours = Conge.objects.filter(
        statut_demande='Approuvé',
        date_debut__lte=aujourd_hui,
        date_fin__gte=aujourd_hui,
        employe__entreprise=request.user.entreprise,
    )
    context['conges_en_cours'] = conges_en_cours.count()
    context['employes_en_conge'] = conges_en_cours.select_related('employe')[:5]
    
    # Congés en attente
    context['conges_en_attente'] = Conge.objects.filter(
        statut_demande='En attente',
        employe__entreprise=request.user.entreprise,
    ).count()
    
    # Paie du mois en cours
    mois_actuel = timezone.now().month
    annee_actuelle = timezone.now().year
    
    try:
        periode_actuelle = PeriodePaie.objects.get(
            entreprise=request.user.entreprise,
            annee=annee_actuelle,
            mois=mois_actuel
        )
        bulletins_mois = BulletinPaie.objects.filter(
            periode=periode_actuelle,
            employe__entreprise=request.user.entreprise,
        )
        context['bulletins_calcules'] = bulletins_mois.filter(statut_bulletin='Calculé').count()
        context['bulletins_valides'] = bulletins_mois.filter(statut_bulletin='Validé').count()
        context['masse_salariale'] = bulletins_mois.aggregate(
            total=Sum('net_a_payer')
        )['total'] or 0
    except PeriodePaie.DoesNotExist:
        context['bulletins_calcules'] = 0
        context['bulletins_valides'] = 0
        context['masse_salariale'] = 0
    
    # Pointages du jour
    context['pointages_jour'] = Pointage.objects.filter(
        date_pointage=aujourd_hui,
        employe__entreprise=request.user.entreprise,
    ).count()
    
    # Alertes
    context['alertes'] = []
    
    # Contrats arrivant à échéance (30 jours)
    date_limite = aujourd_hui + timedelta(days=30)
    contrats_echeance = Employe.objects.filter(
        entreprise=request.user.entreprise,
        type_contrat='CDD',
        date_fin_contrat__lte=date_limite,
        date_fin_contrat__gte=aujourd_hui,
        statut_employe='actif'
    ).count()
    
    if contrats_echeance > 0:
        context['alertes'].append({
            'type': 'warning',
            'icon': 'bi-exclamation-triangle',
            'message': f'{contrats_echeance} contrat(s) arrivent à échéance dans les 30 jours'
        })
    
    # Congés en attente de validation
    if context['conges_en_attente'] > 0:
        context['alertes'].append({
            'type': 'info',
            'icon': 'bi-calendar-check',
            'message': f'{context["conges_en_attente"]} demande(s) de congé en attente'
        })
    
    return render(request, 'dashboard/index.html', context)


@login_required
def rapports(request):
    """Page des rapports et statistiques"""
    context = {}
    
    # Statistiques annuelles
    annee = request.GET.get('annee', timezone.now().year)
    context['annee'] = int(annee)
    
    # Évolution effectif par mois
    effectif_mensuel = []
    for mois in range(1, 13):
        effectif = Employe.objects.filter(
            entreprise=request.user.entreprise,
            date_embauche__year__lte=annee,
            date_embauche__month__lte=mois
        ).exclude(
            date_depart__year__lt=annee
        ).exclude(
            date_depart__year=annee,
            date_depart__month__lt=mois
        ).count()
        effectif_mensuel.append(effectif)
    
    context['effectif_mensuel'] = effectif_mensuel
    context['mois'] = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                       'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    
    # Pyramide des âges
    aujourd_hui = timezone.now().date()
    employes_actifs = Employe.objects.filter(
        entreprise=request.user.entreprise,
        statut_employe='actif'
    )
    
    pyramide_ages = {
        '< 25 ans': 0,
        '25-34 ans': 0,
        '35-44 ans': 0,
        '45-54 ans': 0,
        '55+ ans': 0
    }
    
    for employe in employes_actifs:
        if employe.date_naissance:
            age = (aujourd_hui - employe.date_naissance).days // 365
            if age < 25:
                pyramide_ages['< 25 ans'] += 1
            elif age < 35:
                pyramide_ages['25-34 ans'] += 1
            elif age < 45:
                pyramide_ages['35-44 ans'] += 1
            elif age < 55:
                pyramide_ages['45-54 ans'] += 1
            else:
                pyramide_ages['55+ ans'] += 1
    
    context['pyramide_ages'] = pyramide_ages
    
    # Répartition par service
    from core.models import Service
    services_stats = []
    for service in Service.objects.filter(
        actif=True,
        etablissement__societe__entreprise=request.user.entreprise,
    ):
        effectif = employes_actifs.filter(service=service).count()
        if effectif > 0:
            services_stats.append({
                'nom': service.nom_service,
                'effectif': effectif
            })
    
    context['services_stats'] = services_stats
    
    return render(request, 'dashboard/rapports.html', context)


@login_required
def statistiques_paie(request):
    """Statistiques de paie"""
    context = {}
    
    annee = request.GET.get('annee', timezone.now().year)
    context['annee'] = int(annee)
    
    # Masse salariale mensuelle
    masse_mensuelle = []
    for mois in range(1, 13):
        try:
            periode = PeriodePaie.objects.get(
                entreprise=request.user.entreprise,
                annee=annee,
                mois=mois
            )
            total = BulletinPaie.objects.filter(
                periode=periode,
                statut_bulletin__in=['Validé', 'Payé'],
                employe__entreprise=request.user.entreprise,
            ).aggregate(total=Sum('net_a_payer'))['total'] or 0
            masse_mensuelle.append(float(total))
        except PeriodePaie.DoesNotExist:
            masse_mensuelle.append(0)
    
    context['masse_mensuelle'] = masse_mensuelle
    context['mois'] = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                       'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    
    return render(request, 'dashboard/statistiques_paie.html', context)


@login_required
def telecharger_manuel(request):
    """Télécharger le manuel d'utilisation en PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    import io
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    def nouvelle_page():
        p.showPage()
        return height - 2*cm
    
    def draw_title(y, text, size=16):
        p.setFont("Helvetica-Bold", size)
        p.setFillColor(colors.HexColor("#0d6efd"))
        p.drawString(2*cm, y, text)
        p.setFillColor(colors.black)
        return y - 0.8*cm
    
    def draw_subtitle(y, text, size=12):
        p.setFont("Helvetica-Bold", size)
        p.setFillColor(colors.HexColor("#198754"))
        p.drawString(2*cm, y, text)
        p.setFillColor(colors.black)
        return y - 0.6*cm
    
    def draw_text(y, text, indent=2):
        p.setFont("Helvetica", 10)
        max_width = width - 4*cm
        words = text.split()
        line = ""
        for word in words:
            test_line = line + " " + word if line else word
            if p.stringWidth(test_line, "Helvetica", 10) < max_width:
                line = test_line
            else:
                p.drawString(indent*cm, y, line)
                y -= 0.4*cm
                line = word
        if line:
            p.drawString(indent*cm, y, line)
            y -= 0.4*cm
        return y - 0.2*cm
    
    def draw_bullet(y, text, indent=2.5):
        p.drawString(indent*cm - 0.3*cm, y, "•")
        return draw_text(y, text, indent)
    
    y = height - 2*cm
    
    # === PAGE DE COUVERTURE ===
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(colors.HexColor("#0d6efd"))
    p.drawCentredString(width/2, height - 8*cm, "MANUEL D'UTILISATION")
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 9.5*cm, "Gestionnaire RH Guinée")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 12)
    p.drawCentredString(width/2, height - 12*cm, "Application de Gestion des Ressources Humaines")
    p.drawCentredString(width/2, height - 12.8*cm, "Paie, Congés, Pointages, Formations, Recrutement")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width/2, height - 16*cm, f"Version 1.0 - {timezone.now().strftime('%B %Y')}")
    p.drawCentredString(width/2, height - 16.6*cm, "www.guineerh.space")
    
    y = nouvelle_page()
    
    # === TABLE DES MATIÈRES ===
    y = draw_title(y, "TABLE DES MATIÈRES", 14)
    y -= 0.5*cm
    toc = [
        "1. Introduction",
        "2. Gestion des Employés",
        "3. Gestion de la Paie",
        "   3.1 Formules de calcul",
        "   3.2 Calcul du salaire net",
        "4. Gestion du Temps de Travail",
        "5. Gestion des Congés",
        "6. Déclarations Sociales",
        "7. Formations",
        "8. Recrutement",
    ]
    for item in toc:
        p.setFont("Helvetica", 11)
        p.drawString(2.5*cm, y, item)
        y -= 0.5*cm
    
    y = nouvelle_page()
    
    # === 1. INTRODUCTION ===
    y = draw_title(y, "1. INTRODUCTION")
    y = draw_text(y, "Le Gestionnaire RH Guinée est une application complète de gestion des ressources humaines adaptée au contexte guinéen. Elle permet de gérer l'ensemble du cycle de vie des employés, de la paie, des congés et des déclarations sociales.")
    y -= 0.3*cm
    y = draw_text(y, "L'application respecte la législation guinéenne en matière de travail et de cotisations sociales (CNSS, IRG).")
    
    y -= 0.8*cm
    y = draw_title(y, "2. GESTION DES EMPLOYÉS")
    y = draw_text(y, "Le module Employés permet de gérer les informations personnelles et professionnelles de chaque salarié:")
    y = draw_bullet(y, "Informations personnelles: nom, prénom, date de naissance, adresse, contact")
    y = draw_bullet(y, "Informations professionnelles: matricule, poste, service, établissement")
    y = draw_bullet(y, "Contrat: type (CDI, CDD, Stage), dates, salaire de base")
    y = draw_bullet(y, "Documents: pièce d'identité, diplômes, contrat signé")
    
    y -= 0.8*cm
    y = draw_title(y, "3. GESTION DE LA PAIE")
    y = draw_text(y, "Le module Paie permet de calculer et générer les bulletins de paie mensuels pour tous les employés.")
    
    y -= 0.5*cm
    y = draw_subtitle(y, "3.1 Formules de Calcul")
    y -= 0.3*cm
    
    # Tableau des formules
    formules_data = [
        ['Élément', 'Formule / Taux', 'Description'],
        ['Salaire Brut', 'Base + Primes - Absences', 'Total des gains avant retenues'],
        ['CNSS Employé', 'Brut × 5%', 'Part salariale CNSS'],
        ['CNSS Employeur', 'Brut × 18%', 'Part patronale CNSS'],
        ['Base IRG', 'Brut - CNSS Employé', 'Assiette imposable'],
        ['IRG', 'Barème progressif', 'Impôt sur le Revenu Guinéen'],
        ['Net à Payer', 'Brut - CNSS - IRG', 'Montant versé au salarié'],
    ]
    
    table = Table(formules_data, colWidths=[4*cm, 4.5*cm, 7*cm])
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    tw, th = table.wrapOn(p, width, height)
    table.drawOn(p, 2*cm, y - th)
    y = y - th - 0.8*cm
    
    y = draw_subtitle(y, "3.2 Barème IRG (Impôt sur le Revenu Guinéen)")
    y -= 0.3*cm
    
    irg_data = [
        ['Tranche de revenu mensuel', 'Taux'],
        ['0 - 1 000 000 GNF', '0%'],
        ['1 000 001 - 5 000 000 GNF', '5%'],
        ['5 000 001 - 10 000 000 GNF', '10%'],
        ['10 000 001 - 20 000 000 GNF', '15%'],
        ['Au-delà de 20 000 000 GNF', '20%'],
    ]
    
    table_irg = Table(irg_data, colWidths=[7*cm, 4*cm])
    table_irg.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 9),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fff3cd')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    tw, th = table_irg.wrapOn(p, width, height)
    table_irg.drawOn(p, 2*cm, y - th)
    y = y - th - 0.5*cm
    
    y = draw_text(y, "Note: L'IRG est calculé de manière progressive. Chaque tranche est imposée à son taux propre.")
    
    y = nouvelle_page()
    
    # === 4. TEMPS DE TRAVAIL ===
    y = draw_title(y, "4. GESTION DU TEMPS DE TRAVAIL")
    y = draw_text(y, "Le module Pointage permet de suivre les heures de travail des employés:")
    y = draw_bullet(y, "Saisie des pointages quotidiens (heure d'arrivée et de départ)")
    y = draw_bullet(y, "Calcul automatique des heures travaillées")
    y = draw_bullet(y, "Gestion des absences et retards")
    y = draw_bullet(y, "Rapports de présence par période")
    
    y -= 0.8*cm
    y = draw_title(y, "5. GESTION DES CONGÉS")
    y = draw_text(y, "Le module Congés permet de gérer les demandes et le suivi des congés:")
    y = draw_bullet(y, "Types de congés: Annuel, Maladie, Maternité, Paternité, Sans solde, Exceptionnel")
    y = draw_bullet(y, "Workflow de validation: Demande → Approbation → Congé effectif")
    y = draw_bullet(y, "Calcul automatique du solde de congés (2.5 jours/mois travaillé)")
    y = draw_bullet(y, "Historique complet des congés par employé")
    
    y -= 0.5*cm
    y = draw_subtitle(y, "Calcul des droits à congés")
    y = draw_text(y, "Selon le Code du Travail guinéen, chaque employé acquiert 2.5 jours ouvrables de congé par mois de travail effectif, soit 30 jours par an.")
    
    y -= 0.8*cm
    y = draw_title(y, "6. DÉCLARATIONS SOCIALES")
    y = draw_text(y, "Le module Déclarations génère automatiquement les déclarations obligatoires:")
    
    y -= 0.3*cm
    y = draw_subtitle(y, "6.1 Déclaration CNSS")
    y = draw_bullet(y, "Cotisation employé: 5% du salaire brut")
    y = draw_bullet(y, "Cotisation employeur: 18% du salaire brut")
    y = draw_bullet(y, "Total CNSS: 23% du salaire brut")
    y = draw_bullet(y, "Échéance: avant le 15 du mois suivant")
    
    y -= 0.3*cm
    y = draw_subtitle(y, "6.2 Déclaration IRG")
    y = draw_bullet(y, "Retenue à la source sur les salaires")
    y = draw_bullet(y, "Reversement au Trésor Public avant le 10 du mois suivant")
    
    y = nouvelle_page()
    
    # === 7. FORMATIONS ===
    y = draw_title(y, "7. GESTION DES FORMATIONS")
    y = draw_text(y, "Le module Formation permet de planifier et suivre les formations des employés:")
    y = draw_bullet(y, "Catalogue de formations (internes, externes, en ligne, certifiantes)")
    y = draw_bullet(y, "Planification des sessions avec dates, lieu et formateur")
    y = draw_bullet(y, "Inscription des employés aux sessions")
    y = draw_bullet(y, "Suivi des compétences acquises")
    
    y -= 0.8*cm
    y = draw_title(y, "8. RECRUTEMENT")
    y = draw_text(y, "Le module Recrutement permet de gérer le processus d'embauche:")
    y = draw_bullet(y, "Publication d'offres d'emploi")
    y = draw_bullet(y, "Réception et tri des candidatures")
    y = draw_bullet(y, "Planification des entretiens")
    y = draw_bullet(y, "Suivi du processus de recrutement")
    
    y -= 1*cm
    y = draw_title(y, "SUPPORT ET CONTACT")
    y = draw_text(y, "Pour toute question ou assistance technique:")
    y = draw_bullet(y, "Site web: www.guineerh.space")
    y = draw_bullet(y, "Email: support@guineerh.space")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Manuel_Utilisation_GestionnaireRH.pdf"'
    return response
