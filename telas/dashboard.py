import streamlit as st

from database.dashboard_db import (
    total_despesas_fixas_mes,
    total_vendido_mes,
    calcular_meta_mes,
    calcular_falta_meta,
    percentual_meta,
    lucro_estimado
)


# ==================================================
# DASHBOARD
# ==================================================

def tela_dashboard():

    st.title("📊 Dashboard Financeiro")

    # ==============================================
    # INDICADORES
    # ==============================================

    despesas_fixas = total_despesas_fixas_mes()

    vendido = total_vendido_mes()

    meta = calcular_meta_mes()

    falta = calcular_falta_meta()

    percentual = percentual_meta()

    lucro = lucro_estimado()

    # ==============================================
    # PRIMEIRA LINHA
    # ==============================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "💸 Despesas Fixas",
            f"R$ {despesas_fixas:,.2f}"
        )

    with col2:

        st.metric(
            "🎯 Meta do Mês",
            f"R$ {meta:,.2f}"
        )

    with col3:

        st.metric(
            "💰 Vendido no Mês",
            f"R$ {vendido:,.2f}"
        )

    # ==============================================
    # SEGUNDA LINHA
    # ==============================================

    col4, col5, col6 = st.columns(3)

    with col4:

        st.metric(
            "📉 Falta para Meta",
            f"R$ {falta:,.2f}"
        )

    with col5:

        st.metric(
            "📊 Meta Atingida",
            f"{percentual:.1f}%"
        )

    with col6:

        st.metric(
            "📈 Lucro Estimado",
            f"R$ {lucro:,.2f}"
        )

    # ==============================================
    # BARRA PROGRESSO
    # ==============================================

    st.divider()

    st.subheader(
        "🎯 Progresso da Meta"
    )

    st.progress(
        min(percentual / 100, 1.0)
    )

    st.info(f'''
💰 Vendido: R$ {vendido:,.2f}

🎯 Meta: R$ {meta:,.2f}

📉 Falta: R$ {falta:,.2f}
''')