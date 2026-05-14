# telas/contas_receber.py

import streamlit as st
import pandas as pd

from database.financeiro_db import (
    listar_contas_receber,
    receber_conta
)


def tela_contas_receber():

    st.title("📥 Contas a Receber")

    # ==================================================
    # CARREGAR DADOS
    # ==================================================

    df = listar_contas_receber()

    # ==================================================
    # FILTROS
    # ==================================================

    st.subheader("Filtros")

    status_filtro = st.selectbox(

        "Status",

        [
            "Todos",
            "Pendente",
            "Pago"
        ],

        key="filtro_status_receber"
    )

    cliente_filtro = st.text_input(
        "Buscar Cliente"
    )

    # ==================================================
    # APLICAR FILTROS
    # ==================================================

    if status_filtro != "Todos":

        df = df[
            df["status"] == status_filtro
        ]

    if cliente_filtro:

        df = df[
            df["cliente"].str.contains(
                cliente_filtro,
                case=False,
                na=False
            )
        ]

    # ==================================================
    # VALIDAR
    # ==================================================

    if df.empty:

        st.info(
            "Nenhuma conta encontrada."
        )

        return

    # ==================================================
    # FORMATAR
    # ==================================================

    df_exibir = df.copy()

    df_exibir["valor"] = df_exibir[
        "valor"
    ].map(
        lambda x: f"R$ {x:,.2f}"
    )

    st.divider()

    st.subheader(
        "Lista de Contas"
    )

    st.dataframe(
        df_exibir,
        use_container_width=True
    )

    # ==================================================
    # CONTAS PENDENTES
    # ==================================================

    pendentes = df[
        df["status"] == "Pendente"
    ]

    if pendentes.empty:

        st.success(
            "✅ Nenhuma conta pendente."
        )

        return

    # ==================================================
    # RECEBER CONTA
    # ==================================================

    st.divider()

    st.subheader(
        "Receber Conta"
    )

    conta_id = st.selectbox(

        "Selecione a Conta",

        pendentes["id"],

        key="select_receber_conta"
    )

    conta = pendentes[
        pendentes["id"] == conta_id
    ].iloc[0]

    st.info(
        f"""
Cliente: {conta['cliente']}

Descrição: {conta['descricao']}

Valor: R$ {conta['valor']:,.2f}

Vencimento: {conta['vencimento']}
        """
    )

    # ==================================================
    # BOTÃO RECEBER
    # ==================================================

    if st.button(
        "✅ Confirmar Recebimento",
        key="botao_receber_conta"
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