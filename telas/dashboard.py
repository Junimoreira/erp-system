# telas/dashboard.py

import streamlit as st

from database.dashboard_db import (
    obter_dashboard_mensal,
    total_despesas_fixas_mes,
    total_vendido_mes,
    calcular_meta_mes,
    calcular_falta_meta,
    percentual_meta,
    lucro_estimado
)


# ==================================================
# DASHBOARD ERP
# ==================================================
def tela_dashboard():

    st.title("📊 Dashboard Financeiro")

    # ==================================================
    # DADOS GERAIS
    # ==================================================
    try:

        dados = obter_dashboard_mensal()

        despesas_fixas = float(
            total_despesas_fixas_mes() or 0
        )

        vendido = float(
            total_vendido_mes() or 0
        )

        meta = float(
            calcular_meta_mes() or 0
        )

        falta = float(
            calcular_falta_meta() or 0
        )

        percentual = float(
            percentual_meta() or 0
        )

        lucro = float(
            lucro_estimado() or 0
        )

    except Exception as erro:

        st.error(f"Erro ao carregar dashboard: {erro}")

        return

    # ==================================================
    # VALIDAÇÕES
    # ==================================================
    vendas_mes = float(
        dados.get("vendas_mes", 0) or 0
    )

    receber_mes = float(
        dados.get("receber_mes", 0) or 0
    )

    pagar_mes = float(
        dados.get("pagar_mes", 0) or 0
    )

    clientes = int(
        dados.get("clientes", 0) or 0
    )

    fornecedores = int(
        dados.get("fornecedores", 0) or 0
    )

    produtos = int(
        dados.get("produtos", 0) or 0
    )

    estoque_baixo = int(
        dados.get("estoque_baixo", 0) or 0
    )

    caixa_atual = float(
        dados.get("caixa_atual", 0) or 0
    )

    lucro_mes = float(
        dados.get("lucro_mes", 0) or 0
    )

    # ==================================================
    # PRIMEIRA LINHA
    # ==================================================
    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💰 Vendas Mês",
            f"R$ {vendas_mes:,.2f}"
        )

    with col2:

        st.metric(
            "📈 Lucro Mês",
            f"R$ {lucro_mes:,.2f}"
        )

    with col3:

        st.metric(
            "💳 Contas Receber",
            f"R$ {receber_mes:,.2f}"
        )

    with col4:

        st.metric(
            "💸 Contas Pagar",
            f"R$ {pagar_mes:,.2f}"
        )

    st.divider()

    # ==================================================
    # SEGUNDA LINHA
    # ==================================================
    col5, col6, col7, col8 = st.columns(4)

    with col5:

        st.metric(
            "📦 Produtos",
            produtos
        )

    with col6:

        st.metric(
            "👥 Clientes",
            clientes
        )

    with col7:

        st.metric(
            "🚚 Fornecedores",
            fornecedores
        )

    with col8:

        st.metric(
            "⚠️ Estoque Baixo",
            estoque_baixo
        )

    st.divider()

    # ==================================================
    # TERCEIRA LINHA
    # ==================================================
    col9, col10, col11 = st.columns(3)

    with col9:

        st.metric(
            "💸 Despesas Fixas",
            f"R$ {despesas_fixas:,.2f}"
        )

    with col10:

        st.metric(
            "🎯 Meta do Mês",
            f"R$ {meta:,.2f}"
        )

    with col11:

        st.metric(
            "🏦 Caixa Atual",
            f"R$ {caixa_atual:,.2f}"
        )

    st.divider()

    # ==================================================
    # QUARTA LINHA
    # ==================================================
    col12, col13, col14 = st.columns(3)

    with col12:

        st.metric(
            "💰 Vendido no Mês",
            f"R$ {vendido:,.2f}"
        )

    with col13:

        st.metric(
            "📉 Falta para Meta",
            f"R$ {falta:,.2f}"
        )

    with col14:

        st.metric(
            "📊 Meta Atingida",
            f"{percentual:.1f}%"
        )

    st.divider()

    # ==================================================
    # LUCRO ESTIMADO
    # ==================================================
    st.metric(
        "📈 Lucro Estimado",
        f"R$ {lucro:,.2f}"
    )

    st.divider()

    # ==================================================
    # PROGRESSO META
    # ==================================================
    st.subheader(
        "🎯 Progresso da Meta"
    )

    progresso = min(
        percentual / 100,
        1.0
    )

    progresso = max(
        progresso,
        0
    )

    st.progress(progresso)

    st.info(f"""
💰 Vendido: R$ {vendido:,.2f}

🎯 Meta: R$ {meta:,.2f}

📉 Falta: R$ {falta:,.2f}

📊 Progresso: {percentual:.1f}%
""")

    # ==================================================
    # DEBUG TEMPORÁRIO
    # ==================================================
    with st.expander("🔍 Debug Dashboard"):

        st.write(dados)