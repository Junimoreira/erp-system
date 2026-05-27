import streamlit as st
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from database.connection import conectar


def gerar_pdf_produtos():

    conn = conectar()

    if conn is None:
        st.error("Erro ao conectar com o banco.")
        return

    query = """
        SELECT id, nome, preco, estoque
        FROM produtos
        ORDER BY nome
    """

    df = None

    try:
        import pandas as pd
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")
        return

    if df.empty:
        st.warning("Nenhum produto encontrado.")
        return

    nome_arquivo = "relatorio_produtos.pdf"

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    elementos = []

    styles = getSampleStyleSheet()

    # =========================
    # LOGO
    # =========================
    try:
        logo = Image("assets/Logo1.png", width=120, height=60)
        elementos.append(logo)
    except:
        pass

    # =========================
    # TÍTULO
    # =========================
    titulo = Paragraph(
        "📦 RELATÓRIO DE PRODUTOS",
        styles["Title"]
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 12))

    # =========================
    # DATA GERAÇÃO
    # =========================
    data = Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    )

    elementos.append(data)
    elementos.append(Spacer(1, 20))

    # =========================
    # DADOS DA TABELA
    # =========================
    dados = [["ID", "Produto", "Preço", "Estoque"]]

    for _, row in df.iterrows():
        dados.append([
            row["id"],
            row["nome"],
            f"R$ {row['preco']:.2f}",
            row["estoque"]
        ])

    tabela = Table(dados)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
    ]))

    elementos.append(tabela)

    doc.build(elementos)

    return nome_arquivo


def tela_relatorio_produtos_pdf():

    st.title("📦 Relatório de Produtos (PDF)")

    arquivo = gerar_pdf_produtos()

    if arquivo:
        with open(arquivo, "rb") as f:
            st.download_button(
                "📥 Baixar PDF",
                f,
                file_name="relatorio_produtos.pdf",
                mime="application/pdf"
            )