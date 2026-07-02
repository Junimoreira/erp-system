# telas/dashboard.py

import streamlit as st

from database.dashboard_db import (
    obter_dashboard_mensal,
    total_despesas_fixas_mes,
    total_despesas_variaveis_mes,
    total_vendido_mes,
    calcular_meta_mes,
    calcular_falta_meta,
    percentual_meta,
    lucro_estimado,
    obter_alertas_financeiros
)

from utils.formatacao import (
    formatar_moeda,
    formatar_data
)


def valor_float(valor):
    try:
        if valor is None:
            return 0.0
        return float(valor)
    except Exception:
        return 0.0


def valor_int(valor):
    try:
        if valor is None:
            return 0
        return int(valor)
    except Exception:
        return 0


def tela_dashboard():

    st.title("📊 Dashboard Financeiro")

    try:
        dados = obter_dashboard_mensal()

        if dados is None:
            dados = {}

        vendido = valor_float(total_vendido_mes())
        despesas_fixas = valor_float(total_despesas_fixas_mes())
        despesas_variaveis = valor_float(total_despesas_variaveis_mes())
        meta = valor_float(calcular_meta_mes())
        falta = valor_float(calcular_falta_meta())
        percentual = valor_float(percentual_meta())
        lucro = valor_float(lucro_estimado())

    except Exception as erro:
        st.error(f"Erro ao carregar dashboard: {erro}")
        return

    vendas_mes = valor_float(dados.get("vendas_mes", 0))
    receber_mes = valor_float(dados.get("receber_mes", 0))
    pagar_mes = valor_float(dados.get("pagar_mes", 0))
    pagar_pendente_mes = valor_float(dados.get("pagar_pendente_mes", 0))
    caixa_atual = valor_float(dados.get("caixa_atual", 0))

    clientes = valor_int(dados.get("clientes", 0))
    fornecedores = valor_int(dados.get("fornecedores", 0))
    produtos = valor_int(dados.get("produtos", 0))
    estoque_baixo = valor_int(dados.get("estoque_baixo", 0))

    st.subheader("💰 Resumo do Mês")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💵 Vendas do Mês", formatar_moeda(vendas_mes))
    col2.metric("📥 A Receber no Mês", formatar_moeda(receber_mes))
    col3.metric("📤 Obrigações do Mês", formatar_moeda(pagar_mes))
    col4.metric("🏦 Caixa Atual", formatar_moeda(caixa_atual))

    st.divider()

    st.subheader("📌 Compromissos e Meta")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("🔒 Contas Fixas", formatar_moeda(despesas_fixas))
    col6.metric("🔄 Contas Variáveis", formatar_moeda(despesas_variaveis))
    col7.metric("⏳ Pendentes do Mês", formatar_moeda(pagar_pendente_mes))
    col8.metric("🎯 Meta Mínima", formatar_moeda(meta))

    st.caption(
        "A meta mínima é calculada sobre as contas FIXAS do mês: Contas Fixas x 1,25."
    )

    st.divider()

    st.subheader("📈 Resultado Estratégico")

    col9, col10, col11, col12 = st.columns(4)

    col9.metric("📉 Falta para Meta", formatar_moeda(falta))
    col10.metric("📊 Meta Atingida", f"{percentual:.2f}%".replace(".", ","))
    col11.metric("📈 Resultado Estimado", formatar_moeda(lucro))
    col12.metric(
        "🧮 Total Despesas",
        formatar_moeda(despesas_fixas + despesas_variaveis)
    )

    progresso = min(max(percentual / 100, 0), 1)
    st.progress(progresso)

    if lucro > 0:
        st.success(
            f"Empresa projetando resultado positivo de {formatar_moeda(lucro)} no mês."
        )
    elif lucro < 0:
        st.error(
            f"Empresa projetando déficit de {formatar_moeda(abs(lucro))} no mês."
        )
    else:
        st.warning("Resultado financeiro zerado até o momento.")

    st.divider()

    st.subheader("📋 Cadastros")

    col13, col14, col15, col16 = st.columns(4)

    col13.metric("👥 Clientes", clientes)
    col14.metric("🚚 Fornecedores", fornecedores)
    col15.metric("📦 Produtos", produtos)
    col16.metric("⚠️ Estoque Baixo", estoque_baixo)

    st.divider()

    st.subheader("🚨 Alertas Financeiros")

    try:
        alertas = obter_alertas_financeiros()

        if alertas is None:
            alertas = {}

        vencidas = alertas.get("vencidas", [])
        hoje = alertas.get("hoje", [])
        proximas = alertas.get("proximas", [])

    except Exception as erro:
        st.error(f"Erro ao carregar alertas financeiros: {erro}")
        vencidas = []
        hoje = []
        proximas = []

    if vencidas:
        st.error(f"Existem {len(vencidas)} contas vencidas.")

        for descricao, valor, vencimento in vencidas:
            st.write(
                f"🔴 {descricao} | {formatar_moeda(valor)} | {formatar_data(vencimento)}"
            )

    if hoje:
        st.warning(f"Existem {len(hoje)} contas vencendo hoje.")

        for descricao, valor, vencimento in hoje:
            st.write(
                f"🟠 {descricao} | {formatar_moeda(valor)} | {formatar_data(vencimento)}"
            )

    if proximas:
        st.info(f"Existem {len(proximas)} contas vencendo nos próximos 7 dias.")

        for descricao, valor, vencimento in proximas:
            st.write(
                f"🟢 {descricao} | {formatar_moeda(valor)} | {formatar_data(vencimento)}"
            )

    if not vencidas and not hoje and not proximas:
        st.success("Nenhuma conta vencida ou próxima do vencimento.")

    with st.expander("🔍 Debug Dashboard"):
        st.write(dados)