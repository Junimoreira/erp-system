from datetime import date, datetime, timedelta
import calendar

import pandas as pd
import streamlit as st

from database.relatorios_vendas_db import (
    obter_resumo_mensal,
    obter_resumo_geral,
    obter_clientes_recorrentes,
    obter_novos_clientes,
    obter_top_produtos,
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
# FUNÇÕES AUXILIARES
# ============================================================

MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def nome_mes(data_valor):
    return (
        f"{MESES_PT[data_valor.month]}/"
        f"{data_valor.year}"
    )


def inicio_mes(data_valor):
    return date(
        data_valor.year,
        data_valor.month,
        1,
    )


def primeiro_dia_mes_seguinte(data_valor):

    if data_valor.month == 12:

        return date(
            data_valor.year + 1,
            1,
            1,
        )

    return date(
        data_valor.year,
        data_valor.month + 1,
        1,
    )


def ultimo_dia_mes(data_valor):

    ultimo = calendar.monthrange(
        data_valor.year,
        data_valor.month,
    )[1]

    return date(
        data_valor.year,
        data_valor.month,
        ultimo,
    )


def numero_seguro(valor):
    try:
        return float(valor or 0)
    except Exception:
        return 0.0


def inteiro_seguro(valor):
    try:
        return int(valor or 0)
    except Exception:
        return 0


def formatar_percentual(valor):

    if valor is None:
        return "Não calculável"

    try:

        if pd.isna(valor):
            return "Não calculável"

        return (
            f"{float(valor):,.2f}%"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:
        return "Não calculável"


# ============================================================
# PREPARAR DADOS DO PDF
# ============================================================

def gerar_pdf_gerencial_vendas(
    data_inicio,
    data_fim,
    resumo_mensal,
    resumo_geral,
    recorrentes,
    novos,
    top_produtos,
):

    # ========================================================
    # MÉDIAS
    # ========================================================

    quantidade_meses = len(
        resumo_mensal
    )

    media_vendas = 0
    media_clientes = 0
    media_faturamento = 0

    if quantidade_meses > 0:

        media_vendas = (
            resumo_mensal[
                "quantidade_vendas"
            ].sum()
            / quantidade_meses
        )

        media_clientes = (
            resumo_mensal[
                "clientes_unicos"
            ].sum()
            / quantidade_meses
        )

        media_faturamento = (
            resumo_mensal[
                "faturamento"
            ].sum()
            / quantidade_meses
        )

    # ========================================================
    # TABELA MENSAL
    # ========================================================

    linhas_mensais = []

    for _, row in resumo_mensal.iterrows():

        mes_data = row["mes"]

        linhas_mensais.append(
            [
                nome_mes(
                    mes_data
                ),
                inteiro_seguro(
                    row[
                        "quantidade_vendas"
                    ]
                ),
                inteiro_seguro(
                    row[
                        "clientes_unicos"
                    ]
                ),
                inteiro_seguro(
                    row[
                        "vendas_sem_cliente"
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
            ]
        )

    tabela_mensal = (
        criar_tabela_relatorio(
            [
                "Mês",
                "Vendas",
                "Clientes",
                "Sem identificação",
                "Faturamento",
                "Ticket médio",
            ],
            linhas_mensais,
            alinhamentos=[
                "LEFT",
                "CENTER",
                "CENTER",
                "CENTER",
                "RIGHT",
                "RIGHT",
            ],
        )
    )

    # ========================================================
    # CLIENTES RECORRENTES
    # ========================================================

    linhas_recorrentes = []

    for _, row in recorrentes.iterrows():

        linhas_recorrentes.append(
            [
                row["cliente"],
                inteiro_seguro(
                    row[
                        "quantidade_compras"
                    ]
                ),
                formatar_moeda(
                    row[
                        "total_gasto"
                    ]
                ),
                formatar_moeda(
                    row[
                        "ticket_medio"
                    ]
                ),
            ]
        )

    tabela_recorrentes = (
        criar_tabela_relatorio(
            [
                "Cliente",
                "Compras",
                "Total gasto",
                "Ticket médio",
            ],
            linhas_recorrentes,
            alinhamentos=[
                "LEFT",
                "CENTER",
                "RIGHT",
                "RIGHT",
            ],
        )
        if linhas_recorrentes
        else None
    )

    # ========================================================
    # NOVOS CLIENTES
    # ========================================================

    linhas_novos = []

    for _, row in novos.iterrows():

        linhas_novos.append(
            [
                row["cliente"],
                formatar_data(
                    row[
                        "primeira_compra"
                    ]
                ),
            ]
        )

    tabela_novos = (
        criar_tabela_relatorio(
            [
                "Cliente",
                "Primeira compra",
            ],
            linhas_novos,
            alinhamentos=[
                "LEFT",
                "CENTER",
            ],
        )
        if linhas_novos
        else None
    )

    # ========================================================
    # TOP PRODUTOS
    # ========================================================

    linhas_top = []

    for _, row in top_produtos.iterrows():

        custo = numero_seguro(
            row.get(
                "custo_atual"
            )
        )

        margem_bruta = row.get(
            "margem_bruta_estimada_percentual"
        )

        margem_liquida = row.get(
            "margem_liquida_gerencial_estimada_percentual"
        )

        if custo <= 0:

            margem_bruta_texto = (
                "Não calculável - "
                "custo não informado"
            )

            margem_liquida_texto = (
                "Não calculável - "
                "custo não informado"
            )

        else:

            margem_bruta_texto = (
                formatar_percentual(
                    margem_bruta
                )
            )

            margem_liquida_texto = (
                formatar_percentual(
                    margem_liquida
                )
            )

        linhas_top.append(
            [
                row["produto"],
                inteiro_seguro(
                    row[
                        "quantidade_vendida"
                    ]
                ),
                inteiro_seguro(
                    row[
                        "quantidade_pedidos"
                    ]
                ),
                formatar_moeda(
                    row[
                        "faturamento_produto"
                    ]
                ),
                formatar_moeda(
                    row[
                        "preco_medio_praticado"
                    ]
                ),
                formatar_moeda(
                    row[
                        "ticket_medio_produto_por_pedido"
                    ]
                ),
                margem_bruta_texto,
                margem_liquida_texto,
            ]
        )

    tabela_top = (
        criar_tabela_relatorio(
            [
                "Produto / Serviço",
                "Qtd.",
                "Pedidos",
                "Faturamento",
                "Preço médio",
                "Ticket / pedido",
                "Margem bruta estimada",
                "Margem líquida gerencial",
            ],
            linhas_top,
            alinhamentos=[
                "LEFT",
                "CENTER",
                "CENTER",
                "RIGHT",
                "RIGHT",
                "RIGHT",
                "RIGHT",
                "RIGHT",
            ],
        )
    )

    # ========================================================
    # MÊS FINAL DA ANÁLISE
    # ========================================================

    mes_final_texto = (
        nome_mes(
            data_fim
        )
    )

    # ========================================================
    # INDICADORES PRINCIPAIS
    # ========================================================

    indicadores = [
        {
            "titulo":
                "Média mensal de vendas",
            "valor":
                f"{media_vendas:.2f}"
                .replace(".", ","),
        },
        {
            "titulo":
                "Média mensal de clientes",
            "valor":
                f"{media_clientes:.2f}"
                .replace(".", ","),
        },
        {
            "titulo":
                "Faturamento médio mensal",
            "valor":
                formatar_moeda(
                    media_faturamento
                ),
        },
        {
            "titulo":
                "Ticket médio do período",
            "valor":
                formatar_moeda(
                    resumo_geral.get(
                        "ticket_medio",
                        0,
                    )
                ),
        },
        {
            "titulo":
                f"Recorrentes - {mes_final_texto}",
            "valor":
                str(
                    len(
                        recorrentes
                    )
                ),
        },
        {
            "titulo":
                f"Novos - {mes_final_texto}",
            "valor":
                str(
                    len(
                        novos
                    )
                ),
        },
    ]

    # ========================================================
    # SEÇÕES
    # ========================================================

    secoes = [
        {
            "titulo":
                "Desempenho Mensal",

            "texto":
                (
                    "Os indicadores de vendas utilizam "
                    "o número do pedido como unidade de venda. "
                    "Um pedido contendo vários produtos "
                    "continua sendo contabilizado como uma "
                    "única venda."
                ),

            "tabela":
                tabela_mensal,
        },

        {
            "titulo":
                (
                    "Clientes Recorrentes - "
                    f"{mes_final_texto}"
                ),

            "texto":
                (
                    f"Foram identificados "
                    f"{len(recorrentes)} clientes "
                    "com mais de uma compra/pedido "
                    "distinto no mês."
                ),

            "tabela":
                tabela_recorrentes,
        },

        {
            "titulo":
                (
                    "Novos Clientes - "
                    f"{mes_final_texto}"
                ),

            "texto":
                (
                    f"Foram identificados "
                    f"{len(novos)} clientes cuja "
                    "primeira venda concluída registrada "
                    "no ERP ocorreu no mês analisado."
                ),

            "tabela":
                tabela_novos,

            "observacao":
                (
                    "A classificação de novo cliente "
                    "considera o histórico de vendas "
                    "disponível no ERP."
                ),
        },

        {
            "titulo":
                "Produtos / Serviços Mais Vendidos",

            "texto":
                (
                    "Ranking calculado pelo volume "
                    "total de unidades vendidas no "
                    "período selecionado."
                ),

            "tabela":
                tabela_top,

            "observacao":
                (
                    "Margem bruta estimada: receita menos "
                    "o custo atual cadastrado do produto. "
                    "Margem líquida gerencial estimada: "
                    "considera também o imposto padrão atual "
                    "e a taxa de cartão padrão somente sobre "
                    "as vendas realizadas em cartão. "
                    "Não inclui rateio de despesas fixas nem "
                    "frete sem vínculo direto com a venda. "
                    "Este indicador é gerencial e não equivale "
                    "à margem líquida contábil da empresa."
                ),
        },
    ]

    return gerar_pdf_profissional(
        titulo=(
            "Relatório Gerencial de "
            "Vendas e Clientes"
        ),
        periodo_inicio=data_inicio,
        periodo_fim=data_fim,
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )


# ============================================================
# TELA PRINCIPAL
# ============================================================

def tela_relatorio_gerencial_vendas():

    st.title(
        "📊 Relatório Gerencial de Vendas e Clientes"
    )

    st.caption(
        "Análise profissional de vendas, clientes, "
        "recorrência, ticket médio e produtos."
    )

    # ========================================================
    # FILTROS
    # ========================================================

    st.subheader(
        "Período de análise"
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
                "relatorio_vendas_"
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
                "relatorio_vendas_"
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
    # LIMITE FINAL EXCLUSIVO PARA SQL
    #
    # Exemplo:
    # período informado até 31/08/2026
    # consulta utiliza < 01/09/2026
    #
    # st.date_input já retorna datetime.date.
    # Por isso NÃO usamos .date() aqui.
    # ========================================================

    data_fim_sql = (
        data_fim
        + timedelta(
            days=1
        )
    )

    # ========================================================
    # MÊS FINAL PARA RECORRÊNCIA E NOVOS CLIENTES
    # ========================================================

    mes_analise_inicio = (
        inicio_mes(
            data_fim
        )
    )

    mes_analise_fim = (
        primeiro_dia_mes_seguinte(
            data_fim
        )
    )

    # ========================================================
    # GERAR RELATÓRIO
    # ========================================================

    if st.button(
        "🔎 Gerar relatório",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Consultando dados..."
        ):

            resumo_mensal = (
                obter_resumo_mensal(
                    data_inicio,
                    data_fim_sql,
                )
            )

            resumo_geral = (
                obter_resumo_geral(
                    data_inicio,
                    data_fim_sql,
                )
            )

            recorrentes = (
                obter_clientes_recorrentes(
                    mes_analise_inicio,
                    mes_analise_fim,
                )
            )

            novos = (
                obter_novos_clientes(
                    mes_analise_inicio,
                    mes_analise_fim,
                )
            )

            top_produtos = (
                obter_top_produtos(
                    data_inicio,
                    data_fim_sql,
                    3,
                )
            )

        if (
            resumo_mensal is None
            or resumo_mensal.empty
            or resumo_geral is None
        ):

            st.warning(
                "Nenhuma venda encontrada "
                "no período selecionado."
            )

            return

        # ====================================================
        # MÉDIAS
        # ====================================================

        quantidade_meses = len(
            resumo_mensal
        )

        media_vendas = (
            resumo_mensal[
                "quantidade_vendas"
            ].sum()
            / quantidade_meses
        )

        media_clientes = (
            resumo_mensal[
                "clientes_unicos"
            ].sum()
            / quantidade_meses
        )

        media_faturamento = (
            resumo_mensal[
                "faturamento"
            ].sum()
            / quantidade_meses
        )

        # ====================================================
        # INDICADORES PRINCIPAIS
        # ====================================================

        st.divider()

        st.subheader(
            "Resumo executivo"
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        col1.metric(
            "Média mensal de vendas",
            (
                f"{media_vendas:.2f}"
                .replace(
                    ".",
                    ",",
                )
            ),
        )

        col2.metric(
            "Média mensal de clientes",
            (
                f"{media_clientes:.2f}"
                .replace(
                    ".",
                    ",",
                )
            ),
        )

        col3.metric(
            "Faturamento médio mensal",
            formatar_moeda(
                media_faturamento
            ),
        )

        col4.metric(
            "Ticket médio do período",
            formatar_moeda(
                resumo_geral.get(
                    "ticket_medio",
                    0,
                )
            ),
        )

        col4, col5, col6 = (
            st.columns(3)
        )

        col4.metric(
            "Vendas no período",
            inteiro_seguro(
                resumo_geral.get(
                    "quantidade_vendas"
                )
            ),
        )

        col5.metric(
            (
                "Clientes recorrentes - "
                f"{nome_mes(data_fim)}"
            ),
            len(
                recorrentes
            ),
        )

        col6.metric(
            (
                "Novos clientes - "
                f"{nome_mes(data_fim)}"
            ),
            len(
                novos
            ),
        )

        st.caption(
            (
                "Vendas sem cliente identificado "
                f"no período: "
                f"{inteiro_seguro(resumo_geral.get('vendas_sem_cliente'))}"
            )
        )

        # ====================================================
        # DESEMPENHO MENSAL
        # ====================================================

        st.divider()

        st.subheader(
            "📅 Desempenho mensal"
        )

        df_mensal = (
            resumo_mensal.copy()
        )

        df_mensal[
            "Mês"
        ] = df_mensal[
            "mes"
        ].apply(
            nome_mes
        )

        df_mensal[
            "Faturamento"
        ] = df_mensal[
            "faturamento"
        ].apply(
            formatar_moeda
        )

        df_mensal[
            "Ticket Médio"
        ] = df_mensal[
            "ticket_medio"
        ].apply(
            formatar_moeda
        )

        df_mensal = df_mensal[
            [
                "Mês",
                "quantidade_vendas",
                "clientes_unicos",
                "vendas_sem_cliente",
                "Faturamento",
                "Ticket Médio",
            ]
        ]

        df_mensal.columns = [
            "Mês",
            "Vendas",
            "Clientes únicos",
            "Sem identificação",
            "Faturamento",
            "Ticket médio",
        ]

        st.dataframe(
            df_mensal,
            use_container_width=True,
            hide_index=True,
        )

        # ====================================================
        # RECORRÊNCIA
        # ====================================================

        st.divider()

        st.subheader(
            (
                "🔁 Clientes recorrentes - "
                f"{nome_mes(data_fim)}"
            )
        )

        if recorrentes.empty:

            st.info(
                "Nenhum cliente identificado "
                "comprou mais de uma vez no mês."
            )

        else:

            df_recorrentes = (
                recorrentes.copy()
            )

            df_recorrentes[
                "total_gasto"
            ] = df_recorrentes[
                "total_gasto"
            ].apply(
                formatar_moeda
            )

            df_recorrentes[
                "ticket_medio"
            ] = df_recorrentes[
                "ticket_medio"
            ].apply(
                formatar_moeda
            )

            df_recorrentes = (
                df_recorrentes[
                    [
                        "cliente",
                        "quantidade_compras",
                        "total_gasto",
                        "ticket_medio",
                    ]
                ]
            )

            df_recorrentes.columns = [
                "Cliente",
                "Compras",
                "Total gasto",
                "Ticket médio",
            ]

            st.dataframe(
                df_recorrentes,
                use_container_width=True,
                hide_index=True,
            )

        # ====================================================
        # NOVOS CLIENTES
        # ====================================================

        st.divider()

        st.subheader(
            (
                "🆕 Novos clientes - "
                f"{nome_mes(data_fim)}"
            )
        )

        if novos.empty:

            st.info(
                "Nenhum novo cliente "
                "identificado no mês."
            )

        else:

            df_novos = (
                novos.copy()
            )

            df_novos[
                "Primeira compra"
            ] = df_novos[
                "primeira_compra"
            ].apply(
                formatar_data
            )

            df_novos = (
                df_novos[
                    [
                        "cliente",
                        "Primeira compra",
                    ]
                ]
            )

            df_novos.columns = [
                "Cliente",
                "Primeira compra",
            ]

            st.dataframe(
                df_novos,
                use_container_width=True,
                hide_index=True,
            )

        # ====================================================
        # TOP 3
        # ====================================================

        st.divider()

        st.subheader(
            "🏆 Top 3 produtos / serviços"
        )

        if top_produtos.empty:

            st.info(
                "Nenhum produto encontrado."
            )

        else:

            linhas_tela = []

            for _, row in (
                top_produtos.iterrows()
            ):

                custo = numero_seguro(
                    row.get(
                        "custo_atual"
                    )
                )

                if custo <= 0:

                    margem_bruta = (
                        "Não calculável - "
                        "custo não informado"
                    )

                    margem_liquida = (
                        "Não calculável - "
                        "custo não informado"
                    )

                else:

                    margem_bruta = (
                        formatar_percentual(
                            row.get(
                                "margem_bruta_estimada_percentual"
                            )
                        )
                    )

                    margem_liquida = (
                        formatar_percentual(
                            row.get(
                                "margem_liquida_gerencial_estimada_percentual"
                            )
                        )
                    )

                linhas_tela.append(
                    {
                        "Produto / Serviço":
                            row[
                                "produto"
                            ],

                        "Qtd. vendida":
                            inteiro_seguro(
                                row[
                                    "quantidade_vendida"
                                ]
                            ),

                        "Pedidos":
                            inteiro_seguro(
                                row[
                                    "quantidade_pedidos"
                                ]
                            ),

                        "Faturamento":
                            formatar_moeda(
                                row[
                                    "faturamento_produto"
                                ]
                            ),

                        "Preço médio":
                            formatar_moeda(
                                row[
                                    "preco_medio_praticado"
                                ]
                            ),

                        "Ticket / pedido":
                            formatar_moeda(
                                row[
                                    "ticket_medio_produto_por_pedido"
                                ]
                            ),

                        "Margem bruta estimada":
                            margem_bruta,

                        "Margem líquida gerencial":
                            margem_liquida,
                    }
                )

            st.dataframe(
                pd.DataFrame(
                    linhas_tela
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.caption(
            "Margem bruta estimada: receita menos "
            "o custo atual cadastrado do produto. "
            "Margem líquida gerencial estimada: "
            "considera também o imposto padrão atual "
            "e a taxa de cartão padrão somente sobre "
            "as vendas realizadas em cartão. "
            "Não inclui rateio de despesas fixas nem "
            "frete sem vínculo direto com a venda e "
            "não representa margem líquida contábil."
        )

        # ====================================================
        # PDF PROFISSIONAL
        # ====================================================

        st.divider()

        st.subheader(
            "📄 Documento profissional"
        )

        pdf = (
            gerar_pdf_gerencial_vendas(
                data_inicio,
                data_fim,
                resumo_mensal,
                resumo_geral,
                recorrentes,
                novos,
                top_produtos,
            )
        )

        nome_pdf = (
            "relatorio_gerencial_vendas_"
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
**Venda:** cada número de pedido/venda é
contabilizado uma única vez, independentemente
da quantidade de produtos do pedido.

**Cliente atendido:** cliente identificado único
que realizou compra no período.

**Venda sem identificação:** pedido associado a
cliente genérico, como Consumidor, ou sem cliente
individual identificado.

**Cliente recorrente:** cliente identificado com
dois ou mais pedidos diferentes no mês analisado.

**Novo cliente:** cliente identificado cuja primeira
venda concluída disponível no histórico do ERP ocorreu
no mês analisado.

**Top produtos:** classificados pela quantidade total
de unidades vendidas.

**Margem bruta estimada:** utiliza o custo atual
cadastrado do produto e representa a receita do item
menos o custo estimado das unidades vendidas.

**Margem líquida gerencial estimada:** parte da receita
dos itens e deduz o custo atual cadastrado, o imposto
padrão atual configurado no ERP e a taxa de cartão
padrão atual somente sobre os itens vendidos em cartão.
O frete padrão utilizado na formação de preço não
é abatido automaticamente, pois não representa
necessariamente frete efetivamente ocorrido em cada
venda. Também não há rateio de despesas fixas ou
operacionais. Portanto, este indicador é gerencial
e não equivale à margem líquida contábil da empresa.
                """
            )
