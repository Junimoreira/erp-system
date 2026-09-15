from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database.relatorios_clientes_db import (
    listar_vendas_por_cliente,
    obter_resumo_clientes,
    obter_vendas_sem_cliente,
    conferir_relatorio_clientes,
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
# AUXILIARES
# ============================================================

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

    try:
        valor = float(valor or 0)

    except Exception:
        valor = 0

    return (
        f"{valor:,.2f}%"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ============================================================
# PREPARAR DATAFRAME PARA TELA
# ============================================================

def preparar_dataframe_exibicao(df):

    if df is None or df.empty:
        return pd.DataFrame()

    exibicao = df.copy()

    exibicao = exibicao.rename(
        columns={
            "cliente":
                "Cliente",

            "quantidade_compras":
                "Compras",

            "total_gasto":
                "Total Gasto",

            "ticket_medio":
                "Ticket Médio",

            "primeira_compra":
                "Primeira Compra",

            "ultima_compra":
                "Última Compra",

            "recorrencia":
                "Classificação",
        }
    )

    exibicao["Total Gasto"] = (
        exibicao["Total Gasto"]
        .apply(formatar_moeda)
    )

    exibicao["Ticket Médio"] = (
        exibicao["Ticket Médio"]
        .apply(formatar_moeda)
    )

    exibicao["Primeira Compra"] = (
        exibicao["Primeira Compra"]
        .apply(formatar_data)
    )

    exibicao["Última Compra"] = (
        exibicao["Última Compra"]
        .apply(formatar_data)
    )

    colunas = [
        "Cliente",
        "Compras",
        "Total Gasto",
        "Ticket Médio",
        "Primeira Compra",
        "Última Compra",
        "Classificação",
    ]

    return exibicao[colunas]


# ============================================================
# GERAR PDF
# ============================================================

def gerar_pdf_vendas_clientes(
    data_inicio,
    data_fim,
    df_clientes,
    resumo,
    sem_cliente,
    conferencia,
):

    clientes_atendidos = inteiro_seguro(
        resumo.get(
            "clientes_atendidos"
        )
    )

    clientes_recorrentes = inteiro_seguro(
        resumo.get(
            "clientes_recorrentes"
        )
    )

    clientes_compra_unica = inteiro_seguro(
        resumo.get(
            "clientes_compra_unica"
        )
    )

    faturamento_identificado = numero_seguro(
        resumo.get(
            "faturamento_identificado"
        )
    )

    ticket_medio_cliente = numero_seguro(
        resumo.get(
            "ticket_medio_cliente"
        )
    )

    vendas_identificadas = inteiro_seguro(
        resumo.get(
            "quantidade_vendas_identificadas"
        )
    )

    vendas_sem_cliente = inteiro_seguro(
        sem_cliente.get(
            "quantidade_vendas"
        )
    )

    faturamento_sem_cliente = numero_seguro(
        sem_cliente.get(
            "faturamento"
        )
    )

    total_vendas = (
        vendas_identificadas
        +
        vendas_sem_cliente
    )

    faturamento_total = (
        faturamento_identificado
        +
        faturamento_sem_cliente
    )

    percentual_recorrentes = 0

    if clientes_atendidos > 0:

        percentual_recorrentes = (
            clientes_recorrentes
            /
            clientes_atendidos
            *
            100
        )

    percentual_identificado = 0

    if total_vendas > 0:

        percentual_identificado = (
            vendas_identificadas
            /
            total_vendas
            *
            100
        )

    # ========================================================
    # INDICADORES
    # ========================================================

    indicadores = [
        {
            "titulo":
                "Clientes atendidos",

            "valor":
                str(
                    clientes_atendidos
                ),
        },
        {
            "titulo":
                "Clientes recorrentes",

            "valor":
                str(
                    clientes_recorrentes
                ),
        },
        {
            "titulo":
                "Faturamento identificado",

            "valor":
                formatar_moeda(
                    faturamento_identificado
                ),
        },
        {
            "titulo":
                "Ticket médio / cliente",

            "valor":
                formatar_moeda(
                    ticket_medio_cliente
                ),
        },
    ]

    # ========================================================
    # TABELA PRINCIPAL
    # ========================================================

    linhas_clientes = []

    if (
        df_clientes is not None
        and not df_clientes.empty
    ):

        for _, linha in df_clientes.iterrows():

            linhas_clientes.append(
                [
                    linha.get(
                        "cliente",
                        "",
                    ),

                    inteiro_seguro(
                        linha.get(
                            "quantidade_compras"
                        )
                    ),

                    formatar_moeda(
                        numero_seguro(
                            linha.get(
                                "total_gasto"
                            )
                        )
                    ),

                    formatar_moeda(
                        numero_seguro(
                            linha.get(
                                "ticket_medio"
                            )
                        )
                    ),

                    formatar_data(
                        linha.get(
                            "primeira_compra"
                        )
                    ),

                    formatar_data(
                        linha.get(
                            "ultima_compra"
                        )
                    ),

                    linha.get(
                        "recorrencia",
                        "",
                    ),
                ]
            )

    tabela_clientes = criar_tabela_relatorio(
        colunas=[
            "Cliente",
            "Compras",
            "Total gasto",
            "Ticket médio",
            "Primeira compra",
            "Última compra",
            "Classificação",
        ],
        linhas=linhas_clientes,
        larguras=[
            175,
            48,
            75,
            75,
            78,
            78,
            82,
        ],
        alinhamentos=[
            "LEFT",
            "CENTER",
            "RIGHT",
            "RIGHT",
            "CENTER",
            "CENTER",
            "CENTER",
        ],
    )

    # ========================================================
    # ANÁLISE DO PERFIL
    # ========================================================

    texto_perfil = (
        f"No período foram atendidos "
        f"{clientes_atendidos} clientes identificados. "
        f"Desses, {clientes_recorrentes} realizaram "
        f"duas ou mais compras e "
        f"{clientes_compra_unica} realizaram apenas "
        f"uma compra. A taxa de recorrência foi de "
        f"{formatar_percentual(percentual_recorrentes)}."
    )

    # ========================================================
    # VENDAS IDENTIFICADAS / NÃO IDENTIFICADAS
    # ========================================================

    linhas_identificacao = [
        [
            "Clientes identificados",
            vendas_identificadas,
            formatar_moeda(
                faturamento_identificado
            ),
        ],
        [
            "Consumidor não identificado",
            vendas_sem_cliente,
            formatar_moeda(
                faturamento_sem_cliente
            ),
        ],
        [
            "Total",
            total_vendas,
            formatar_moeda(
                faturamento_total
            ),
        ],
    ]

    tabela_identificacao = criar_tabela_relatorio(
        colunas=[
            "Tipo de atendimento",
            "Vendas",
            "Faturamento",
        ],
        linhas=linhas_identificacao,
        larguras=[
            220,
            90,
            110,
        ],
        alinhamentos=[
            "LEFT",
            "CENTER",
            "RIGHT",
        ],
    )

    texto_identificacao = (
        f"{vendas_identificadas} das "
        f"{total_vendas} vendas do período "
        f"({formatar_percentual(percentual_identificado)}) "
        f"possuem um cliente individualmente identificado "
        f"no ERP. As vendas vinculadas ao cadastro genérico "
        f"'Consumidor' são mantidas integralmente no "
        f"faturamento, mas não são consideradas na análise "
        f"de fidelização ou ranking de clientes."
    )

    # ========================================================
    # TOP 10
    # ========================================================

    linhas_top = []

    if (
        df_clientes is not None
        and not df_clientes.empty
    ):

        top_clientes = (
            df_clientes
            .head(10)
        )

        for _, linha in top_clientes.iterrows():

            linhas_top.append(
                [
                    linha.get(
                        "cliente",
                        "",
                    ),

                    inteiro_seguro(
                        linha.get(
                            "quantidade_compras"
                        )
                    ),

                    formatar_moeda(
                        numero_seguro(
                            linha.get(
                                "total_gasto"
                            )
                        )
                    ),

                    formatar_moeda(
                        numero_seguro(
                            linha.get(
                                "ticket_medio"
                            )
                        )
                    ),
                ]
            )

    tabela_top = criar_tabela_relatorio(
        colunas=[
            "Cliente",
            "Compras",
            "Total gasto",
            "Ticket médio",
        ],
        linhas=linhas_top,
        larguras=[
            245,
            70,
            100,
            100,
        ],
        alinhamentos=[
            "LEFT",
            "CENTER",
            "RIGHT",
            "RIGHT",
        ],
    )

    # ========================================================
    # CONFERÊNCIA
    # ========================================================

    conferencia_ok = bool(
        conferencia.get(
            "ok",
            False,
        )
    )

    texto_conferencia = (
        f"Vendas apuradas no relatório: "
        f"{inteiro_seguro(conferencia.get('vendas_relatorio'))}. "
        f"Vendas registradas na base: "
        f"{inteiro_seguro(conferencia.get('vendas_banco'))}. "
        f"Faturamento apurado no relatório: "
        f"{formatar_moeda(numero_seguro(conferencia.get('faturamento_relatorio')))}. "
        f"Faturamento registrado na base: "
        f"{formatar_moeda(numero_seguro(conferencia.get('faturamento_banco')))}. "
        f"Diferença: "
        f"{formatar_moeda(numero_seguro(conferencia.get('diferenca')))}."
    )

    observacao_conferencia = (
        "OK - quantidade de vendas e faturamento conciliados."
        if conferencia_ok
        else
        "ATENÇÃO - foi identificada divergência na conferência."
    )

    secoes = [
        {
            "titulo":
                "Perfil da Carteira de Clientes",

            "texto":
                texto_perfil,

            "tabela":
                tabela_top,

            "observacao":
                (
                    "O ranking considera somente clientes "
                    "individualmente identificados e utiliza "
                    "o valor líquido efetivamente vendido."
                ),
        },
        {
            "titulo":
                "Identificação das Vendas",

            "texto":
                texto_identificacao,

            "tabela":
                tabela_identificacao,
        },
        {
            "titulo":
                "Detalhamento por Cliente",

            "texto":
                (
                    "Relação completa dos clientes "
                    "identificados no período, ordenada "
                    "pelo maior valor total de compras."
                ),

            "tabela":
                tabela_clientes,
        },
        {
            "titulo":
                "Conferência",

            "texto":
                texto_conferencia,

            "observacao":
                observacao_conferencia,
        },
    ]

    return gerar_pdf_profissional(
        titulo=(
            "Relatório de Vendas por Cliente"
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

def tela_relatorio_vendas_clientes():

    st.title(
        "👥 Vendas por Cliente"
    )

    st.caption(
        "Análise de clientes, recorrência, "
        "faturamento, ticket médio e frequência de compras."
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
            key="clientes_relatorio_data_inicio",
        )

    with col2:

        data_fim = st.date_input(
            "Data final",
            value=hoje,
            format="DD/MM/YYYY",
            key="clientes_relatorio_data_fim",
        )

    if data_inicio > data_fim:

        st.error(
            "A data inicial não pode ser "
            "maior que a data final."
        )

        return

    data_fim_sql = (
        data_fim
        +
        timedelta(
            days=1
        )
    )

    st.divider()

    # ========================================================
    # GERAR RELATÓRIO
    # ========================================================

    if st.button(
        "🔎 Gerar relatório",
        type="primary",
        use_container_width=True,
        key="btn_relatorio_clientes",
    ):

        with st.spinner(
            "Consultando clientes e vendas..."
        ):

            df_clientes = (
                listar_vendas_por_cliente(
                    data_inicio,
                    data_fim_sql,
                )
            )

            resumo = (
                obter_resumo_clientes(
                    data_inicio,
                    data_fim_sql,
                )
            )

            sem_cliente = (
                obter_vendas_sem_cliente(
                    data_inicio,
                    data_fim_sql,
                )
            )

            conferencia = (
                conferir_relatorio_clientes(
                    data_inicio,
                    data_fim_sql,
                )
            )

        if (
            df_clientes is None
            or df_clientes.empty
        ):

            st.warning(
                "Nenhuma venda com cliente "
                "identificado foi encontrada "
                "no período selecionado."
            )

            return

        # ====================================================
        # INDICADORES
        # ====================================================

        clientes_atendidos = inteiro_seguro(
            resumo.get(
                "clientes_atendidos"
            )
        )

        clientes_recorrentes = inteiro_seguro(
            resumo.get(
                "clientes_recorrentes"
            )
        )

        clientes_compra_unica = inteiro_seguro(
            resumo.get(
                "clientes_compra_unica"
            )
        )

        faturamento_identificado = numero_seguro(
            resumo.get(
                "faturamento_identificado"
            )
        )

        ticket_cliente = numero_seguro(
            resumo.get(
                "ticket_medio_cliente"
            )
        )

        percentual_recorrencia = 0

        if clientes_atendidos > 0:

            percentual_recorrencia = (
                clientes_recorrentes
                /
                clientes_atendidos
                *
                100
            )

        c1, c2, c3, c4 = (
            st.columns(4)
        )

        c1.metric(
            "Clientes atendidos",
            clientes_atendidos,
        )

        c2.metric(
            "Clientes recorrentes",
            clientes_recorrentes,
        )

        c3.metric(
            "Faturamento identificado",
            formatar_moeda(
                faturamento_identificado
            ),
        )

        c4.metric(
            "Ticket médio / cliente",
            formatar_moeda(
                ticket_cliente
            ),
        )

        st.caption(
            f"Clientes de compra única: "
            f"{clientes_compra_unica} | "
            f"Taxa de recorrência: "
            f"{formatar_percentual(percentual_recorrencia)}"
        )

        # ====================================================
        # IDENTIFICAÇÃO DE VENDAS
        # ====================================================

        st.subheader(
            "Identificação das vendas"
        )

        vendas_identificadas = inteiro_seguro(
            resumo.get(
                "quantidade_vendas_identificadas"
            )
        )

        vendas_genericas = inteiro_seguro(
            sem_cliente.get(
                "quantidade_vendas"
            )
        )

        faturamento_generico = numero_seguro(
            sem_cliente.get(
                "faturamento"
            )
        )

        i1, i2 = (
            st.columns(2)
        )

        i1.metric(
            "Vendas com cliente identificado",
            vendas_identificadas,
        )

        i2.metric(
            "Vendas como Consumidor",
            vendas_genericas,
            help=(
                "Vendas sem identificação individual. "
                "Continuam normalmente no faturamento."
            ),
        )

        st.info(
            f"As {vendas_genericas} vendas registradas "
            f"como Consumidor representam "
            f"{formatar_moeda(faturamento_generico)}. "
            f"Elas não entram no ranking nem na "
            f"taxa de recorrência dos clientes."
        )

        # ====================================================
        # TOP CLIENTES
        # ====================================================

        st.subheader(
            "🏆 Principais clientes"
        )

        top10 = (
            df_clientes
            .head(10)
        )

        st.dataframe(
            preparar_dataframe_exibicao(
                top10
            ),
            use_container_width=True,
            hide_index=True,
        )

        # ====================================================
        # TODOS OS CLIENTES
        # ====================================================

        st.subheader(
            "📋 Todos os clientes no período"
        )

        st.dataframe(
            preparar_dataframe_exibicao(
                df_clientes
            ),
            use_container_width=True,
            hide_index=True,
        )

        # ====================================================
        # CONFERÊNCIA
        # ====================================================

        st.subheader(
            "✅ Conferência"
        )

        if conferencia.get(
            "ok"
        ):

            st.success(
                "Quantidade de vendas e faturamento "
                "conciliados com a base do ERP."
            )

        else:

            st.error(
                "Foi encontrada divergência entre "
                "o relatório e a base do ERP."
            )

        st.write(
            f"**Vendas no relatório:** "
            f"{inteiro_seguro(conferencia.get('vendas_relatorio'))}"
        )

        st.write(
            f"**Vendas na base:** "
            f"{inteiro_seguro(conferencia.get('vendas_banco'))}"
        )

        st.write(
            f"**Faturamento no relatório:** "
            f"{formatar_moeda(numero_seguro(conferencia.get('faturamento_relatorio')))}"
        )

        st.write(
            f"**Faturamento na base:** "
            f"{formatar_moeda(numero_seguro(conferencia.get('faturamento_banco')))}"
        )

        # ====================================================
        # PDF
        # ====================================================

        try:

            pdf = gerar_pdf_vendas_clientes(
                data_inicio=data_inicio,
                data_fim=data_fim,
                df_clientes=df_clientes,
                resumo=resumo,
                sem_cliente=sem_cliente,
                conferencia=conferencia,
            )

            nome_arquivo = (
                "relatorio_vendas_clientes_"
                f"{data_inicio:%Y%m%d}_"
                f"{data_fim:%Y%m%d}.pdf"
            )

            st.download_button(
                label="📄 Baixar relatório em PDF",
                data=pdf,
                file_name=nome_arquivo,
                mime="application/pdf",
                use_container_width=True,
                key="download_relatorio_clientes",
            )

        except Exception as erro:

            st.error(
                "Não foi possível gerar o PDF."
            )

            st.exception(
                erro
            )