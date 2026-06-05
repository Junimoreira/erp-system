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
        return None

    query = """
        SELECT id, nome, custo, preco, estoque
        FROM produtos
        ORDER BY nome
    """

    try:
        import pandas as pd
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao buscar produtos: {e}")
        return None

    finally:
        conn.close()

    if df.empty:
        st.warning("Nenhum produto encontrado.")
        return None

    # ==========================================
    # CAMPOS CALCULADOS
    # ==========================================
    df["valor_estoque"] = df["custo"] * df["estoque"]
    df["margem"] = ((df["preco"] - df["custo"]) / df["custo"]) * 100

    total_estoque = df["valor_estoque"].sum()

    nome_arquivo = "relatorio_produtos.pdf"

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    elementos = []

    styles = getSampleStyleSheet()

    # ==========================================
    # LOGO
    # ==========================================
    try:
        logo = Image("assets/Logo1.png", width=120, height=60)
        elementos.append(logo)
    except:
        pass

    # ==========================================
    # TÍTULO
    # ==========================================
    elementos.append(Paragraph("📦 RELATÓRIO DE PRODUTOS", styles["Title"]))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 20))

    # ==========================================
    # TABELA
    # ==========================================
    dados = [[
        "ID", "Produto", "Custo", "Preço",
        "Estoque", "Valor Estoque", "Margem"
    ]]

    for _, row in df.iterrows():

        dados.append([
            row["id"],
            row["nome"],
            f"R$ {row['custo']:.2f}",
            f"R$ {row['preco']:.2f}",
            row["estoque"],
            f"R$ {row['valor_estoque']:.2f}",
            f"{row['margem']:.1f}%"
        ])

    # ==========================================
    # TOTAL FINAL
    # ==========================================
    dados.append([
        "",
        "TOTAL",
        "",
        "",
        "",
        f"R$ {total_estoque:.2f}",
        ""
    ])

    tabela = Table(dados, repeatRows=1)

    tabela.setStyle(TableStyle([

        # Cabeçalho
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        # Corpo
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),

        # Linhas alternadas
        ("BACKGROUND", (0, 1), (-1, -2), colors.whitesmoke),

        # TOTAL
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

    ]))

    # ==========================================
    # ALERTA ESTOQUE BAIXO
    # ==========================================
    produtos_baixo = df[df["estoque"] <= 5]

    if not produtos_baixo.empty:

        elementos.append(Paragraph("⚠️ Produtos com estoque baixo", styles["Heading3"]))
        elementos.append(Spacer(1, 10))

        for _, row in produtos_baixo.iterrows():
            elementos.append(Paragraph(f"- {row['nome']} (Estoque: {row['estoque']})", styles["Normal"]))

        elementos.append(Spacer(1, 20))

    elementos.append(tabela)

    doc.build(elementos)

    return nome_arquivo


def tela_relatorio_produtos_pdf():

    st.title("📦 Relatório de Produtos (PDF Profissional)")

    if st.button("📄 Gerar Relatório"):

        arquivo = gerar_pdf_produtos()

        if arquivo:

            with open(arquivo, "rb") as f:
                st.download_button(
                    "📥 Baixar PDF",
                    f,
                    file_name="relatorio_produtos.pdf",
                    mime="application/pdf"
                )