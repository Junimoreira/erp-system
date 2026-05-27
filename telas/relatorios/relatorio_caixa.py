import streamlit as st
import pandas as pd
from datetime import datetime

from database.connection import conectar


def tela_relatorio_caixa():

    st.title("📊 Relatório de Caixa")

    conn = conectar()

    if conn is None:
        st.error("Erro ao conectar com o banco.")
        return

    # =========================
    # FILTRO DE DATA (OPCIONAL MAS PROFISSIONAL)
    # =========================
    col1, col2 = st.columns(2)

    data_inicio = col1.date_input("Data inicial", datetime.today())
    data_fim = col2.date_input("Data final", datetime.today())

    try:

        query = """
            SELECT 
                id,
                descricao,
                tipo,
                valor,
                origem,
                data_lancamento,
                categoria_id
            FROM fluxo_caixa
            WHERE data_lancamento BETWEEN %s AND %s
            ORDER BY data_lancamento DESC
        """

        df = pd.read_sql(query, conn, params=[data_inicio, data_fim])

        if df.empty:
            st.warning("Nenhum lançamento encontrado no período selecionado.")
            return

        # =========================
        # KPIs SIMPLES
        # =========================
        entradas = df[df["tipo"] == "entrada"]["valor"].sum()
        saidas = df[df["tipo"] == "saida"]["valor"].sum()
        saldo = entradas - saidas

        col1, col2, col3 = st.columns(3)

        col1.metric("📥 Entradas", f"R$ {entradas:,.2f}")
        col2.metric("📤 Saídas", f"R$ {saidas:,.2f}")
        col3.metric("💰 Saldo", f"R$ {saldo:,.2f}")

        # =========================
        # TABELA
        # =========================
        st.subheader("📄 Lançamentos")

        st.dataframe(df, use_container_width=True)

        # =========================
        # EXPORTAÇÃO CSV
        # =========================
        csv = df.to_csv(index=False)

        st.download_button(
            "⬇️ Exportar CSV",
            csv,
            file_name="relatorio_caixa.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")