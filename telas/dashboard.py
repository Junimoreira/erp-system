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

    try:

        dados = obter_dashboard_mensal()

        despesas_mes = float(
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

        st.error(
            f"Erro ao carregar dashboard: {erro}"
        )

        return

    # ==================================================
    # DADOS
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
    # RESUMO FINANCEIRO
    # ==================================================
    st.subheader("💰 Resumo Financeiro")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💵 Vendas do Mês",
            f"R$ {vendas_mes:,.2f}"
        )

    with col2:

        st.metric(
            "📥 Contas a Receber",
            f"R$ {receber_mes:,.2f}"
        )

    with col3:

        st.metric(
            "📤 Contas a Pagar",
            f"R$ {pagar_mes:,.2f}"
        )

    with col4:

        st.metric(
            "🏦 Caixa Atual",
            f"R$ {caixa_atual:,.2f}"
        )

    st.divider()

    # ==================================================
    # META E RESULTADO
    # ==================================================
    st.subheader("🎯 Meta e Resultado")

    col5, col6, col7, col8 = st.columns(4)

    with col5:

        st.metric(
            "📌 Compromissos do Mês",
            f"R$ {despesas_mes:,.2f}"
        )

    with col6:

        st.metric(
            "🎯 Meta de Faturamento",
            f"R$ {meta:,.2f}"
        )

    with col7:

        st.metric(
            "📉 Falta para Meta",
            f"R$ {falta:,.2f}"
        )

    with col8:

        st.metric(
            "📈 Lucro Estimado",
            f"R$ {lucro:,.2f}"
        )

    st.divider()

    # ==================================================
    # CADASTROS
    # ==================================================
    st.subheader("📋 Cadastros")

    col9, col10, col11, col12 = st.columns(4)

    with col9:

        st.metric(
            "👥 Clientes",
            clientes
        )

    with col10:

        st.metric(
            "🚚 Fornecedores",
            fornecedores
        )

    with col11:

        st.metric(
            "📦 Produtos",
            produtos
        )

    with col12:

        st.metric(
            "⚠️ Estoque Baixo",
            estoque_baixo
        )

    st.divider()

    # ==================================================
    # PROGRESSO DA META
    # ==================================================
    st.subheader(
        "🚀 Progresso da Meta Mensal"
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
💰 Faturamento Atual: R$ {vendido:,.2f}

🎯 Meta de Faturamento: R$ {meta:,.2f}

📉 Falta para atingir a meta: R$ {falta:,.2f}

📊 Meta atingida: {percentual:.2f}%
""")

    st.divider()

    # ==================================================
    # ANÁLISE RÁPIDA
    # ==================================================
    st.subheader("📈 Análise do Mês")

    if lucro > 0:

        st.success(
            f"Empresa projetando lucro de R$ {lucro:,.2f} no mês."
        )

    elif lucro < 0:

        st.error(
            f"Empresa projetando prejuízo de R$ {abs(lucro):,.2f} no mês."
        )

    else:

        st.warning(
            "Resultado financeiro zerado até o momento."
        )

    # ==================================================
    # DEBUG
    # ==================================================
    with st.expander("🔍 Debug Dashboard"):

        st.write(dados)