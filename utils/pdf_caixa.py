from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from reportlab.lib.pagesizes import A4

from reportlab.platypus.flowables import (
    PageBreak
)

from datetime import datetime


# ==================================================
# GERAR PDF RELATÓRIO CAIXA
# ==================================================
def gerar_pdf_caixa(df, caminho_pdf):

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4
    )

    elementos = []

    estilos = getSampleStyleSheet()

    titulo = Paragraph(
        "RELATÓRIO DE CAIXA ERP",
        estilos["Title"]
    )

    elementos.append(titulo)

    elementos.append(
        Spacer(1, 20)
    )

    data = [[

        "ID",
        "Usuário",
        "Abertura",
        "Fechamento",
        "Entradas",
        "Saídas",
        "Saldo Final",
        "Diferença",
        "Status"

    ]]

    # ==================================================
    # DADOS
    # ==================================================
    for _, row in df.iterrows():

        data.append([

            str(row["id"]),

            str(row["usuario"]),

            str(
                row["data_abertura"]
            )[:16],

            str(
                row["data_fechamento"]
            )[:16],

            f'R$ {float(row["entradas"]):,.2f}',

            f'R$ {float(row["saidas"]):,.2f}',

            f'R$ {float(row["saldo_final"]):,.2f}',

            f'R$ {float(row["diferenca"]):,.2f}',

            str(row["status"])

        ])

    tabela = Table(data)

    tabela.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("FONTSIZE", (0, 0), (-1, -1), 8),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

    ]))

    elementos.append(tabela)

    elementos.append(
        Spacer(1, 20)
    )

    rodape = Paragraph(

        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",

        estilos["Normal"]

    )

    elementos.append(rodape)

    doc.build(elementos)