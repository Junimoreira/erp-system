from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os


def gerar_pdf_base(nome_arquivo, titulo, dados, colunas, logo_path="assets/logo.png"):

    arquivo = f"{nome_arquivo}.pdf"
    c = canvas.Canvas(arquivo, pagesize=A4)

    largura, altura = A4

    # =========================
    # LOGO
    # =========================
    try:
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 40, altura - 100, width=80, height=60)
    except:
        pass

    # =========================
    # TÍTULO
    # =========================
    c.setFont("Helvetica-Bold", 14)
    c.drawString(140, altura - 80, titulo)

    c.setFont("Helvetica", 9)
    c.drawString(40, altura - 120, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # =========================
    # CABEÇALHO TABELA
    # =========================
    y = altura - 160
    x = 40

    c.setFont("Helvetica-Bold", 9)
    for col in colunas:
        c.drawString(x, y, str(col))
        x += 120

    y -= 20

    # =========================
    # DADOS
    # =========================
    c.setFont("Helvetica", 8)

    for linha in dados:
        x = 40
        for item in linha:
            c.drawString(x, y, str(item)[:20])
            x += 120
        y -= 15

        if y < 50:
            c.showPage()
            y = altura - 50

    c.save()
    return arquivo