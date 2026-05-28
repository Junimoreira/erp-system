from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from datetime import datetime
import os


def gerar_pdf_base(nome_arquivo, titulo, dados, colunas):

    file_path = f"{nome_arquivo}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()

    # ==================================================
    # LOGO
    # ==================================================
    logo_path = "assets/logo1.png"

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=120, height=60)
        elements.append(logo)

    # ==================================================
    # CABEÇALHO
    # ==================================================
    elements.append(Paragraph("<b>SISTEMA ERP - RELATÓRIOS GERENCIAIS</b>", styles["Title"]))
    elements.append(Paragraph(titulo, styles["h2"]))

    data_geracao = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"Gerado em: {data_geracao}", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # ==================================================
    # TABELA
    # ==================================================
    table_data = [colunas] + dados

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)

    doc.build(elements)

    return file_path