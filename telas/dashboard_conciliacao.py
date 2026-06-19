import streamlit as st
import pandas as pd
from database.connection import conectar


# ==================================================
# QUERY GENÉRICA
# ==================================================
def query_df(sql):
    conn = conectar()
    df = pd.read_sql(sql, conn)
    conn.close()
    return df


# ==================================================
# FINANCE ENGINE
# ==================================================
def get_finance():
    return query_df("""
        SELECT
            LOWER(tipo) as tipo,
            SUM(valor) as total
        FROM movimentacoes_financeiras
        GROUP BY tipo
    """)


# ==================================================
# CAIXA
# ==================================================
def get_caixa():
    return query_df("""
        SELECT
            LOWER(tipo) as tipo,
            SUM(valor) as total
        FROM movimentacoes
        GROUP BY tipo
    """)


# ==================================================
# BANCO
# ==================================================
def get_banco():
    return query_df("""
        SELECT
            LOWER(tipo) as tipo,
            SUM(valor) as total
        FROM movimentacoes_bancarias
        GROUP BY tipo
    """)


# ==================================================
# UI
# ==================================================
st.set_page_config(page_title="Conciliação Financeira", layout="wide")

st.title("📊 Conciliação Financeira (Caixa vs Banco vs ERP)")

finance = get_finance()
caixa = get_caixa()
banco = get_banco()


# ==================================================
# RESUMO GERAL
# ==================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "💰 Finance Engine (Entradas)",
        finance[finance["tipo"] == "entrada"]["total"].sum()
    )

with col2:
    st.metric(
        "🏧 Caixa (Entradas)",
        caixa[caixa["tipo"] == "entrada"]["total"].sum()
    )

with col3:
    st.metric(
        "🏦 Banco (Entradas)",
        banco[banco["tipo"] == "entrada"]["total"].sum()
    )


st.divider()


# ==================================================
# COMPARAÇÃO
# ==================================================
st.subheader("📌 Diferença (Conciliação)")

finance_in = finance[finance["tipo"] == "entrada"]["total"].sum()
caixa_in = caixa[caixa["tipo"] == "entrada"]["total"].sum()
banco_in = banco[banco["tipo"] == "entrada"]["total"].sum()

st.write("💰 Diferença Caixa vs Finance:", caixa_in - finance_in)
st.write("🏦 Diferença Banco vs Finance:", banco_in - finance_in)


st.divider()


# ==================================================
# DETALHAMENTO
# ==================================================
st.subheader("📊 Detalhamento")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("💰 Finance Engine")
    st.dataframe(finance)

with col2:
    st.write("🏧 Caixa")
    st.dataframe(caixa)

with col3:
    st.write("🏦 Banco")
    st.dataframe(banco)