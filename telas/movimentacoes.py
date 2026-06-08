import streamlit as st
import pandas as pd

from database.movimentacoes_db import (
    listar_movimentacoes,
    resumo_movimentacoes
)


def tela_movimentacoes():

    st.title("💰 Movimentações Financeiras")

    # ==================================================
    # AVISO (se quiser manter como alerta inicial)
    # ==================================================
    # Se isso era só teste, pode remover depois
    # st.warning("A consulta geral de movimentações ainda não foi implementada.")

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

    # formatação visual do valor
    if "valor" in df.columns:
        df["valor"] = df["valor"].apply(lambda x: f"R$ {float(x):,.2f}" if x != "" else "")

    st.dataframe(df, use_container_width=True)