import streamlit as st
#from database.movimentacoes_db import listar_movimentacoes, resumo_movimentacoes
import pandas as pd


def tela_movimentacoes():

    st.title("💰 Movimentações Financeiras")

    # ==================================================
    # RESUMO
    # ==================================================
    dados = resumo_movimentacoes()

    col1, col2, col3 = st.columns(3)

    col1.metric("📥 Entradas", f"R$ {dados['entradas']:,.2f}")
    col2.metric("📤 Saídas", f"R$ {dados['saidas']:,.2f}")
    col3.metric("💰 Saldo", f"R$ {dados['saldo']:,.2f}")

    st.divider()

    # ==================================================
    # LISTA COMPLETA
    # ==================================================
    st.subheader("📋 Histórico de Movimentações")

    df = listar_movimentacoes()

    if df.empty:
        st.info("Nenhuma movimentação encontrada.")
        return

    # formatar visual
    df["valor"] = df["valor"].apply(lambda x: f"R$ {x:,.2f}")

    st.dataframe(df, use_container_width=True)