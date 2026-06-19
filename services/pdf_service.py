from io import BytesIO
from datetime import datetime
import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet


def gerar_pdf_relatorio(titulo, df, resumo=None):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    elementos = []
    estilos = getSampleStyleSheet()

    logo_path = os.path.join(os.getcwd(), "assets", "logo1.png")

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=90, height=60)
        elementos.append(logo)

    elementos.append(Paragraph(f"<b>{titulo}</b>", estilos["Title"]))
    elementos.append(Paragraph(
        f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["Normal"]
    ))

    elementos.append(Spacer(1, 12))

    if resumo:
        for chave, valor in resumo.items():
            elementos.append(Paragraph(f"<b>{chave}:</b> {valor}", estilos["Normal"]))

        elementos.append(Spacer(1, 12))

    if df.empty:
        elementos.append(Paragraph("Nenhum registro encontrado.", estilos["Normal"]))
    else:
        dados = [list(df.columns)] + df.astype(str).values.tolist()

        tabela = Table(dados, repeatRows=1)

        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#008ACD")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ]))

        elementos.append(tabela)

    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(
        "Verde Infância - Relatório gerado pelo ERP",
        estilos["Normal"]
    ))

    doc.build(elementos)

    buffer.seek(0)
    return buffer