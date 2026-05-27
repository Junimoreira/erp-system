import streamlit as st
import pandas as pd
from datetime import datetime

from database.connection import conectar


def tela_relatorio_vendas():

    st.title("📊 Relatório de Vendas")

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

        # 🔥 CONVERSÃO SEGURA (evita erro de SQL com datas)
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)

        query = """
        SELECT 
            v.id,
            c.nome AS cliente,
            p.nome AS produto,
            v.quantidade,
            v.valor_unitario,
            (v.quantidade * v.valor_unitario) AS total_venda,
            v.data_venda
        FROM vendas v
        JOIN clientes c ON c.id = v.cliente_id
        JOIN produtos p ON p.id = v.produto_id
        WHERE v.data_venda BETWEEN %s AND %s
        ORDER BY v.data_venda DESC
        """

        df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))

        if df.empty:
            st.warning("Nenhuma venda encontrada no período selecionado.")
            return

        # =========================
        # KPIs (RESUMO)
        # =========================
        total_vendas = len(df)
        total_faturado = df["total_venda"].sum()
        ticket_medio = total_faturado / total_vendas if total_vendas > 0 else 0

        col1, col2, col3 = st.columns(3)

        col1.metric("📦 Vendas", total_vendas)
        col2.metric("💰 Faturamento", f"R$ {total_faturado:,.2f}")
        col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}")

        # =========================
        # TABELA DETALHADA
        # =========================
        st.subheader("📄 Detalhamento das Vendas")
        st.dataframe(df, use_container_width=True)

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

    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")