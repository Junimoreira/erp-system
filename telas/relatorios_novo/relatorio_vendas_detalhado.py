from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database.relatorios_vendas_detalhado_db import (
    obter_vendas_detalhadas,
    obter_resumo_vendas_periodo,
    conferir_totais_vendas,
)

from services.relatorios.relatorio_base import (
    formatar_moeda,
    formatar_data_hora,
)

from services.relatorios.pdf_relatorio import (
    gerar_pdf_profissional,
    criar_tabela_relatorio,
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def inteiro_seguro(valor):
    try:
        return int(valor or 0)
    except Exception:
        return 0


def formatar_status_conferencia(ok):
    if ok:
        return "OK"

    return "DIVERGÊNCIA"


# ============================================================
# PDF
# ============================================================

def gerar_pdf_vendas_detalhado(
    data_inicio,
    data_fim,
    df,
    resumo,
    conferencia,
):

    linhas = []

    for _, row in df.iterrows():

        ajuste = (
            "Sim"
            if bool(
                row.get(
                    "ajuste_historico",
                    False,
                )
            )
            else "Não"
        )

        linhas.append(
            [
                inteiro_seguro(
                    row["pedido"]
                ),
                formatar_data_hora(
                    row["data_venda"]
                ),
                row["cliente"],
                formatar_moeda(
                    row["valor_bruto"]
                ),
                formatar_moeda(
                    row["desconto"]
                ),
                formatar_moeda(
                    row["valor_final"]
                ),
                row["forma_pagamento"],
                ajuste,
            ]
        )

    tabela = criar_tabela_relatorio(
        [
            "Pedido",
            "Data",
            "Cliente",
            "Valor bruto",
            "Desconto",
            "Valor final",
            "Pagamento",
            "Normalizado",
        ],
        linhas,
        alinhamentos=[
            "CENTER",
            "CENTER",
            "LEFT",
            "RIGHT",
            "RIGHT",
            "RIGHT",
            "CENTER",
            "CENTER",
        ],
    )

    indicadores = [
        {
            "titulo": "Vendas",
            "valor": str(
                inteiro_seguro(
                    resumo.get(
                        "quantidade_vendas"
                    )
                )
            ),
        },
        {
            "titulo": "Valor bruto",
            "valor": formatar_moeda(
                resumo.get(
                    "valor_bruto",
                    0,
                )
            ),
        },
        {
            "titulo": "Descontos",
            "valor": formatar_moeda(
                resumo.get(
                    "total_descontos",
                    0,
                )
            ),
        },
        {
            "titulo": "Faturamento",
            "valor": formatar_moeda(
                resumo.get(
                    "faturamento",
                    0,
                )
            ),
        },
        {
            "titulo": "Ticket médio",
            "valor": formatar_moeda(
                resumo.get(
                    "ticket_medio",
                    0,
                )
            ),
        },
    ]

    texto_conferencia = (
        "Conferência matemática do período: "
        f"{formatar_moeda(conferencia.get('valor_bruto', 0))} "
        "- "
        f"{formatar_moeda(conferencia.get('descontos', 0))} "
        "= "
        f"{formatar_moeda(conferencia.get('faturamento', 0))}. "
        f"Status: {formatar_status_conferencia(conferencia.get('ok'))}."
    )

    texto_normalizacao = (
        f"Foram identificadas "
        f"{inteiro_seguro(conferencia.get('vendas_normalizadas'))} "
        "vendas históricas registradas pelo padrão antigo do ERP. "
        "Nesses casos, o valor bruto foi reconstruído apenas para "
        "fins de relatório, sem qualquer alteração nos registros "
        "originais do banco."
    )

    secoes = [
        {
            "titulo":
                "Conferência do Período",

            "texto":
                texto_conferencia,

            "observacao":
                texto_normalizacao,
        },

        {
            "titulo":
                "Vendas do Período",

            "texto":
                (
                    "Cada linha representa uma venda/pedido "
                    "único registrado no ERP. "
                    "Os produtos existentes dentro do pedido "
                    "não multiplicam a quantidade de vendas."
                ),

            "tabela":
                tabela,
        },
    ]

    return gerar_pdf_profissional(
        titulo="Relatório de Vendas por Período",
        periodo_inicio=data_inicio,
        periodo_fim=data_fim,
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )


# ============================================================
# TELA PRINCIPAL
# ============================================================

def tela_relatorio_vendas_detalhado():

    st.title(
        "🧾 Relatório de Vendas por Período"
    )

    st.caption(
        "Conferência detalhada de pedidos, "
        "valores, descontos e formas de pagamento."
    )

    # ========================================================
    # FILTROS
    # ========================================================

    st.subheader(
        "Período"
    )

    col1, col2 = st.columns(2)

    with col1:

        data_inicio = st.date_input(
            "Data inicial",
            value=date(
                2026,
                6,
                1,
            ),
            format="DD/MM/YYYY",
            key=(
                "relatorio_detalhado_"
                "data_inicio"
            ),
        )

    with col2:

        data_fim = st.date_input(
            "Data final",
            value=date(
                2026,
                8,
                31,
            ),
            format="DD/MM/YYYY",
            key=(
                "relatorio_detalhado_"
                "data_fim"
            ),
        )

    if data_inicio > data_fim:

        st.error(
            "A data inicial não pode ser "
            "maior que a data final."
        )

        return

    data_fim_sql = (
        data_fim
        + timedelta(days=1)
    )

    # ========================================================
    # GERAR
    # ========================================================

    if st.button(
        "🔎 Gerar relatório",
        type="primary",
        use_container_width=True,
        key=(
            "botao_relatorio_"
            "vendas_detalhado"
        ),
    ):

        with st.spinner(
            "Consultando vendas..."
        ):

            df = (
                obter_vendas_detalhadas(
                    data_inicio,
                    data_fim_sql,
                )
            )

            resumo = (
                obter_resumo_vendas_periodo(
                    data_inicio,
                    data_fim_sql,
                )
            )

            conferencia = (
                conferir_totais_vendas(
                    data_inicio,
                    data_fim_sql,
                )
            )

        if (
            df is None
            or df.empty
            or resumo is None
            or conferencia is None
        ):

            st.warning(
                "Nenhuma venda encontrada "
                "no período."
            )

            return

        # ====================================================
        # INDICADORES
        # ====================================================

        st.divider()

        st.subheader(
            "Resumo"
        )

        col1, col2, col3 = (
            st.columns(3)
        )

        col1.metric(
            "Vendas",
            inteiro_seguro(
                resumo.get(
                    "quantidade_vendas"
                )
            ),
        )

        col2.metric(
            "Valor bruto",
            formatar_moeda(
                resumo.get(
                    "valor_bruto"
                )
            ),
        )

        col3.metric(
            "Descontos",
            formatar_moeda(
                resumo.get(
                    "total_descontos"
                )
            ),
        )

        col4, col5 = (
            st.columns(2)
        )

        col4.metric(
            "Faturamento",
            formatar_moeda(
                resumo.get(
                    "faturamento"
                )
            ),
        )

        col5.metric(
            "Ticket médio",
            formatar_moeda(
                resumo.get(
                    "ticket_medio"
                )
            ),
        )

        # ====================================================
        # CONFERÊNCIA
        # ====================================================

        st.divider()

        st.subheader(
            "✅ Conferência do período"
        )

        col1, col2, col3 = (
            st.columns(3)
        )

        col1.metric(
            "Bruto - descontos",
            formatar_moeda(
                conferencia.get(
                    "valor_esperado"
                )
            ),
        )

        col2.metric(
            "Faturamento",
            formatar_moeda(
                conferencia.get(
                    "faturamento"
                )
            ),
        )

        col3.metric(
            "Diferença",
            formatar_moeda(
                conferencia.get(
                    "diferenca"
                )
            ),
        )

        if conferencia.get(
            "ok"
        ):

            st.success(
                "Conferência matemática OK: "
                "valor bruto - descontos = faturamento."
            )

        else:

            st.error(
                "Há divergência entre valor bruto, "
                "descontos e faturamento."
            )

        vendas_normalizadas = (
            inteiro_seguro(
                conferencia.get(
                    "vendas_normalizadas"
                )
            )
        )

        if vendas_normalizadas > 0:

            st.info(
                (
                    f"{vendas_normalizadas} vendas históricas "
                    "foram normalizadas para apresentação. "
                    "Nenhum registro original do banco foi alterado."
                )
            )

        # ====================================================
        # TABELA
        # ====================================================

        st.divider()

        st.subheader(
            "Detalhamento das vendas"
        )

        df_tela = (
            df.copy()
        )

        df_tela[
            "Data"
        ] = df_tela[
            "data_venda"
        ].apply(
            formatar_data_hora
        )

        df_tela[
            "Valor bruto"
        ] = df_tela[
            "valor_bruto"
        ].apply(
            formatar_moeda
        )

        df_tela[
            "Desconto"
        ] = df_tela[
            "desconto"
        ].apply(
            formatar_moeda
        )

        df_tela[
            "Valor final"
        ] = df_tela[
            "valor_final"
        ].apply(
            formatar_moeda
        )

        df_tela[
            "Normalizado"
        ] = df_tela[
            "ajuste_historico"
        ].apply(
            lambda valor:
                "Sim"
                if bool(valor)
                else "Não"
        )

        df_tela = (
            df_tela[
                [
                    "pedido",
                    "Data",
                    "cliente",
                    "Valor bruto",
                    "Desconto",
                    "Valor final",
                    "forma_pagamento",
                    "Normalizado",
                ]
            ]
        )

        df_tela.columns = [
            "Pedido",
            "Data",
            "Cliente",
            "Valor bruto",
            "Desconto",
            "Valor final",
            "Forma de pagamento",
            "Normalizado",
        ]

        st.dataframe(
            df_tela,
            use_container_width=True,
            hide_index=True,
        )

        # ====================================================
        # PDF
        # ====================================================

        st.divider()

        st.subheader(
            "📄 Documento profissional"
        )

        pdf = gerar_pdf_vendas_detalhado(
            data_inicio,
            data_fim,
            df,
            resumo,
            conferencia,
        )

        nome_pdf = (
            "relatorio_vendas_"
            f"{data_inicio.strftime('%Y%m%d')}_"
            f"{data_fim.strftime('%Y%m%d')}.pdf"
        )

        st.download_button(
            "📥 Baixar relatório em PDF",
            data=pdf.getvalue(),
            file_name=nome_pdf,
            mime="application/pdf",
            use_container_width=True,
        )

        # ====================================================
        # METODOLOGIA
        # ====================================================

        with st.expander(
            "ℹ️ Critérios e metodologia"
        ):

            st.markdown(
                """
**Venda:** cada número de pedido é contabilizado
uma única vez, independentemente da quantidade
de produtos existentes dentro dele.

**Valor bruto:** representa o valor da venda antes
do desconto.

**Desconto:** valor concedido ao cliente.

**Valor final:** valor efetivamente considerado como
faturamento da venda.

**Normalização histórica:** algumas vendas antigas
foram gravadas por uma versão anterior do ERP em que
`valor_total` já continha o desconto aplicado. Nesses
casos, o relatório reconstrói o valor bruto apenas para
fins de apresentação e conferência.

**Importante:** a normalização não altera nenhum dado
histórico do banco.
                """
            )