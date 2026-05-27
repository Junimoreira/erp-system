import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# ==================================================
# AJUSTE DE PATH (TEM QUE VIR ANTES DOS IMPORTS LOCAIS)
# ==================================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from database.connection import conectar
from relatorios.relatorio_vendas_lucro import gerar_pdf_vendas_lucro


def tela_relatorio_vendas_lucro():

    st.title("📊 Relatório de Vendas com Lucro")

    # =========================
    # CONEXÃO COM BANCO
    # =========================
    conn = conectar()

    if conn is None:
        st.error("Erro ao conectar com o banco de dados.")
        return

    # =========================
    # FILTRO DE DATAS
    # =========================
    col1, col2 = st.columns(2)

    data_inicio = col1.date_input("Data inicial", datetime.today())
    data_fim = col2.date_input("Data final", datetime.today())

    try:

        query = """
        SELECT 
            v.id,
            c.nome AS cliente,
            v.produto,
            v.quantidade,
            v.valor_unitario,
            (v.quantidade * v.valor_unitario) AS total_venda,
            v.data_venda
        FROM vendas v
        JOIN clientes c ON c.id = v.cliente_id
        WHERE v.data_venda BETWEEN %s AND %s
        ORDER BY v.data_venda DESC
        """

        df = pd.read_sql(query, conn, params=[data_inicio, data_fim])

        if df.empty:
            st.warning("Nenhuma venda encontrada no período selecionado.")
            return

        # =========================
        # KPIs
        # =========================
        total_vendas = len(df)
        total_faturado = df["total_venda"].sum()
        ticket_medio = total_faturado / total_vendas if total_vendas > 0 else 0

        col1, col2, col3 = st.columns(3)

        col1.metric("📦 Vendas", total_vendas)
        col2.metric("💰 Faturamento", f"R$ {total_faturado:,.2f}")
        col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}")

        # =========================
        # DETALHAMENTO
        # =========================
        st.subheader("📄 Detalhamento das Vendas")
        st.dataframe(df, use_container_width=True)

        # =========================
        # PRODUTOS MAIS VENDIDOS
        # =========================
        st.subheader("📦 Produtos mais vendidos")

        top_produtos = (
            df.groupby("produto")["quantidade"]
            .sum()
            .reset_index()
            .sort_values("quantidade", ascending=False)
        )

        st.dataframe(top_produtos, use_container_width=True)

        # =========================
        # EXPORTAÇÃO CSV
        # =========================
        csv = df.to_csv(index=False)

        st.download_button(
            "⬇️ Exportar CSV",
            csv,
            file_name="relatorio_vendas.csv",
            mime="text/csv"
        )

        # =========================
        # PDF
        # =========================
        if st.button("📄 Gerar PDF do Relatório"):
            arquivo = gerar_pdf_vendas_lucro()

            if arquivo:
                with open(arquivo, "rb") as f:
                    st.download_button(
                        "📥 Baixar PDF",
                        f,
                        file_name="relatorio_vendas_lucro.pdf",
                        mime="application/pdf"
                    )

    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")