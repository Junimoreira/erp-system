import streamlit as st
import pandas as pd
import plotly.express as px

from database.produto_db import listar_produtos
from utils.financeiro import calcular_lucro_real


# ==================================================
# DASHBOARD FINANCEIRO
# ==================================================
def tela_dashboard_financeiro():

    st.title("📊 Dashboard Financeiro ERP")

    df = listar_produtos()

    if df.empty:
        st.warning("Sem produtos cadastrados.")
        return

    # =========================
    # TRATAMENTO DE DADOS
    # =========================
    df["lucro_unitario"] = df.apply(
        lambda x: calcular_lucro_real(x["preco"], x["custo"]),
        axis=1
    )

    df["lucro_total"] = df["lucro_unitario"] * df["estoque"]

    # =========================
    # KPIs
    # =========================
    lucro_total = df["lucro_total"].sum()
    estoque_total = df["estoque"].sum()
    produtos = len(df)

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Lucro Total Estimado", f"R$ {lucro_total:,.2f}")
    col2.metric("📦 Estoque Total", f"{estoque_total}")
    col3.metric("📊 Produtos", produtos)

    st.divider()

    # =========================
    # GRÁFICO: TOP LUCRO
    # =========================
    st.subheader("🏆 Top 10 Produtos Mais Lucrativos")

    top = df.sort_values("lucro_total", ascending=False).head(10)

    fig1 = px.bar(
        top,
        x="nome",
        y="lucro_total",
        title="Top Produtos por Lucro"
    )

    st.plotly_chart(fig1, use_container_width=True)

    st.dataframe(
        top[["nome", "preco", "custo", "estoque", "lucro_total"]],
        use_container_width=True
    )

    st.divider()

    # =========================
    # ESTOQUE BAIXO
    # =========================
    st.subheader("⚠️ Estoque Baixo")

    baixo = df[df["estoque"] <= df["estoque_minimo"]]

    if baixo.empty:
        st.success("Nenhum produto com estoque baixo.")
    else:

        fig2 = px.bar(
            baixo,
            x="nome",
            y="estoque",
            title="Produtos com Estoque Baixo"
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(
            baixo[["nome", "estoque", "estoque_minimo"]],
            use_container_width=True
        )

    st.divider()

    # =========================
    # DISTRIBUIÇÃO DE ESTOQUE
    # =========================
    st.subheader("📦 Distribuição de Estoque")

    fig3 = px.pie(
        df,
        values="estoque",
        names="nome",
        title="Participação do Estoque por Produto"
    )

    st.plotly_chart(fig3, use_container_width=True)