import streamlit as st
from datetime import date, timedelta

from database.fluxo_caixa_db import (
    listar_pagar_previsto,
    listar_receber_previsto,
    resumo_fluxo_caixa_previsto,
    resumo_geral_fluxo
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)


def tela_fluxo_caixa():

    st.title("📊 Fluxo de Caixa Previsto")

    st.info(
        "Esta tela mostra uma previsão financeira com base nas contas a pagar "
        "e contas a receber que ainda estão em aberto."
    )

    hoje = date.today()
    data_padrao_fim = hoje + timedelta(days=180)

    col_filtro1, col_filtro2 = st.columns(2)

    with col_filtro1:
        data_inicio = st.date_input(
            "Data inicial",
            value=hoje,
            format="DD/MM/YYYY"
        )

    with col_filtro2:
        data_fim = st.date_input(
            "Data final",
            value=data_padrao_fim,
            format="DD/MM/YYYY"
        )

    if data_fim < data_inicio:
        st.warning("A data final não pode ser menor que a data inicial.")
        return

    st.divider()

    resumo_geral = resumo_geral_fluxo(data_inicio, data_fim)
    resumo_mensal = resumo_fluxo_caixa_previsto(data_inicio, data_fim)

    contas_pagar = listar_pagar_previsto(data_inicio, data_fim)
    contas_receber = listar_receber_previsto(data_inicio, data_fim)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "📥 Total a Receber",
        formatar_moeda(resumo_geral["total_receber"])
    )

    col2.metric(
        "📤 Total a Pagar",
        formatar_moeda(resumo_geral["total_pagar"])
    )

    col3.metric(
        "💰 Saldo Previsto",
        formatar_moeda(resumo_geral["saldo_previsto"])
    )

    col4.metric(
        "📊 Saldo Acumulado",
        formatar_moeda(resumo_geral["saldo_acumulado"])
    )

    st.divider()

    abas = st.tabs([
        "📅 Resumo Mensal",
        "📥 A Receber",
        "📤 A Pagar"
    ])

    with abas[0]:

        st.subheader("📅 Resumo Mensal Previsto")

        if resumo_mensal.empty:
            st.info("Nenhuma previsão encontrada para o período selecionado.")

        else:
            resumo_exibicao = formatar_dataframe_brasil(
                resumo_mensal,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                resumo_exibicao,
                use_container_width=True,
                hide_index=True
            )

            st.bar_chart(
                resumo_mensal.set_index("mes")[["total_receber", "total_pagar"]]
            )

            st.line_chart(
                resumo_mensal.set_index("mes")["saldo_acumulado"]
            )

    with abas[1]:

        st.subheader("📥 Contas a Receber em Aberto")

        if contas_receber.empty:
            st.info("Nenhuma conta a receber em aberto no período.")

        else:
            contas_receber_exibicao = formatar_dataframe_brasil(
                contas_receber,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                contas_receber_exibicao,
                use_container_width=True,
                hide_index=True
            )

    with abas[2]:

        st.subheader("📤 Contas a Pagar em Aberto")

        if contas_pagar.empty:
            st.info("Nenhuma conta a pagar em aberto no período.")

        else:
            contas_pagar_exibicao = formatar_dataframe_brasil(
                contas_pagar,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                contas_pagar_exibicao,
                use_container_width=True,
                hide_index=True
            )