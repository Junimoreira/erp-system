import streamlit as st
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from database.connection import conectar


def buscar_vendas(data_inicio, data_fim):

    conn = conectar()

    if conn is None:
        return None

    query = """
        SELECT
            v.id,
            v.data_venda,
            p.nome AS produto,
            iv.quantidade,
            iv.preco_unitario,
            p.custo
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.venda_id
        JOIN produtos p ON p.id = iv.produto_id
        WHERE DATE(v.data_venda) BETWEEN %s AND %s
        ORDER BY v.data_venda DESC
    """

    try:
        import pandas as pd
        df = pd.read_sql(query, conn, params=(data_inicio, data_fim))

        # =========================
        # CÁLCULOS
        # =========================
        df["total_venda"] = df["quantidade"] * df["preco_unitario"]
        df["custo_total"] = df["quantidade"] * df["custo"]
        df["lucro"] = df["total_venda"] - df["custo_total"]

        return df

    except Exception as e:
        st.error(f"Erro ao buscar vendas: {e}")
        return None

    finally:
        conn.close()


def gerar_pdf_vendas(df, data_inicio, data_fim):

    nome_arquivo = "relatorio_vendas.pdf"

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    # =========================
    # TÍTULO
    # =========================
    elementos.append(Paragraph("📊 RELATÓRIO DE VENDAS COM LUCRO", styles["Title"]))
    elementos.append(Spacer(1, 10))

    elementos.append(Paragraph(
        f"Período: {data_inicio} até {data_fim}",
        styles["Normal"]
    ))

    elementos.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    ))

    elementos.append(Spacer(1, 20))

    # =========================
    # INDICADORES
    # =========================
    total_vendas = df["total_venda"].sum()
    total_lucro = df["lucro"].sum()
    margem = (total_lucro / total_vendas * 100) if total_vendas > 0 else 0

    elementos.append(Paragraph(f"💰 Total Vendido: R$ {total_vendas:.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"📈 Lucro Total: R$ {total_lucro:.2f}", styles["Normal"]))
    elementos.append(Paragraph(f"📊 Margem: {margem:.1f}%", styles["Normal"]))

    elementos.append(Spacer(1, 20))

    # =========================
    # TABELA
    # =========================
    dados = [[
        "Venda",
        "Data",
        "Produto",
        "Qtd",
        "Preço",
        "Total",
        "Lucro"
    ]]

    for _, row in df.iterrows():

        dados.append([
            row["id"],
            row["data_venda"].strftime("%d/%m/%Y"),
            row["produto"],
            row["quantidade"],
            f"R$ {row['preco_unitario']:.2f}",
            f"R$ {row['total_venda']:.2f}",
            f"R$ {row['lucro']:.2f}"
        ])

    tabela = Table(dados, repeatRows=1)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elementos.append(tabela)

    # =========================
    # RANKING PRODUTOS
    # =========================
    ranking = df.groupby("produto")["quantidade"].sum().sort_values(ascending=False)

    elementos.append(Spacer(1, 30))
    elementos.append(Paragraph("🏆 Produtos Mais Vendidos", styles["Heading2"]))

    for produto, qtd in ranking.items():
        elementos.append(Paragraph(f"{produto} - {qtd} vendidos", styles["Normal"]))

    doc.build(elementos)

    return nome_arquivo


# ==================================================
# TELA STREAMLIT
# ==================================================
def tela_relatorio_vendas_lucro():

    st.title("📊 Relatório de Vendas com Lucro")

    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input("Data inicial")

    with col2:
        data_fim = st.date_input("Data final")

    if st.button("📄 Gerar Relatório"):

        df = buscar_vendas(data_inicio, data_fim)

        if df is None or df.empty:
            st.warning("Nenhuma venda encontrada.")
            return

        # =========================
        # INDICADORES NA TELA
        # =========================
        total_vendas = df["total_venda"].sum()
        total_lucro = df["lucro"].sum()

        col1, col2 = st.columns(2)

        col1.metric("💰 Total Vendido", f"R$ {total_vendas:,.2f}")
        col2.metric("📈 Lucro", f"R$ {total_lucro:,.2f}")

        st.dataframe(df, use_container_width=True)

        # PDF
        arquivo = gerar_pdf_vendas(df, data_inicio, data_fim)

        with open(arquivo, "rb") as f:
            st.download_button(
                "📥 Baixar PDF",
                f,
                file_name="relatorio_vendas.pdf",
                mime="application/pdf"
            )