from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database.relatorios_formas_pagamento_db import (
    obter_vendas_por_forma_pagamento,
    obter_resumo_formas_pagamento,
    conferir_formas_pagamento,
)

from services.relatorios.relatorio_base import (
    formatar_moeda,
)

from services.relatorios.pdf_relatorio import (
    gerar_pdf_profissional,
    criar_tabela_relatorio,
)


# ============================================================
# FORMATAÇÕES
# ============================================================

def formatar_percentual(valor):

    try:
        valor = float(valor or 0)

    except Exception:
        valor = 0

    return (
        f"{valor:.2f}%"
        .replace(".", ",")
    )


# ============================================================
# PREPARAR DATAFRAME PARA TELA
# ============================================================

def preparar_dataframe_exibicao(df):
    """
    Prepara somente a apresentação na tela.

    Não altera os dados originais retornados
    pelo banco.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    exibicao = df.copy()

    exibicao = exibicao.rename(
        columns={
            "forma_pagamento":
                "Forma de Pagamento",

            "quantidade_vendas":
                "Nº Vendas",

            "faturamento":
                "Faturamento",

            "ticket_medio":
                "Ticket Médio",

            "participacao_quantidade_percentual":
                "% das Vendas",

            "participacao_faturamento_percentual":
                "% do Faturamento",
        }
    )

    exibicao[
        "Faturamento"
    ] = exibicao[
        "Faturamento"
    ].apply(
        formatar_moeda
    )

    exibicao[
        "Ticket Médio"
    ] = exibicao[
        "Ticket Médio"
    ].apply(
        formatar_moeda
    )

    exibicao[
        "% das Vendas"
    ] = exibicao[
        "% das Vendas"
    ].apply(
        formatar_percentual
    )

    exibicao[
        "% do Faturamento"
    ] = exibicao[
        "% do Faturamento"
    ].apply(
        formatar_percentual
    )

    return exibicao


# ============================================================
# GERAR PDF PROFISSIONAL
# ============================================================

def gerar_pdf_formas_pagamento(
    data_inicio,
    data_fim,
    df,
    resumo,
    conferencia,
):

    # ========================================================
    # LINHAS DA TABELA
    # ========================================================

    linhas_pdf = []

    for _, row in df.iterrows():

        linhas_pdf.append(
            [
                row[
                    "forma_pagamento"
                ],

                int(
                    row[
                        "quantidade_vendas"
                    ]
                ),

                formatar_moeda(
                    row[
                        "faturamento"
                    ]
                ),

                formatar_moeda(
                    row[
                        "ticket_medio"
                    ]
                ),

                formatar_percentual(
                    row[
                        "participacao_quantidade_percentual"
                    ]
                ),

                formatar_percentual(
                    row[
                        "participacao_faturamento_percentual"
                    ]
                ),
            ]
        )

    # ========================================================
    # TABELA PDF
    # ========================================================

    tabela_pdf = criar_tabela_relatorio(
        [
            "Forma de pagamento",
            "Vendas",
            "Faturamento",
            "Ticket médio",
            "% vendas",
            "% faturamento",
        ],
        linhas_pdf,
        alinhamentos=[
            "LEFT",
            "CENTER",
            "RIGHT",
            "RIGHT",
            "RIGHT",
            "RIGHT",
        ],
    )

    # ========================================================
    # INDICADORES
    # ========================================================

    indicadores_pdf = [
        {
            "titulo":
                "Vendas",

            "valor":
                str(
                    int(
                        resumo.get(
                            "quantidade_vendas",
                            0,
                        )
                    )
                ),
        },

        {
            "titulo":
                "Faturamento",

            "valor":
                formatar_moeda(
                    resumo.get(
                        "faturamento",
                        0,
                    )
                ),
        },

        {
            "titulo":
                "Ticket médio",

            "valor":
                formatar_moeda(
                    resumo.get(
                        "ticket_medio",
                        0,
                    )
                ),
        },

        {
            "titulo":
                "Formas utilizadas",

            "valor":
                str(
                    int(
                        resumo.get(
                            "quantidade_formas",
                            0,
                        )
                    )
                ),
        },
    ]

    # ========================================================
    # CONFERÊNCIA
    # ========================================================

    if (
        conferencia
        and conferencia.get(
            "ok"
        )
    ):

        status_conferencia = (
            "OK - quantidade de vendas "
            "e faturamento conciliados."
        )

    else:

        status_conferencia = (
            "ATENÇÃO - foram encontradas "
            "diferenças na conferência."
        )

    texto_conferencia = (
        "Quantidade de vendas na distribuição: "
        f"{int(conferencia.get('quantidade_formas', 0))}. "
        "Quantidade de vendas na base: "
        f"{int(conferencia.get('quantidade_banco', 0))}. "
        "Faturamento da distribuição: "
        f"{formatar_moeda(conferencia.get('faturamento_formas', 0))}. "
        "Faturamento da base: "
        f"{formatar_moeda(conferencia.get('faturamento_banco', 0))}. "
        "Diferença financeira: "
        f"{formatar_moeda(conferencia.get('diferenca_faturamento', 0))}."
    )

    # ========================================================
    # DESTAQUES GERENCIAIS
    # ========================================================

    maior_faturamento = (
        df.sort_values(
            "faturamento",
            ascending=False,
        )
        .iloc[0]
    )

    maior_quantidade = (
        df.sort_values(
            "quantidade_vendas",
            ascending=False,
        )
        .iloc[0]
    )

    maior_ticket = (
        df.sort_values(
            "ticket_medio",
            ascending=False,
        )
        .iloc[0]
    )

    texto_analise = (
        "Maior faturamento: "
        f"{maior_faturamento['forma_pagamento']} "
        f"({formatar_moeda(maior_faturamento['faturamento'])}, "
        f"{formatar_percentual(maior_faturamento['participacao_faturamento_percentual'])} "
        "do faturamento). "
        "Maior número de vendas: "
        f"{maior_quantidade['forma_pagamento']} "
        f"({int(maior_quantidade['quantidade_vendas'])} vendas, "
        f"{formatar_percentual(maior_quantidade['participacao_quantidade_percentual'])} "
        "das vendas). "
        "Maior ticket médio: "
        f"{maior_ticket['forma_pagamento']} "
        f"({formatar_moeda(maior_ticket['ticket_medio'])})."
    )

    # ========================================================
    # SEÇÕES
    # ========================================================

    secoes_pdf = [
        {
            "titulo":
                "Distribuição por Forma de Pagamento",

            "texto":
                (
                    "Cada venda é contabilizada uma única vez. "
                    "O faturamento considera o valor final "
                    "registrado na venda."
                ),

            "tabela":
                tabela_pdf,
        },

        {
            "titulo":
                "Análise Gerencial",

            "texto":
                texto_analise,
        },

        {
            "titulo":
                "Conferência",

            "texto":
                texto_conferencia,

            "observacao":
                status_conferencia,
        },
    ]

    # ========================================================
    # GERAR PDF
    # ========================================================

    return gerar_pdf_profissional(
        titulo=(
            "Relatório de Vendas "
            "por Forma de Pagamento"
        ),
        periodo_inicio=data_inicio,
        periodo_fim=data_fim,
        indicadores=indicadores_pdf,
        secoes=secoes_pdf,
        orientacao="paisagem",
    )


# ============================================================
# TELA
# ============================================================

def tela_relatorio_formas_pagamento():

    st.title(
        "💳 Vendas por Forma de Pagamento"
    )

    st.caption(
        "Análise do faturamento, quantidade de vendas, "
        "ticket médio e participação de cada forma "
        "de pagamento."
    )

    st.divider()

    # ========================================================
    # PERÍODO
    # ========================================================

    hoje = date.today()

    primeiro_dia_mes = (
        hoje.replace(
            day=1
        )
    )

    col1, col2 = (
        st.columns(2)
    )

    with col1:

        data_inicio = st.date_input(
            "Data inicial",
            value=primeiro_dia_mes,
            format="DD/MM/YYYY",
            key=(
                "formas_pagamento_"
                "data_inicio"
            ),
        )

    with col2:

        data_fim = st.date_input(
            "Data final",
            value=hoje,
            format="DD/MM/YYYY",
            key=(
                "formas_pagamento_"
                "data_fim"
            ),
        )

    if data_inicio > data_fim:

        st.error(
            "A data inicial não pode ser "
            "maior que a data final."
        )

        return

    # ========================================================
    # DATA FINAL EXCLUSIVA
    # ========================================================

    data_fim_sql = (
        data_fim
        + timedelta(
            days=1
        )
    )

    st.divider()

    # ========================================================
    # CONSULTAR
    # ========================================================

    if st.button(
        "🔎 Gerar relatório",
        type="primary",
        use_container_width=True,
        key=(
            "botao_relatorio_"
            "formas_pagamento"
        ),
    ):

        with st.spinner(
            "Consultando vendas..."
        ):

            df = (
                obter_vendas_por_forma_pagamento(
                    data_inicio,
                    data_fim_sql,
                )
            )

            resumo = (
                obter_resumo_formas_pagamento(
                    data_inicio,
                    data_fim_sql,
                )
            )

            conferencia = (
                conferir_formas_pagamento(
                    data_inicio,
                    data_fim_sql,
                )
            )

        if (
            df is None
            or df.empty
        ):

            st.warning(
                "Nenhuma venda concluída "
                "foi encontrada no período."
            )

            return

        if resumo is None:

            st.error(
                "Não foi possível calcular "
                "o resumo do período."
            )

            return

        if conferencia is None:

            st.error(
                "Não foi possível realizar "
                "a conferência do relatório."
            )

            return

        # ====================================================
        # INDICADORES
        # ====================================================

        st.subheader(
            "Resumo do período"
        )

        quantidade_vendas = int(
            resumo.get(
                "quantidade_vendas",
                0,
            )
        )

        faturamento = float(
            resumo.get(
                "faturamento",
                0,
            )
        )

        ticket_medio = float(
            resumo.get(
                "ticket_medio",
                0,
            )
        )

        quantidade_formas = int(
            resumo.get(
                "quantidade_formas",
                0,
            )
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
            "Ticket Médio",
            formatar_moeda(
                ticket_medio
            ),
        )

        col4.metric(
            "Formas utilizadas",
            quantidade_formas,
        )

        st.divider()

        # ====================================================
        # TABELA
        # ====================================================

        st.subheader(
            "Distribuição por forma de pagamento"
        )

        df_exibicao = (
            preparar_dataframe_exibicao(
                df
            )
        )

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # ====================================================
        # DESTAQUES GERENCIAIS
        # ====================================================

        st.subheader(
            "Análise gerencial"
        )

        maior_faturamento = (
            df.sort_values(
                "faturamento",
                ascending=False,
            )
            .iloc[0]
        )

        maior_quantidade = (
            df.sort_values(
                "quantidade_vendas",
                ascending=False,
            )
            .iloc[0]
        )

        maior_ticket = (
            df.sort_values(
                "ticket_medio",
                ascending=False,
            )
            .iloc[0]
        )

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.markdown(
                "**Maior faturamento**"
            )

            st.write(
                maior_faturamento[
                    "forma_pagamento"
                ]
            )

            st.write(
                formatar_moeda(
                    maior_faturamento[
                        "faturamento"
                    ]
                )
            )

            st.caption(
                (
                    f"{formatar_percentual(maior_faturamento['participacao_faturamento_percentual'])} "
                    "do faturamento"
                )
            )

        with col2:

            st.markdown(
                "**Maior nº de vendas**"
            )

            st.write(
                maior_quantidade[
                    "forma_pagamento"
                ]
            )

            st.write(
                (
                    f"{int(maior_quantidade['quantidade_vendas'])} "
                    "vendas"
                )
            )

            st.caption(
                (
                    f"{formatar_percentual(maior_quantidade['participacao_quantidade_percentual'])} "
                    "das vendas"
                )
            )

        with col3:

            st.markdown(
                "**Maior ticket médio**"
            )

            st.write(
                maior_ticket[
                    "forma_pagamento"
                ]
            )

            st.write(
                formatar_moeda(
                    maior_ticket[
                        "ticket_medio"
                    ]
                )
            )

        st.divider()

        # ====================================================
        # CONFERÊNCIA
        # ====================================================

        st.subheader(
            "Conferência"
        )

        if conferencia.get(
            "ok"
        ):

            st.success(
                "Relatório conferido: "
                "a quantidade de vendas e o "
                "faturamento fecham com a "
                "base de vendas."
            )

        else:

            st.error(
                "Foi encontrada diferença "
                "na conferência. "
                "O relatório deve ser revisado."
            )

        col1, col2, col3 = (
            st.columns(3)
        )

        col1.metric(
            "Vendas conferidas",
            int(
                conferencia.get(
                    "quantidade_banco",
                    0,
                )
            ),
        )

        col2.metric(
            "Faturamento conferido",
            formatar_moeda(
                conferencia.get(
                    "faturamento_banco",
                    0,
                )
            ),
        )

        col3.metric(
            "Diferença",
            formatar_moeda(
                conferencia.get(
                    "diferenca_faturamento",
                    0,
                )
            ),
        )

        st.divider()

        # ====================================================
        # PDF
        # ====================================================

        st.subheader(
            "📄 Documento profissional"
        )

        try:

            pdf = (
                gerar_pdf_formas_pagamento(
                    data_inicio,
                    data_fim,
                    df,
                    resumo,
                    conferencia,
                )
            )

            st.download_button(
                "📥 Baixar relatório em PDF",
                data=pdf.getvalue(),
                file_name=(
                    "relatorio_vendas_forma_pagamento_"
                    f"{data_inicio.strftime('%Y%m%d')}_"
                    f"{data_fim.strftime('%Y%m%d')}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as erro:

            st.error(
                "Não foi possível gerar o PDF."
            )

            st.exception(
                erro
            )

        # ====================================================
        # METODOLOGIA
        # ====================================================

        with st.expander(
            "ℹ️ Critérios e metodologia"
        ):

            st.markdown(
                """
**Venda:** cada número de pedido é contabilizado uma
única vez.

**Faturamento:** utiliza o valor final registrado
na venda.

**Ticket médio:** faturamento da forma de pagamento
dividido pela quantidade de vendas daquela forma.

**% das vendas:** participação da forma de pagamento
na quantidade total de vendas.

**% do faturamento:** participação da forma de
pagamento no faturamento total do período.

**Conferência:** a soma das formas de pagamento é
comparada automaticamente com a quantidade e o
faturamento existentes diretamente na tabela de
vendas.
                """
            )