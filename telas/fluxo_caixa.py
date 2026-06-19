import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database.fluxo_caixa_db import (
    listar_pagar_previsto,
    listar_receber_previsto,
    resumo_fluxo_caixa_previsto,
    resumo_geral_fluxo
)


# ==================================================
# FORMATAR MOEDA
# ==================================================
def moeda(valor):

    try:
        return f"R$ {float(valor):,.2f}"
    except Exception:
        return "R$ 0,00"


# ==================================================
# FORMATAR DATAFRAME
# ==================================================
def formatar_valores(df):

    if df.empty:
        return df

    df_formatado = df.copy()

    for coluna in ["valor", "total_receber", "total_pagar", "saldo_previsto", "saldo_acumulado"]:
        if coluna in df_formatado.columns:
            df_formatado[coluna] = df_formatado[coluna].apply(moeda)

    if "mes" in df_formatado.columns:
        df_formatado["mes"] = pd.to_datetime(df_formatado["mes"]).dt.strftime("%m/%Y")

    if "vencimento" in df_formatado.columns:
        df_formatado["vencimento"] = pd.to_datetime(df_formatado["vencimento"]).dt.strftime("%d/%m/%Y")

    return df_formatado


# ==================================================
# TELA FLUXO DE CAIXA
# ==================================================
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
            value=hoje
        )

    with col_filtro2:
        data_fim = st.date_input(
            "Data final",
            value=data_padrao_fim
        )

    if data_fim < data_inicio:
        st.warning("A data final não pode ser menor que a data inicial.")
        return

    st.divider()

    resumo_geral = resumo_geral_fluxo(data_inicio, data_fim)
    resumo_mensal = resumo_fluxo_caixa_previsto(data_inicio, data_fim)

    contas_pagar = listar_pagar_previsto(data_inicio, data_fim)
    contas_receber = listar_receber_previsto(data_inicio, data_fim)

    # ==================================================
    # CARDS
    # ==================================================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "📥 Total a Receber",
        moeda(resumo_geral["total_receber"])
    )

    col2.metric(
        "📤 Total a Pagar",
        moeda(resumo_geral["total_pagar"])
    )

    col3.metric(
        "💰 Saldo Previsto",
        moeda(resumo_geral["saldo_previsto"])
    )

    col4.metric(
        "📊 Saldo Acumulado",
        moeda(resumo_geral["saldo_acumulado"])
    )

    st.divider()

    abas = st.tabs([
        "📅 Resumo Mensal",
        "📥 A Receber",
        "📤 A Pagar"
    ])

    # ==================================================
    # RESUMO MENSAL
    # ==================================================
    with abas[0]:

        st.subheader("📅 Resumo Mensal Previsto")

        if resumo_mensal.empty:
            st.info("Nenhuma previsão encontrada para o período selecionado.")

        else:
            st.dataframe(
                formatar_valores(resumo_mensal),
                use_container_width=True,
                hide_index=True
            )

            st.bar_chart(
                resumo_mensal.set_index("mes")[["total_receber", "total_pagar"]]
            )

            st.line_chart(
                resumo_mensal.set_index("mes")["saldo_acumulado"]
            )

    # ==================================================
    # CONTAS A RECEBER
    # ==================================================
    with abas[1]:

        st.subheader("📥 Contas a Receber em Aberto")

        if contas_receber.empty:
            st.info("Nenhuma conta a receber em aberto no período.")

        else:
            st.dataframe(
                formatar_valores(contas_receber),
                use_container_width=True,
                hide_index=True
            )

    # ==================================================
    # CONTAS A PAGAR
    # ==================================================
    with abas[2]:

        st.subheader("📤 Contas a Pagar em Aberto")

        if contas_pagar.empty:
            st.info("Nenhuma conta a pagar em aberto no período.")

        else:
            st.dataframe(
                formatar_valores(contas_pagar),
                use_container_width=True,
                hide_index=True
            )