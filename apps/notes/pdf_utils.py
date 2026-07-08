"""
Génération des bulletins de notes PDF pour les élèves.
Utilise ReportLab en mode paysage avec cadre, logo et style.
"""
import os
from io import BytesIO
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.db.models import Sum, Avg
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, Frame, PageTemplate, BaseDocTemplate, PageBreak
)
from reportlab.platypus.frames import Frame as RLFrame
from reportlab.platypus.doctemplate import PageTemplate as RLPageTemplate

# Couleurs du thème ADEIB
BLEU_ADEIB = '#0048AE'
BLEU_CLAIR = '#E8F0FE'
GRIS_CLAIR = '#F5F5F5'
GRIS_FONCE = '#333333'

WIDTH, HEIGHT = landscape(A4)  # 297mm x 210mm
MARGIN = 1.5 * cm


def mention_from_moyenne(moyenne):
    """Détermine la mention en fonction de la moyenne."""
    if moyenne is None:
        return ''
    m = float(moyenne)
    if m >= 18:
        return 'Excellent'
    elif m >= 16:
        return 'Très Bien'
    elif m >= 14:
        return 'Bien'
    elif m >= 12:
        return 'Assez Bien'
    elif m >= 10:
        return 'Passable'
    elif m >= 8:
        return 'Insuffisant'
    else:
        return 'Faible'


def observation_from_moyenne(moyenne):
    """Génère une observation automatique."""
    if moyenne is None:
        return ''
    m = float(moyenne)
    if m >= 16:
        return 'Félicitations ! Excellent travail, continuez ainsi.'
    elif m >= 14:
        return 'Très bon résultat. Encouragez l\'élève à maintenir ce niveau.'
    elif m >= 12:
        return 'Bon travail. Peut encore progresser avec plus d\'efforts.'
    elif m >= 10:
        return 'Résultats passables. Des efforts supplémentaires sont nécessaires.'
    elif m >= 8:
        return 'Résultats insuffisants. Un accompagnement renforcé est recommandé.'
    else:
        return 'Résultats très faibles. Une attention particulière est requise.'


def get_logo_path():
    """Retourne le chemin du logo ADEIB."""
    logo_path = os.path.join(settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT, 'img', 'logo_adeib.png')
    if os.path.exists(logo_path):
        return logo_path
    # Fallback
    alt_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_adeib.png')
    if os.path.exists(alt_path):
        return alt_path
    return None


def draw_border(canvas, doc):
    """Draw a decorative border frame on each page."""
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor(BLEU_ADEIB))
    canvas.setLineWidth(2)
    # Rectangle extérieur
    canvas.rect(MARGIN - 0.2 * cm, MARGIN - 0.2 * cm,
                WIDTH - 2 * MARGIN + 0.4 * cm, HEIGHT - 2 * MARGIN + 0.4 * cm)
    # Rectangle intérieur (filet)
    canvas.setLineWidth(0.5)
    canvas.rect(MARGIN - 0.1 * cm, MARGIN - 0.1 * cm,
                WIDTH - 2 * MARGIN + 0.2 * cm, HEIGHT - 2 * MARGIN + 0.2 * cm)
    canvas.restoreState()


def generate_bulletin_pdf(inscription, notes_data, session, config=None, message_directeur=''):
    """
    Génère le bulletin PDF pour un élève.

    Args:
        inscription: Instance Inscription
        notes_data: Liste de dicts avec 'matiere', 'note', 'coefficient'
        session: Instance SessionVacances
        config: Optionnel, BulletinConfig
        message_directeur: Message optionnel du directeur
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
    )

    styles = getSampleStyleSheet()
    story = []

    # Styles personnalisés
    title_style = ParagraphStyle(
        'TitleADEIB',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor(BLEU_ADEIB),
        spaceAfter=2 * mm,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    subtitle_style = ParagraphStyle(
        'SubtitleADEIB',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor(GRIS_FONCE),
        spaceAfter=1 * mm,
        alignment=TA_CENTER,
    )
    info_style = ParagraphStyle(
        'InfoADEIB',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor(GRIS_FONCE),
        spaceAfter=2 * mm,
        leading=14,
    )
    header_style = ParagraphStyle(
        'HeaderADEIB',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    )
    cell_style = ParagraphStyle(
        'CellADEIB',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        leading=14,
    )
    cell_left_style = ParagraphStyle(
        'CellLeftADEIB',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        leading=14,
    )
    mention_style = ParagraphStyle(
        'MentionADEIB',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor(BLEU_ADEIB),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=3 * mm,
    )
    obs_style = ParagraphStyle(
        'ObsADEIB',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor(GRIS_FONCE),
        leading=14,
        alignment=TA_LEFT,
    )
    message_style = ParagraphStyle(
        'MessageADEIB',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        leading=14,
        alignment=TA_LEFT,
        fontName='Helvetica-Oblique',
        leftIndent=10,
        rightIndent=10,
    )

    # --- Logo + En-tête ---
    logo_path = get_logo_path()
    if logo_path:
        img = Image(logo_path, width=50 * mm, height=50 * mm)
        img.hAlign = TA_CENTER
        story.append(img)

    story.append(Paragraph("ADEIB - Vacances", title_style))
    story.append(Paragraph("Association pour le Développement de l'Éducation et de l'Insertion au Bénin", subtitle_style))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("BULLETIN DE NOTES", ParagraphStyle(
        'BulletinTitle', parent=title_style, fontSize=22, spaceAfter=4 * mm
    )))
    story.append(Spacer(1, 2 * mm))

    # --- Informations élève ---
    eleve_info = [
        [Paragraph(f"<b>Nom :</b> {inscription.nom_eleve}", info_style),
         Paragraph(f"<b>Prénom :</b> {inscription.prenom_eleve}", info_style)],
        [Paragraph(f"<b>Classe :</b> {inscription.niveau.nom}", info_style),
         Paragraph(f"<b>Session :</b> {session.nom} ({session.annee})", info_style)],
        [Paragraph(f"<b>Parent/Tuteur :</b> {inscription.nom_parent}", info_style),
         Paragraph(f"<b>Tél. parent :</b> {inscription.telephone_parent}", info_style)],
    ]
    info_table = Table(eleve_info, colWidths=[WIDTH / 2 - MARGIN, WIDTH / 2 - MARGIN])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 4 * mm))

    # --- Tableau des notes ---
    table_data = [
        [Paragraph('N°', header_style),
         Paragraph('Matière', header_style),
         Paragraph('Note /20', header_style),
         Paragraph('Coefficient', header_style),
         Paragraph('Note Pondérée', header_style),
         Paragraph('Appréciation', header_style)],
    ]

    total_notes_ponderees = Decimal('0.0')
    total_coefficients = Decimal('0.0')
    nb_matieres = 0

    for i, nd in enumerate(notes_data, 1):
        matiere_nom = nd['matiere']
        note_val = nd['note']
        coef_val = nd['coefficient']
        note_pond = note_val * coef_val

        total_notes_ponderees += note_pond
        total_coefficients += coef_val
        nb_matieres += 1

        # Appréciation simple
        n = float(note_val)
        if n >= 16:
            aprec = 'Excellent'
        elif n >= 14:
            aprec = 'Très bien'
        elif n >= 12:
            aprec = 'Bien'
        elif n >= 10:
            aprec = 'Passable'
        elif n >= 8:
            aprec = 'Insuffisant'
        else:
            aprec = 'Faible'

        table_data.append([
            Paragraph(str(i), cell_style),
            Paragraph(matiere_nom, cell_left_style),
            Paragraph(str(note_val), cell_style),
            Paragraph(str(coef_val), cell_style),
            Paragraph(f"{note_pond:.1f}", cell_style),
            Paragraph(aprec, cell_style),
        ])

    # Ligne total
    moyenne = (total_notes_ponderees / total_coefficients) if total_coefficients > 0 else Decimal('0.0')
    table_data.append([
        Paragraph('<b>Total</b>', ParagraphStyle('TotalStyle', parent=cell_style, fontName='Helvetica-Bold')),
        Paragraph(f'<b>{nb_matieres} matières</b>', ParagraphStyle('TotalStyle', parent=cell_left_style, fontName='Helvetica-Bold')),
        Paragraph('', cell_style),
        Paragraph(f'<b>{total_coefficients:.1f}</b>', ParagraphStyle('TotalStyle', parent=cell_style, fontName='Helvetica-Bold')),
        Paragraph(f'<b>{total_notes_ponderees:.1f}</b>', ParagraphStyle('TotalStyle', parent=cell_style, fontName='Helvetica-Bold')),
        Paragraph('', cell_style),
    ])

    col_widths = [0.5 * cm, 5.5 * cm, 2.5 * cm, 2.5 * cm, 3.0 * cm, 5.0 * cm]
    notes_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style du tableau
    table_style_cmds = [
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BLEU_ADEIB)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Quadrillage
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#DDDDDD')),
        ('BOX', (0, 0), (-1, -2), 1, colors.HexColor(BLEU_ADEIB)),
        # Lignes alternées
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor(GRIS_CLAIR))
          for i in range(2, len(table_data) - 1, 2)],
        # Dernière ligne (total)
        ('BACKGROUND', (0, len(table_data) - 1), (-1, len(table_data) - 1), colors.HexColor(BLEU_CLAIR)),
        ('LINEABOVE', (0, len(table_data) - 1), (-1, len(table_data) - 1), 1.5, colors.HexColor(BLEU_ADEIB)),
        ('FONTNAME', (0, len(table_data) - 1), (-1, len(table_data) - 1), 'Helvetica-Bold'),
        # Alignements
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    notes_table.setStyle(TableStyle(table_style_cmds))
    story.append(notes_table)
    story.append(Spacer(1, 4 * mm))

    # --- Moyenne et Mention ---
    mention = mention_from_moyenne(moyenne)
    obs = observation_from_moyenne(moyenne)

    resume_data = [
        [Paragraph(f'<b>Moyenne Générale :</b> {moyenne:.1f}/20', mention_style),
         Paragraph(f'<b>Mention :</b> {mention}', mention_style)],
    ]
    resume_table = Table(resume_data, colWidths=[WIDTH / 2 - MARGIN, WIDTH / 2 - MARGIN])
    resume_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(BLEU_ADEIB)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(BLEU_CLAIR)),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(resume_table)
    story.append(Spacer(1, 3 * mm))

    # --- Observation ---
    if obs:
        obs_data = [
            [Paragraph(f'<b>Observation :</b>', obs_style)],
            [Paragraph(obs, obs_style)],
        ]
        obs_table = Table(obs_data, colWidths=[WIDTH - 2 * MARGIN])
        obs_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(GRIS_CLAIR)),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(obs_table)
        story.append(Spacer(1, 3 * mm))

    # --- Message du Directeur ---
    if message_directeur:
        msg_data = [
            [Paragraph('<b>Message du Comité Directeur :</b>', ParagraphStyle(
                'MsgTitle', parent=info_style, fontName='Helvetica-Bold', fontSize=10
            ))],
            [Paragraph(message_directeur, message_style)],
        ]
        msg_table = Table(msg_data, colWidths=[WIDTH - 2 * MARGIN])
        msg_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor(BLEU_ADEIB)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BLEU_CLAIR)),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(msg_table)
        story.append(Spacer(1, 5 * mm))

    # --- Signature ---
    date_str = datetime.now().strftime('%d/%m/%Y')
    sign_data = [
        [Paragraph(f'<b>Date :</b> {date_str}', info_style),
         Paragraph('<b>Le Secrétaire du Comité</b>', ParagraphStyle(
             'SignStyle', parent=info_style, alignment=TA_RIGHT
         ))],
    ]
    sign_table = Table(sign_data, colWidths=[WIDTH / 2 - MARGIN, WIDTH / 2 - MARGIN])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sign_table)

    # Génération
    doc.build(story, onFirstPage=draw_border, onLaterPages=draw_border)
    buffer.seek(0)
    return buffer


