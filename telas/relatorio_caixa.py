import streamlit as st
import pandas as pd

from database.connection import conectar


# ==================================================
# RELATÓRIO CAIXA
# ==================================================
def tela_relatorio_caixa():

    st.title("💰 Relatório de Caixa")

    conn = None

    try:

        conn = conectar()

        if conn is None:

            st.error("Erro ao conectar banco.")

            return

        # ==================================================
        # CONSULTA
        # ==================================================
        query = """
            SELECT
                id,
                usuario,
                data_abertura,
                data_fechamento,
                saldo_inicial,
                status
            FROM caixa
            ORDER BY id DESC
        """

        df = pd.read_sql(query, conn)

        # ==================================================
        # SEM DADOS
        # ==================================================
        if df.empty:

            st.info("Nenhum caixa encontrado.")

            return

        # ==================================================
        # TRATAMENTO DADOS
        # ==================================================
        numeric_cols = [
            "saldo_inicial"
        ]

        for col in numeric_cols:

            if col in df.columns:

                df[col] = pd.to_numeric(
                    df[col],
                    errors="coerce"
                ).fillna(0)

        # ==================================================
        # TABELA
        # ==================================================
        st.dataframe(
            df,
            use_container_width=True,
            height=600
        )

        st.divider()

	historico = listar_historico_caixa()

            st.write(historico)

            if historico is None or historico.empty:

        # ==================================================
        # RESUMO
        # ==================================================
        st.subheader("📊 Resumo")

        total_saldo = float(
            df["saldo_inicial"].sum()
        )

        st.metric(
            "💰 Total Saldo Inicial",
            f"R$ {total_saldo:,.2f}"
        )

    except Exception as erro:

        st.error(
            f"Erro relatório caixa: {erro}"
        )

    finally:

        if conn:

            conn.close()