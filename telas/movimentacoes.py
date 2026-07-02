import streamlit as st

from database.movimentacoes_db import (
    listar_movimentacoes,
    resumo_movimentacoes
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)


def tela_movimentacoes():

    st.title("💰 Movimentações Financeiras")

    dados = resumo_movimentacoes()

    col1, col2, col3 = st.columns(3)

    col1.metric("📥 Entradas", formatar_moeda(dados["entradas"]))
    col2.metric("📤 Saídas", formatar_moeda(dados["saidas"]))
    col3.metric("💰 Saldo", formatar_moeda(dados["saldo"]))

    st.divider()

    st.subheader("📋 Histórico de Movimentações")

    df = listar_movimentacoes()

    if df.empty:
        st.info("Nenhuma movimentação encontrada.")
        return

    df_exibicao = formatar_dataframe_brasil(
        df,
        com_hora=True,
        moedas=True
    )

    st.dataframe(df_exibicao, use_container_width=True)