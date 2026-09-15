from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database.relatorios_vendas_diarias_db import (
    obter_vendas_por_dia,
    obter_detalhes_vendas_dia,
)

from services.relatorios.relatorio_base import (
    formatar_moeda,
    formatar_data,
)

from services.relatorios.pdf_relatorio import (
    gerar_pdf_profissional,
    criar_tabela_relatorio,
)


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def inteiro_seguro(valor):
    try:
        return int(valor or 0)
    except Exception:
        return 0


def numero_seguro(valor):
    try:
        return float(valor or 0)
    except Exception:
        return 0.0


def formatar_hora(valor):
    if valor is None:
        return ""

    try:
        return pd.to_datetime(
            valor
        ).strftime("%H:%M")
    except Exception:
        return ""


def formatar_data_hora(valor):
    if valor is None:
        return ""

    try:
        return pd.to_datetime(
            valor
        ).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return ""


# ============================================================
# PDF
# ============================================================

def gerar_pdf_vendas_diarias(
    data_inicio,
    data_fim,
    vendas_dia,
    detalhes,
):
    quantidade_vendas = inteiro_seguro(
        vendas_dia["quantidade_vendas"].sum()
    )

    faturamento = numero_seguro(
        vendas_dia["faturamento"].sum()
    )

    dias_com_vendas = inteiro_seguro(
        (
            vendas_dia["quantidade_vendas"] > 0
        ).sum()
    )

    ticket_medio = (
        faturamento / quantidade_vendas
        if quantidade_vendas > 0
        else 0
    )

    # ========================================================
    # RESUMO DIARIO
    # ========================================================

    linhas_diarias = []

    for _, row in vendas_dia.iterrows():

        linhas_diarias.append(
            [
                formatar_data(
                    row["data"]
                ),
                inteiro_seguro(
                    row["quantidade_vendas"]
                ),
                formatar_moeda(
                    row["faturamento"]
                ),
                formatar_moeda(
                    row["ticket_medio"]
                ),
            ]
        )

    tabela_diaria = criar_tabela_relatorio(
        [
            "Data",
            "Vendas",
            "Faturamento",
            "Ticket médio",
        ],
        linhas_diarias,
        alinhamentos=[
            "CENTER",
            "CENTER",
            "RIGHT",
            "RIGHT",
        ],
    )

    # ========================================================
    # DETALHAMENTO PARA CONFERENCIA
    # ========================================================

    linhas_detalhes = []

    if detalhes is not None and not detalhes.empty:

        for _, row in detalhes.iterrows():

            cliente = (
                row.get("cliente")
                or "Consumidor"
            )

            forma_pagamento = (
                row.get("forma_pagamento")
                or "Não informado"
            )

            linhas_detalhes.append(
                [
                    inteiro_seguro(
                        row["venda_id"]
                    ),
                    formatar_data_hora(
                        row["data_venda"]
                    ),
                    cliente,
                    forma_pagamento,
                    formatar_moeda(
                        row["valor_total"]
                    ),
                    formatar_moeda(
                        row["desconto"]
                    ),
                    formatar_moeda(
                        row["valor_final"]
                    ),
                ]
            )

    tabela_detalhes = (
        criar_tabela_relatorio(
            [
                "Venda",
                "Data / hora",
                "Cliente",
                "Pagamento",
                "Total",
                "Desconto",
                "Valor final",
            ],
            linhas_detalhes,
            alinhamentos=[
                "CENTER",
                "CENTER",
                "LEFT",
                "LEFT",
                "RIGHT",
                "RIGHT",
                "RIGHT",
            ],
        )
        if linhas_detalhes
        else None
    )

    indicadores = [
        {
            "titulo": "Vendas",
            "valor": str(
                quantidade_vendas
            ),
        },
        {
            "titulo": "Faturamento",
            "valor": formatar_moeda(
                faturamento
            ),
        },
        {
            "titulo": "Ticket médio",
            "valor": formatar_moeda(
                ticket_medio
            ),
        },
        {
            "titulo": "Dias com vendas",
            "valor": str(
                dias_com_vendas
            ),
        },
    ]

    secoes = [
        {
            "titulo":
                "Resumo Diário",

            "texto":
                (
                    "O quadro apresenta a quantidade "
                    "de pedidos e o faturamento de "
                    "cada dia do período selecionado. "
                    "Dias sem vendas são apresentados "
                    "com valores zerados."
                ),

            "tabela":
                tabela_diaria,
        },
        {
            "titulo":
                "Conferência dos Pedidos / Talões",

            "texto":
                (
                    "Cada linha representa uma venda "
                    "concluída registrada no ERP. "
                    "Esta relação pode ser utilizada "
                    "para conferência com os talões "
                    "físicos da loja."
                ),

            "tabela":
                tabela_detalhes,
        },
    ]

    return gerar_pdf_profissional(
        titulo="Relatório Diário de Vendas",
        periodo_inicio=data_inicio,
        periodo_fim=data_fim,
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )


# ============================================================
# TELA PRINCIPAL
# ============================================================

def tela_relatorio_vendas_diarias():

    st.title(
        "📅 Relatório Diário de Vendas"
    )

    st.caption(
        "Conferência diária das vendas registradas "
        "no ERP com os pedidos e talões físicos da loja."
    )

    hoje = date.today()

    primeiro_dia_mes = date(
        hoje.year,
        hoje.month,
        1,
    )

    # ========================================================
    # FILTROS
    # ========================================================

    st.subheader(
        "Período de conferência"
    )

    col1, col2 = st.columns(2)

    with col1:

        data_inicio = st.date_input(
            "Data inicial",
            value=primeiro_dia_mes,
            format="DD/MM/YYYY",
            key=(
                "relatorio_vendas_diarias_"
                "data_inicio"
            ),
        )

    with col2:

        data_fim = st.date_input(
            "Data final",
            value=hoje,
            format="DD/MM/YYYY",
            key=(
                "relatorio_vendas_diarias_"
                "data_fim"
            ),
        )

    if data_inicio > data_fim:

        st.error(
            "A data inicial não pode ser "
            "maior que a data final."
        )

        return

    if data_inicio > hoje:

        st.warning(
            "O período selecionado começa "
            "em uma data futura."
        )

        return

    data_fim_consulta = min(
        data_fim,
        hoje,
    )

    if data_fim > hoje:

        st.info(
            "A data final selecionada está no futuro. "
            "O relatório será limitado até hoje."
        )

    # ========================================================
    # GERAR
    # ========================================================

    if st.button(
        "🔎 Gerar relatório",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Consultando vendas..."
        ):

            vendas_dia = (
                obter_vendas_por_dia(
                    data_inicio,
                    data_fim_consulta,
                )
            )

            detalhes = (
                obter_detalhes_vendas_dia(
                    data_inicio,
                    data_fim_consulta,
                )
            )

        if (
            vendas_dia is None
            or vendas_dia.empty
        ):

            st.warning(
                "Não foi possível montar "
                "o período selecionado."
            )

            return

        # ====================================================
        # INDICADORES
        # ====================================================

        quantidade_vendas = inteiro_seguro(
            vendas_dia[
                "quantidade_vendas"
            ].sum()
        )

        faturamento = numero_seguro(
            vendas_dia[
                "faturamento"
            ].sum()
        )

        dias_com_vendas = inteiro_seguro(
            (
                vendas_dia[
                    "quantidade_vendas"
                ] > 0
            ).sum()
        )

        ticket_medio = (
            faturamento / quantidade_vendas
            if quantidade_vendas > 0
            else 0
        )

        st.divider()

        st.subheader(
            "Resumo do período"
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        col1.metric(
            "Vendas",
            quantidade_vendas,
        )

        col2.metric(
            "Faturamento",
            formatar_moeda(
                faturamento
            ),
        )

        col3.metric(
            "Ticket médio",
            formatar_moeda(
                ticket_medio
            ),
        )

        col4.metric(
            "Dias com vendas",
            dias_com_vendas,
        )

        # ====================================================
        # VENDAS POR DIA
        # ====================================================

        st.divider()

        st.subheader(
            "📅 Vendas por dia"
        )

        df_diario = vendas_dia.copy()

        df_diario["Data"] = (
            df_diario["data"].apply(
                formatar_data
            )
        )

        df_diario["Vendas"] = (
            df_diario[
                "quantidade_vendas"
            ].astype(int)
        )

        df_diario["Faturamento"] = (
            df_diario[
                "faturamento"
            ].apply(
                formatar_moeda
            )
        )

        df_diario["Ticket médio"] = (
            df_diario[
                "ticket_medio"
            ].apply(
                formatar_moeda
            )
        )

        df_diario = df_diario[
            [
                "Data",
                "Vendas",
                "Faturamento",
                "Ticket médio",
            ]
        ]

        st.dataframe(
            df_diario,
            use_container_width=True,
            hide_index=True,
        )

        # ====================================================
        # CONFERENCIA DOS TALOES
        # ====================================================

        st.divider()

        st.subheader(
            "🧾 Conferência dos pedidos / talões"
        )

        st.caption(
            "Uma linha corresponde a uma venda. "
            "Use esta relação para conferir os "
            "pedidos físicos do período."
        )

        if (
            detalhes is None
            or detalhes.empty
        ):

            st.info(
                "Nenhuma venda registrada "
                "no período."
            )

        else:

            df_detalhes = detalhes.copy()

            df_detalhes[
                "Data"
            ] = df_detalhes[
                "data_venda"
            ].apply(
                formatar_data
            )

            df_detalhes[
                "Hora"
            ] = df_detalhes[
                "data_venda"
            ].apply(
                formatar_hora
            )

            df_detalhes[
                "Cliente"
            ] = (
                df_detalhes[
                    "cliente"
                ]
                .fillna(
                    "Consumidor"
                )
            )

            df_detalhes[
                "Pagamento"
            ] = (
                df_detalhes[
                    "forma_pagamento"
                ]
                .fillna(
                    "Não informado"
                )
            )

            df_detalhes[
                "Total"
            ] = df_detalhes[
                "valor_total"
            ].apply(
                formatar_moeda
            )

            df_detalhes[
                "Desconto"
            ] = df_detalhes[
                "desconto"
            ].apply(
                formatar_moeda
            )

            df_detalhes[
                "Valor final"
            ] = df_detalhes[
                "valor_final"
            ].apply(
                formatar_moeda
            )

            df_detalhes = df_detalhes[
                [
                    "venda_id",
                    "Data",
                    "Hora",
                    "Cliente",
                    "Pagamento",
                    "Total",
                    "Desconto",
                    "Valor final",
                ]
            ]

            df_detalhes.columns = [
                "Venda",
                "Data",
                "Hora",
                "Cliente",
                "Pagamento",
                "Total",
                "Desconto",
                "Valor final",
            ]

            st.dataframe(
                df_detalhes,
                use_container_width=True,
                hide_index=True,
            )

        # ====================================================
        # PDF
        # ====================================================

        st.divider()

        st.subheader(
            "📄 Documento para conferência"
        )

        pdf = gerar_pdf_vendas_diarias(
            data_inicio,
            data_fim_consulta,
            vendas_dia,
            detalhes,
        )

        nome_pdf = (
            "relatorio_diario_vendas_"
            f"{data_inicio.strftime('%Y%m%d')}_"
            f"{data_fim_consulta.strftime('%Y%m%d')}"
            ".pdf"
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
**Venda:** cada número de venda/pedido concluído é
contabilizado uma única vez.

**Faturamento:** utiliza o valor final registrado na
venda e, quando necessário, o valor total como alternativa.

**Ticket médio:** faturamento do período dividido pela
quantidade de vendas concluídas.

**Dias sem venda:** aparecem com quantidade e faturamento
zerados para facilitar a conferência diária.

**Datas futuras:** não são apresentadas como dias sem venda.

**Conferência dos talões:** o detalhamento apresenta uma
linha por venda concluída, permitindo comparar o ERP com
os pedidos físicos da loja.
                """
            )
