import streamlit as st
import pandas as pd
from database.connection import conectar


# ==================================================
# RELATÓRIO DE PRODUTOS
# ==================================================
def relatorio_produtos():

    st.title("📦 Relatório de Produtos")

    conn = conectar()

    if conn is None:
        st.error("Erro conexão banco")
        return

    try:

        df = pd.read_sql("""
            SELECT id, nome, categoria, preco, estoque
            FROM produtos
            ORDER BY nome
        """, conn)

        st.dataframe(df)

        st.download_button(
            "📥 Exportar CSV",
            df.to_csv(index=False).encode("utf-8"),
            "produtos.csv",
            "text/csv"
        )

    finally:
        conn.close()


# ==================================================
# RELATÓRIO DE CLIENTES
# ==================================================
def relatorio_clientes():

    st.title("👥 Relatório de Clientes")

    conn = conectar()

    if conn is None:
        st.error("Erro conexão banco")
        return

    try:

        df = pd.read_sql("""
            SELECT id, nome, telefone, email, cidade
            FROM clientes
            ORDER BY nome
        """, conn)

        st.dataframe(df)

    finally:
        conn.close()


# ==================================================
# RELATÓRIO DE FORNECEDORES
# ==================================================
def relatorio_fornecedores():

    st.title("🏭 Relatório de Fornecedores")

    conn = conectar()

    if conn is None:
        st.error("Erro conexão banco")
        return

    try:

        df = pd.read_sql("""
            SELECT id, nome, telefone, email
            FROM fornecedores
            ORDER BY nome
        """, conn)

        st.dataframe(df)

    finally:
        conn.close()


# ==================================================
# RELATÓRIO CONTAS A PAGAR
# ==================================================
def relatorio_contas_pagar():

    st.title("💸 Contas a Pagar")

    conn = conectar()

    if conn is None:
        st.error("Erro conexão banco")
        return

    try:

        df = pd.read_sql("""
            SELECT id, descricao, valor, vencimento, status
            FROM contas_pagar
            ORDER BY vencimento
        """, conn)

        st.dataframe(df)

        st.metric(
            "Total em aberto",
            float(df[df["status"] == "ABERTO"]["valor"].sum())
        )

    finally:
        conn.close()


# ==================================================
# RELATÓRIO CONTAS A RECEBER
# ==================================================
def relatorio_contas_receber():

    st.title("💰 Contas a Receber")

    conn = conectar()

    if conn is None:
        st.error("Erro conexão banco")
        return

    try:

        df = pd.read_sql("""
            SELECT id, cliente, descricao, valor, vencimento, status
            FROM contas_receber
            ORDER BY vencimento
        """, conn)

        st.dataframe(df)

        st.metric(
            "Total em aberto",
            float(df[df["status"] == "ABERTO"]["valor"].sum())
        )

    finally:
        conn.close()


# ==================================================
# RELATÓRIO COMPRAS
# ==================================================
def relatorio_compras():

    st.title("🛒 Relatório de Compras")

    conn = conectar()

    if conn is None:
        st.error("Erro conexão banco")
        return

    try:

        df = pd.read_sql("""
            SELECT id, fornecedor, data_compra, total
            FROM compras
            ORDER BY data_compra DESC
        """, conn)

        st.dataframe(df)

        st.metric("Total compras", float(df["total"].sum()))

    finally:
        conn.close()