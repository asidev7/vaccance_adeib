"""PDF generation utilities using ReportLab."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

PRIMARY = HexColor('#0048AE')
DARK = HexColor('#1F2937')
GRAY = HexColor('#6B7280')
LIGHT_GRAY = HexColor('#E5E7EB')
WHITE = HexColor('#FFFFFF')


def _create_doc(buffer):
    """Create a SimpleDocTemplate with standard margins."""
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )


def _header_table(enseignant_nom, title):
    """Create a standard header for PDF documents."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    data = [
        [Paragraph('ADEIB — Cours de Vacances', title_style)],
        [Paragraph(title, subtitle_style)],
        [Paragraph(f'<b>Enseignant :</b> {enseignant_nom}', ParagraphStyle(
            'Teacher', parent=styles['Normal'], fontSize=11, textColor=DARK, alignment=TA_LEFT
        ))],
    ]
    return data


def _draw_bordered_table(elements, data, col_widths=None):
    """Draw a clean flat table with primary-colored header."""
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, LIGHT_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, HexColor('#F9FAFB')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ])
    table.setStyle(style)
    elements.append(table)


def generate_bulletin_salaire(salaire):
    """Generate a salary bulletin PDF for a teacher.

    Returns BytesIO buffer containing the PDF.
    """
    buffer = BytesIO()
    doc = _create_doc(buffer)
    elements = []
    styles = getSampleStyleSheet()

    enseignant = salaire.enseignant
    enseignant_nom = enseignant.user.get_full_name() or enseignant.user.username

    # Header
    for row in _header_table(enseignant_nom, 'Bulletin de Salaire'):
        elements.append(row)
    elements.append(Spacer(1, 10 * mm))

    # Info table
    info_data = [
        ['Session', salaire.session.nom],
        ['Période', f'{salaire.session.date_debut.strftime("%d/%m/%Y")} — {salaire.session.date_fin.strftime("%d/%m/%Y")}'],
        ['Date d\'édition', salaire.date_calcul.strftime('%d/%m/%Y')],
    ]
    _draw_bordered_table(elements, info_data, col_widths=[60 * mm, 100 * mm])
    elements.append(Spacer(1, 8 * mm))

    # Salary details table
    salaire_data = [
        ['Désignation', 'Montant'],
        ['Heures effectuées', f'{salaire.nombre_heures_effectuees} h'],
        ['Taux horaire', f'{salaire.taux_horaire:,} FCFA'],
        ['Salaire brut', f'{salaire.montant_brut:,} FCFA'],
        ['Montant déjà versé', f'{salaire.montant_deja_verse:,} FCFA'],
        ['Reste à verser', f'{salaire.solde_restant:,} FCFA'],
    ]
    _draw_bordered_table(elements, salaire_data, col_widths=[100 * mm, 60 * mm])
    elements.append(Spacer(1, 10 * mm))

    # Versements detail
    if salaire.versements.exists():
        elements.append(Paragraph('<b>Historique des versements</b>', styles['Heading3']))
        elements.append(Spacer(1, 3 * mm))
        vers_data = [['Date', 'Montant', 'Mode']]
        for v in salaire.versements.all():
            vers_data.append([
                v.date_versement.strftime('%d/%m/%Y'),
                f'{v.montant:,} FCFA',
                v.get_mode_paiement_display(),
            ])
        _draw_bordered_table(elements, vers_data, col_widths=[50 * mm, 55 * mm, 55 * mm])

    # Footer
    elements.append(Spacer(1, 15 * mm))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'], fontSize=8, textColor=GRAY, alignment=TA_CENTER
    )
    elements.append(Paragraph('ADEIB — Association des Élèves et Étudiants d\'Illara Béninoise', footer_style))
    elements.append(Paragraph('Ce bulletin est généré automatiquement.', footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_bilan_financier(session, recettes, depenses, solde, details_recettes=None, details_depenses=None):
    """Generate a financial report PDF.

    Args:
        session: SessionVacances object
        recettes: total income (Decimal)
        depenses: total expenses (Decimal)
        solde: net balance (Decimal)
        details_recettes: list of dicts with 'libelle' and 'montant'
        details_depenses: list of dicts with 'libelle', 'categorie', and 'montant'

    Returns BytesIO buffer containing the PDF.
    """
    buffer = BytesIO()
    doc = _create_doc(buffer)
    elements = []
    styles = getSampleStyleSheet()

    # Header
    title_style = ParagraphStyle(
        'RapportTitle', parent=styles['Heading1'],
        fontSize=18, textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=4,
    )
    elements.append(Paragraph('ADEIB — Bilan Financier', title_style))
    elements.append(Paragraph(
        f'Session : {session.nom} ({session.date_debut.strftime("%d/%m/%Y")} — {session.date_fin.strftime("%d/%m/%Y")})',
        ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=GRAY, alignment=TA_CENTER, spaceAfter=12)
    ))
    elements.append(Spacer(1, 8 * mm))

    # Summary
    summary_data = [
        ['Rubrique', 'Montant (FCFA)'],
        ['Recettes totales (inscriptions)', f'{recettes:,}'],
        ['Dépenses totales', f'{depenses:,}'],
        ['Solde net', f'{solde:,}'],
    ]
    _draw_bordered_table(elements, summary_data, col_widths=[100 * mm, 60 * mm])
    elements.append(Spacer(1, 12 * mm))

    # Details recettes
    if details_recettes:
        elements.append(Paragraph('<b>Détail des recettes</b>', styles['Heading3']))
        elements.append(Spacer(1, 3 * mm))
        rec_data = [['Élève / Source', 'Montant']]
        for r in details_recettes:
            rec_data.append([r['libelle'], f"{r['montant']:,} FCFA"])
        _draw_bordered_table(elements, rec_data, col_widths=[100 * mm, 60 * mm])
        elements.append(Spacer(1, 12 * mm))

    # Details depenses
    if details_depenses:
        elements.append(Paragraph('<b>Détail des dépenses</b>', styles['Heading3']))
        elements.append(Spacer(1, 3 * mm))
        dep_data = [['Libellé', 'Catégorie', 'Montant']]
        for d in details_depenses:
            dep_data.append([d['libelle'], d.get('categorie', '—'), f"{d['montant']:,} FCFA"])
        _draw_bordered_table(elements, dep_data, col_widths=[70 * mm, 45 * mm, 45 * mm])

    # Footer
    elements.append(Spacer(1, 15 * mm))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'], fontSize=8, textColor=GRAY, alignment=TA_CENTER,
    )
    elements.append(Paragraph('ADEIB — Rapport généré automatiquement.', footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer
