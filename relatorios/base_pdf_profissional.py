from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


def gerar_pdf_profissional(nome_arquivo, titulo, colunas, dados, logo_path=None):

    arquivo = f"{nome_arquivo}.pdf"
    doc = SimpleDocTemplate(arquivo)

    elementos = []

    styles = getSampleStyleSheet()

    # ==================================================
    # CABEÇALHO
    # ==================================================
    elementos.append(Paragraph(f"<b>{titulo}</b>", styles["Title"]))
    elementos.append(Spacer(1, 10))

    elementos.append(
        Paragraph(
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles["Normal"]
        )
    )

    elementos.append(Spacer(1, 20))

    # ==================================================
    # TABELA
    # ==================================================
    tabela_dados = [colunas] + dados

    tabela = Table(tabela_dados, repeatRows=1)

    tabela.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("FONTSIZE", (0, 0), (-1, -1), 9),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    elementos.append(tabela)

    # ==================================================
    # RODAPÉ
    # ==================================================
    elementos.append(Spacer(1, 20))
    elementos.append(
        Paragraph(
            "ERP - Relatório gerado automaticamente",
            styles["Normal"]
        )
    )

    doc.build(elementos)

    return arquivo