import streamlit as st
import pandas as pd
import plotly.express as px

from database.connection import conectar
from database.produto_db import listar_produtos


# ==================================================
# BUSCAR CAIXA
# ==================================================
def buscar_caixa():

    conn = conectar()

    query = """
        SELECT
            data_abertura,
            total_entradas,
            total_saidas,
            saldo_final,
            status
        FROM caixa
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df


# ==================================================
# BUSCAR VENDAS
# ==================================================
def buscar_vendas():

    conn = conectar()

    query = """
        SELECT
            data_venda,
            total
        FROM vendas
    """

    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame(columns=["data_venda", "total"])

    conn.close()

    return df


# ==================================================
# DASHBOARD HÍBRIDO
# ==================================================
def tela_dashboard_hibrido():

    st.title("📊 Dashboard ERP Completo (Híbrido)")

    # =========================
    # DADOS
    # =========================
    df_prod = listar_produtos()
    df_caixa = buscar_caixa()
    df_vendas = buscar_vendas()

    # =========================
    # KPIs PRINCIPAIS
    # =========================
    total_estoque = df_prod["estoque"].sum()

    lucro_estimado = (df_prod["preco"] - df_prod["custo"]) * df_prod["estoque"]
    lucro_total = lucro_estimado.sum()

    faturamento = 0
    if not df_vendas.empty:
        faturamento = df_vendas["total"].sum()

    entradas_caixa = 0
    saidas_caixa = 0
    saldo_caixa = 0

    if not df_caixa.empty:
        entradas_caixa = df_caixa["total_entradas"].sum()
        saidas_caixa = df_caixa["total_saidas"].sum()
        saldo_caixa = df_caixa["saldo_final"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Faturamento", f"R$ {faturamento:,.2f}")
    col2.metric("💵 Caixa (Saldo)", f"R$ {saldo_caixa:,.2f}")
    col3.metric("📦 Estoque Total", f"{total_estoque}")
    col4.metric("📊 Lucro Estimado", f"R$ {lucro_total:,.2f}")

    st.divider()

    # =========================
    # GRÁFICO CAIXA
    # =========================
    st.subheader("💰 Evolução do Caixa")

    if not df_caixa.empty:

        df_caixa["data_abertura"] = pd.to_datetime(df_caixa["data_abertura"])
        df_caixa["mes"] = df_caixa["data_abertura"].dt.to_period("M").astype(str)

        caixa_mensal = df_caixa.groupby("mes").sum(numeric_only=True).reset_index()

        fig1 = px.line(
            caixa_mensal,
            x="mes",
            y="saldo_final",
            markers=True,
            title="Saldo do Caixa por Mês"
        )

        st.plotly_chart(fig1, use_container_width=True)

    else:
        st.info("Sem dados de caixa.")

    st.divider()

    # =========================
    # GRÁFICO VENDAS
    # =========================
    st.subheader("🛒 Faturamento (Vendas)")

    if not df_vendas.empty:

        df_vendas["data_venda"] = pd.to_datetime(df_vendas["data_venda"])
        df_vendas["mes"] = df_vendas["data_venda"].dt.to_period("M").astype(str)

        vendas_mensal = df_vendas.groupby("mes").sum().reset_index()

        fig2 = px.bar(
            vendas_mensal,
            x="mes",
            y="total",
            title="Faturamento Mensal"
        )

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("Nenhuma venda registrada.")

    st.divider()

    # =========================
    # TOP PRODUTOS
    # =========================
    st.subheader("🏆 Top Produtos")

    df_prod["lucro"] = (df_prod["preco"] - df_prod["custo"]) * df_prod["estoque"]

    top = df_prod.sort_values("lucro", ascending=False).head(10)

    fig3 = px.bar(
        top,
        x="nome",
        y="lucro",
        title="Produtos Mais Lucrativos"
    )

    st.plotly_chart(fig3, use_container_width=True)

    st.dataframe(
        top[["nome", "preco", "custo", "estoque", "lucro"]],
        use_container_width=True
    )