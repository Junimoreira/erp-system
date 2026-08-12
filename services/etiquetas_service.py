from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128


ETIQUETA_LARGURA = 50 * mm
ETIQUETA_ALTURA = 30 * mm

MARGEM_ESQUERDA = 5 * mm
MARGEM_SUPERIOR = 13.5 * mm

COLUNAS = 4
LINHAS = 9
ETIQUETAS_POR_PAGINA = COLUNAS * LINHAS


def _texto_limitado(texto, limite):
    texto = str(texto or "").strip()
    if len(texto) <= limite:
        return texto
    return texto[: limite - 3] + "..."


def _desenhar_etiqueta(
    pdf,
    x,
    y,
    nome_produto,
    codigo_barras,
    preco,
    mostrar_preco
):
    largura = ETIQUETA_LARGURA
    altura = ETIQUETA_ALTURA

    pdf.setLineWidth(0.2)
    pdf.rect(x, y, largura, altura)

    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawCentredString(
        x + largura / 2,
        y + altura - 5 * mm,
        "VERDE INFÂNCIA"
    )

    nome_exibicao = _texto_limitado(nome_produto, 31)

    pdf.setFont("Helvetica-Bold", 6.5)
    pdf.drawCentredString(
        x + largura / 2,
        y + altura - 9 * mm,
        nome_exibicao
    )

    codigo = str(codigo_barras).strip()

    barcode = code128.Code128(
        codigo,
        barHeight=8 * mm,
        barWidth=0.28 * mm,
        humanReadable=False
    )

    barcode_x = x + (largura - barcode.width) / 2
    barcode_y = y + 8 * mm
    barcode.drawOn(pdf, barcode_x, barcode_y)

    pdf.setFont("Helvetica", 6.5)
    pdf.drawCentredString(
        x + largura / 2,
        y + 5.5 * mm,
        codigo
    )

    if mostrar_preco:
        preco_formatado = (
            f"R$ {float(preco):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(
            x + largura / 2,
            y + 2 * mm,
            preco_formatado
        )


def gerar_pdf_etiquetas_produto(
    nome_produto,
    codigo_barras,
    preco,
    quantidade=1,
    mostrar_preco=True
):
    if not codigo_barras:
        raise ValueError("Produto sem código de barras.")

    quantidade = int(quantidade)

    if quantidade < 1:
        raise ValueError(
            "A quantidade deve ser maior que zero."
        )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, pagina_altura = A4

    for indice in range(quantidade):
        posicao_pagina = indice % ETIQUETAS_POR_PAGINA

        if posicao_pagina == 0 and indice > 0:
            pdf.showPage()

        linha = posicao_pagina // COLUNAS
        coluna = posicao_pagina % COLUNAS

        x = MARGEM_ESQUERDA + coluna * ETIQUETA_LARGURA

        y_topo = (
            pagina_altura
            - MARGEM_SUPERIOR
            - linha * ETIQUETA_ALTURA
        )

        y = y_topo - ETIQUETA_ALTURA

        _desenhar_etiqueta(
            pdf=pdf,
            x=x,
            y=y,
            nome_produto=nome_produto,
            codigo_barras=codigo_barras,
            preco=preco,
            mostrar_preco=mostrar_preco
        )

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
