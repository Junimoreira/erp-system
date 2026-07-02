import streamlit as st

from database.central_compras_db import (
    produtos_parados,
    resumo_idade_estoque,
    capital_parado_total,
    produtos_mais_vendidos,
    produtos_menor_giro,
    sugestoes_promocao,
    historico_custos_produtos
)

from database.inteligencia_estoque_db import (
    recalcular_inteligencia_estoque,
    listar_inteligencia_estoque
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)


def tela_central_compras():

    st.title("🧠 Central Inteligente de Compras")

    capital = capital_parado_total()
    resumo = resumo_idade_estoque()

    st.markdown("### 💰 Capital Parado em Estoque")

    st.metric(
        "Valor total em produtos parados/estocados",
        formatar_moeda(capital)
    )

    st.divider()

    st.markdown("### 📦 Idade do Estoque")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🟡 +90 dias", resumo.get("90", 0))
    col2.metric("🟠 +180 dias", resumo.get("180", 0))
    col3.metric("🔴 +270 dias", resumo.get("270", 0))
    col4.metric("🚨 +365 dias", resumo.get("365", 0))

    st.divider()

    abas = st.tabs([
        "🧠 Inteligência de Estoque",
        "📦 Produtos Parados",
        "📢 Sugestões de Promoção",
        "⭐ Mais Vendidos",
        "🐢 Menor Giro",
        "📈 Histórico de Custos"
    ])

    with abas[0]:
        st.subheader("🧠 Inteligência de Estoque")

        if st.button("🔄 Recalcular Inteligência", use_container_width=True):
            sucesso = recalcular_inteligencia_estoque()

            if sucesso:
                st.success("Inteligência de estoque recalculada com sucesso!")
            else:
                st.error("Erro ao recalcular inteligência de estoque.")

        df = listar_inteligencia_estoque()

        if df.empty:
            st.info("Nenhum dado calculado ainda. Clique em Recalcular Inteligência.")
        else:
            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=500
            )

    with abas[1]:
        st.subheader("📦 Produtos Parados")

        dias = st.selectbox(
            "Mostrar produtos sem venda há:",
            [90, 180, 270, 365],
            index=1
        )

        df = produtos_parados(dias)

        if df.empty:
            st.success("Nenhum produto parado nesse período.")
        else:
            st.warning(f"{len(df)} produto(s) parado(s) há {dias} dias ou mais.")

            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=450
            )

    with abas[2]:
        st.subheader("📢 Sugestões de Promoção")

        dias_promocao = st.selectbox(
            "Critério para sugestão:",
            [180, 270, 365],
            index=1
        )

        df = sugestoes_promocao(dias_promocao)

        if df.empty:
            st.success("Nenhum produto exigindo campanha nesse critério.")
        else:
            st.warning(
                f"{len(df)} produto(s) precisam de atenção comercial."
            )

            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=450
            )

            st.info(
                "Sugestão: priorize produtos com maior capital parado e maior tempo sem venda."
            )

    with abas[3]:
        st.subheader("⭐ Produtos Mais Vendidos")

        df = produtos_mais_vendidos()

        if df.empty:
            st.info("Nenhuma venda encontrada.")
        else:
            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=450
            )

    with abas[4]:
        st.subheader("🐢 Produtos com Menor Giro")

        df = produtos_menor_giro()

        if df.empty:
            st.info("Nenhum produto encontrado.")
        else:
            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=450
            )

    with abas[5]:
        st.subheader("📈 Histórico de Custos")

        df = historico_custos_produtos()

        if df.empty:
            st.info("Nenhum histórico de custo encontrado.")
        else:
            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=True,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=450
            )