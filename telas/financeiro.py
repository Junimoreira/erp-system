# telas/financeiro.py

import streamlit as st
import pandas as pd

from database.financeiro_db import (
    listar_contas_receber,
    receber_conta
)


def tela_financeiro():

    st.title("💰 Financeiro")

    abas = st.tabs([
        "📥 Contas a Receber"
    ])

    # ==================================================
    # CONTAS A RECEBER
    # ==================================================

    with abas[0]:

        st.subheader(
            "📥 Contas a Receber"
        )

        df = listar_contas_receber()

        # ==============================================
        # FILTRAR PENDENTES
        # ==============================================

        pendentes = df[
            df["status"] == "Pendente"
        ]

        if pendentes.empty:

            st.success(
                "✅ Nenhuma conta pendente."
            )

        else:

            # ==========================================
            # FORMATAR VALORES
            # ==========================================

            df_exibir = pendentes.copy()

            df_exibir["valor"] = df_exibir[
                "valor"
            ].map(
                lambda x: f"R$ {x:,.2f}"
            )

            st.dataframe(
                df_exibir,
                use_container_width=True
            )

            st.divider()

            st.subheader(
                "Receber Conta"
            )

            conta_id = st.selectbox(

                "Selecione a Conta",

                pendentes["id"],

                key="receber_conta"
            )

            # ==========================================
            # MOSTRAR DADOS DA CONTA
            # ==========================================

            conta = pendentes[
                pendentes["id"] == conta_id
            ].iloc[0]

            st.info(
                f"""
Cliente: {conta['cliente']}

Valor: R$ {conta['valor']:,.2f}

Vencimento: {conta['vencimento']}
                """
            )

            # ==========================================
            # RECEBER
            # ==========================================

            if st.button(
                "✅ Confirmar Recebimento",
                key="confirmar_recebimento"
            ):

                sucesso = receber_conta(
                    int(conta_id)
                )

                if sucesso:

                    st.success(
                        "✅ Conta recebida com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Erro ao receber conta."
                    )