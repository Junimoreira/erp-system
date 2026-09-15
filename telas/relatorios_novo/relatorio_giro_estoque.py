import pandas as pd
import streamlit as st

from database.relatorios_giro_estoque_db import (
    listar_giro_estoque,
    obter_resumo_giro_estoque,
    conferir_giro_estoque,
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

def numero_seguro(valor):

    try:

        if valor is None:
            return 0.0

        if pd.isna(valor):
            return 0.0

        return float(valor)

    except Exception:
        return 0.0


def inteiro_seguro(valor):

    try:

        if valor is None:
            return 0

        if pd.isna(valor):
            return 0

        return int(valor)

    except Exception:
        return 0


def texto_seguro(valor):

    if valor is None:
        return ""

    try:

        if pd.isna(valor):
            return ""

    except Exception:
        pass

    return str(valor)


def formatar_percentual(valor):

    try:

        if valor is None:
            return "0,00%"

        if pd.isna(valor):
            return "0,00%"

        return (
            f"{float(valor):,.2f}%"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:
        return "0,00%"


def formatar_numero(valor):

    try:

        if valor is None:
            return "0"

        if pd.isna(valor):
            return "0"

        numero = float(valor)

        if numero.is_integer():
            return str(
                int(numero)
            )

        return (
            f"{numero:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:
        return "0"


def formatar_cobertura(valor):

    try:

        if valor is None:
            return "-"

        if pd.isna(valor):
            return "-"

        return (
            f"{float(valor):,.2f} meses"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except Exception:
        return "-"


# ============================================================
# PREPARAR DATAFRAME PARA EXIBICAO
# ============================================================

def preparar_dataframe_exibicao(df):

    if df is None or df.empty:
        return pd.DataFrame()

    exibicao = df.copy()

    colunas = {
        "produto_id": "ID",
        "produto": "Produto",
        "tamanho": "Tam.",
        "categoria": "Categoria",
        "estoque_atual": "Estoque",
        "estoque_minimo": "Mín.",
        "vendas_30_dias": "Venda 30d",
        "vendas_90_dias": "Venda 90d",
        "vendas_historico": "Histórico",
        "cobertura_meses": "Cobertura",
        "faturamento_bruto_90_dias": "Bruto 90d",
        "desconto_90_dias": "Desconto 90d",
        "faturamento_90_dias": "Líquido 90d",
        "percentual_desconto_90_dias": "% Desc.",
        "classificacao_giro": "Giro",
        "situacao_estoque": "Situação",
        "alerta_desconto": "Alerta",
        "sugestao": "Recomendação",
    }

    colunas_existentes = [
        coluna
        for coluna in colunas
        if coluna in exibicao.columns
    ]

    exibicao = exibicao[
        colunas_existentes
    ].copy()

    exibicao = exibicao.rename(
        columns=colunas
    )

    if "Tam." in exibicao.columns:

        exibicao["Tam."] = (
            exibicao["Tam."]
            .fillna("")
            .astype(str)
        )

    if "Bruto 90d" in exibicao.columns:

        exibicao["Bruto 90d"] = (
            exibicao["Bruto 90d"]
            .apply(formatar_moeda)
        )

    if "Desconto 90d" in exibicao.columns:

        exibicao["Desconto 90d"] = (
            exibicao["Desconto 90d"]
            .apply(formatar_moeda)
        )

    if "Líquido 90d" in exibicao.columns:

        exibicao["Líquido 90d"] = (
            exibicao["Líquido 90d"]
            .apply(formatar_moeda)
        )

    if "% Desc." in exibicao.columns:

        exibicao["% Desc."] = (
            exibicao["% Desc."]
            .apply(formatar_percentual)
        )

    if "Cobertura" in exibicao.columns:

        exibicao["Cobertura"] = (
            exibicao["Cobertura"]
            .apply(formatar_cobertura)
        )

    return exibicao


# ============================================================
# APLICAR FILTROS
# ============================================================

def aplicar_filtros(
    df,
    categoria,
    classificacao,
    situacao,
    alerta,
    busca,
    somente_com_estoque,
):

    if df is None or df.empty:
        return pd.DataFrame()

    filtrado = df.copy()

    if categoria != "TODAS":

        filtrado = filtrado[
            filtrado[
                "categoria"
            ]
            .fillna("")
            .astype(str)
            .str.upper()
            ==
            categoria.upper()
        ]

    if classificacao != "TODAS":

        filtrado = filtrado[
            filtrado[
                "classificacao_giro"
            ]
            ==
            classificacao
        ]

    if situacao != "TODAS":

        filtrado = filtrado[
            filtrado[
                "situacao_estoque"
            ]
            ==
            situacao
        ]

    if alerta != "TODOS":

        filtrado = filtrado[
            filtrado[
                "alerta_desconto"
            ]
            ==
            alerta
        ]

    if somente_com_estoque:

        filtrado = filtrado[
            filtrado[
                "estoque_atual"
            ]
            > 0
        ]

    if busca:

        busca_normalizada = (
            busca
            .strip()
            .upper()
        )

        mascara = (
            filtrado[
                "produto"
            ]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.contains(
                busca_normalizada,
                regex=False,
            )
        )

        if "codigo_barras" in filtrado.columns:

            mascara = (
                mascara
                |
                filtrado[
                    "codigo_barras"
                ]
                .fillna("")
                .astype(str)
                .str.upper()
                .str.contains(
                    busca_normalizada,
                    regex=False,
                )
            )

        if "sku" in filtrado.columns:

            mascara = (
                mascara
                |
                filtrado[
                    "sku"
                ]
                .fillna("")
                .astype(str)
                .str.upper()
                .str.contains(
                    busca_normalizada,
                    regex=False,
                )
            )

        filtrado = filtrado[
            mascara
        ]

    return filtrado.copy()


# ============================================================
# RESUMO DO DATAFRAME FILTRADO
# ============================================================

def calcular_resumo_filtrado(df):

    if df is None or df.empty:

        return {
            "produtos": 0,
            "unidades_estoque": 0,
            "capital_estoque": 0.0,
            "vendas_90_dias": 0,
            "bruto_90_dias": 0.0,
            "desconto_90_dias": 0.0,
            "liquido_90_dias": 0.0,
            "percentual_desconto_90_dias": 0.0,
        }

    bruto = numero_seguro(
        df[
            "faturamento_bruto_90_dias"
        ].sum()
    )

    desconto = numero_seguro(
        df[
            "desconto_90_dias"
        ].sum()
    )

    liquido = numero_seguro(
        df[
            "faturamento_90_dias"
        ].sum()
    )

    percentual = 0.0

    if bruto > 0:

        percentual = (
            desconto
            /
            bruto
        ) * 100

    return {
        "produtos":
            int(
                len(df)
            ),

        "unidades_estoque":
            inteiro_seguro(
                df.loc[
                    df[
                        "estoque_atual"
                    ] > 0,
                    "estoque_atual"
                ].sum()
            ),

        "capital_estoque":
            numero_seguro(
                df[
                    "valor_estoque_custo"
                ].sum()
            ),

        "vendas_90_dias":
            inteiro_seguro(
                df[
                    "vendas_90_dias"
                ].sum()
            ),

        "bruto_90_dias":
            bruto,

        "desconto_90_dias":
            desconto,

        "liquido_90_dias":
            liquido,

        "percentual_desconto_90_dias":
            percentual,
    }


# ============================================================
# GERAR PDF
# ============================================================

def gerar_pdf_giro_estoque(
    df_filtrado,
    resumo_geral,
    resumo_filtrado,
    conferencia,
    filtros_texto,
):

    inicio_historico = conferencia.get(
        "inicio_historico"
    )

    fim_historico = conferencia.get(
        "fim_historico"
    )

        # ========================================================
    # INDICADORES
    # ========================================================

    indicadores = [
        {
            "titulo": "Produtos ativos",
            "valor": formatar_numero(
                resumo_geral.get(
                    "produtos_ativos"
                )
            ),
        },
        {
            "titulo": "Alto giro",
            "valor": formatar_numero(
                resumo_geral.get(
                    "alto_giro"
                )
            ),
        },
        {
            "titulo": "Estoque parado",
            "valor": formatar_numero(
                resumo_geral.get(
                    "estoque_parado"
                )
            ),
        },
        {
            "titulo": "Rupturas",
            "valor": formatar_numero(
                resumo_geral.get(
                    "ruptura"
                )
            ),
        },
        {
            "titulo": "Capital em estoque",
            "valor": formatar_moeda(
                numero_seguro(
                    resumo_geral.get(
                        "capital_estoque_conhecido"
                    )
                )
            ),
        },
        {
            "titulo": "Faturamento líquido",
            "valor": formatar_moeda(
                numero_seguro(
                    resumo_geral.get(
                        "faturamento_historico"
                    )
                )
            ),
        },
    ]

    # ========================================================
    # TABELA RESUMO DO GIRO
    # ========================================================

    tabela_giro = criar_tabela_relatorio(
        [
            "Classificação",
            "Quantidade",
        ],
        [
            [
                "Alto giro",
                formatar_numero(
                    resumo_geral.get(
                        "alto_giro"
                    )
                ),
            ],
            [
                "Médio giro",
                formatar_numero(
                    resumo_geral.get(
                        "medio_giro"
                    )
                ),
            ],
            [
                "Baixo giro",
                formatar_numero(
                    resumo_geral.get(
                        "baixo_giro"
                    )
                ),
            ],
            [
                "Sem giro",
                formatar_numero(
                    resumo_geral.get(
                        "sem_giro"
                    )
                ),
            ],
        ],
    )

    # ========================================================
    # TABELA SITUACAO DE ESTOQUE
    # ========================================================

    tabela_situacao = criar_tabela_relatorio(
        [
            "Situação",
            "Quantidade",
        ],
        [
            [
                "Ruptura",
                formatar_numero(
                    resumo_geral.get(
                        "ruptura"
                    )
                ),
            ],
            [
                "Sem estoque",
                formatar_numero(
                    resumo_geral.get(
                        "sem_estoque"
                    )
                ),
            ],
            [
                "Abaixo do mínimo",
                formatar_numero(
                    resumo_geral.get(
                        "abaixo_minimo"
                    )
                ),
            ],
            [
                "Estoque parado",
                formatar_numero(
                    resumo_geral.get(
                        "estoque_parado"
                    )
                ),
            ],
            [
                "Possível excesso",
                formatar_numero(
                    resumo_geral.get(
                        "possivel_excesso"
                    )
                ),
            ],
        ],
    )

    # ========================================================
    # TABELA FINANCEIRA
    # ========================================================

    tabela_financeira = criar_tabela_relatorio(
        [
            "Indicador",
            "Valor",
        ],
        [
            [
                "Faturamento bruto - histórico",
                formatar_moeda(
                    numero_seguro(
                        resumo_geral.get(
                            "faturamento_bruto_historico"
                        )
                    )
                ),
            ],
            [
                "Descontos - histórico",
                formatar_moeda(
                    numero_seguro(
                        resumo_geral.get(
                            "desconto_historico"
                        )
                    )
                ),
            ],
            [
                "Faturamento líquido - histórico",
                formatar_moeda(
                    numero_seguro(
                        resumo_geral.get(
                            "faturamento_historico"
                        )
                    )
                ),
            ],
            [
                "Desconto médio efetivo",
                formatar_percentual(
                    resumo_geral.get(
                        "percentual_desconto_historico"
                    )
                ),
            ],
        ],
    )

    # ========================================================
    # TABELA FILTROS
    # ========================================================

    tabela_filtros = criar_tabela_relatorio(
        [
            "Filtro",
            "Seleção",
        ],
        [
            [
                "Categoria",
                filtros_texto.get(
                    "categoria",
                    "TODAS",
                ),
            ],
            [
                "Classificação",
                filtros_texto.get(
                    "classificacao",
                    "TODAS",
                ),
            ],
            [
                "Situação",
                filtros_texto.get(
                    "situacao",
                    "TODAS",
                ),
            ],
            [
                "Alerta de desconto",
                filtros_texto.get(
                    "alerta",
                    "TODOS",
                ),
            ],
            [
                "Busca",
                filtros_texto.get(
                    "busca",
                    "",
                )
                or "SEM FILTRO",
            ],
            [
                "Somente com estoque",
                (
                    "SIM"
                    if filtros_texto.get(
                        "somente_com_estoque"
                    )
                    else "NÃO"
                ),
            ],
        ],
    )

    # ========================================================
    # TABELA RESULTADO FILTRADO
    # ========================================================

    linhas_produtos = []

    for _, linha in df_filtrado.iterrows():

        linhas_produtos.append(
            [
                texto_seguro(
                    linha.get(
                        "produto"
                    )
                ),
                texto_seguro(
                    linha.get(
                        "tamanho"
                    )
                ),
                formatar_numero(
                    linha.get(
                        "estoque_atual"
                    )
                ),
                formatar_numero(
                    linha.get(
                        "vendas_90_dias"
                    )
                ),
                formatar_cobertura(
                    linha.get(
                        "cobertura_meses"
                    )
                ),
                formatar_moeda(
                    numero_seguro(
                        linha.get(
                            "faturamento_bruto_90_dias"
                        )
                    )
                ),
                formatar_moeda(
                    numero_seguro(
                        linha.get(
                            "desconto_90_dias"
                        )
                    )
                ),
                formatar_moeda(
                    numero_seguro(
                        linha.get(
                            "faturamento_90_dias"
                        )
                    )
                ),
                formatar_percentual(
                    linha.get(
                        "percentual_desconto_90_dias"
                    )
                ),
                texto_seguro(
                    linha.get(
                        "classificacao_giro"
                    )
                ),
                texto_seguro(
                    linha.get(
                        "situacao_estoque"
                    )
                ),
            ]
        )

    tabela_produtos = criar_tabela_relatorio(
        [
            "Produto",
            "Tam.",
            "Est.",
            "Venda 90d",
            "Cobertura",
            "Bruto 90d",
            "Desc. 90d",
            "Líquido 90d",
            "% Desc.",
            "Giro",
            "Situação",
        ],
        linhas_produtos,
    )

    # ========================================================
    # CONFERENCIA
    # ========================================================

    bruto_conferencia = numero_seguro(
        conferencia.get(
            "faturamento_bruto_historico"
        )
    )

    desconto_conferencia = numero_seguro(
        conferencia.get(
            "desconto_historico"
        )
    )

    liquido_conferencia = numero_seguro(
        conferencia.get(
            "faturamento_historico"
        )
    )

    diferenca = numero_seguro(
        conferencia.get(
            "diferenca_conciliacao"
        )
    )

    conferencia_ok = (
        abs(
            diferenca
        )
        < 0.01
    )

    texto_conferencia = (
        f"Produtos ativos apurados: "
        f"{formatar_numero(conferencia.get('quantidade_produtos'))}. "
        f"Unidades em estoque: "
        f"{formatar_numero(conferencia.get('quantidade_unidades'))}. "
        f"Valor conhecido do estoque a custo: "
        f"{formatar_moeda(numero_seguro(conferencia.get('valor_estoque_custo')))}. "
        f"Unidades vendidas no histórico: "
        f"{formatar_numero(conferencia.get('vendas_historico_unidades'))}. "
        f"Faturamento bruto: "
        f"{formatar_moeda(bruto_conferencia)}. "
        f"Descontos: "
        f"{formatar_moeda(desconto_conferencia)}. "
        f"Faturamento líquido: "
        f"{formatar_moeda(liquido_conferencia)}. "
        f"Diferença de conciliação: "
        f"{formatar_moeda(diferenca)}."
    )

    observacao_conferencia = (
        "OK - faturamento bruto menos descontos "
        "é igual ao faturamento líquido."
        if conferencia_ok
        else
        "ATENÇÃO - foi identificada divergência "
        "na conciliação do faturamento."
    )

    # ========================================================
    # TEXTO DO HISTORICO
    # ========================================================

    texto_historico = (
        "A análise utiliza exclusivamente o histórico "
        "de vendas concluídas disponível no ERP."
    )

    if (
        inicio_historico is not None
        and fim_historico is not None
    ):

        texto_historico = (
            "O histórico disponível no ERP para esta análise "
            f"vai de {formatar_data(inicio_historico)} "
            f"a {formatar_data(fim_historico)}. "
            "Períodos anteriores não são considerados porque "
            "não estão registrados nesta base."
        )

    # ========================================================
    # SECOES DO PDF
    # ========================================================

    secoes = [
        {
            "titulo":
                "Resumo da Classificação de Giro",

            "texto":
                (
                    "Classificação calculada pelo volume de "
                    "unidades vendidas nos últimos 90 dias."
                ),

            "tabela":
                tabela_giro,
        },

        {
            "titulo":
                "Situação do Estoque",

            "texto":
                (
                    "Produtos classificados de acordo com "
                    "estoque disponível, vendas recentes, "
                    "estoque mínimo e cobertura estimada."
                ),

            "tabela":
                tabela_situacao,
        },

        {
            "titulo":
                "Desempenho Financeiro",

            "texto":
                (
                    "O faturamento bruto representa o valor "
                    "original dos itens vendidos. Os descontos "
                    "são rateados proporcionalmente entre os "
                    "itens da venda. O faturamento líquido "
                    "corresponde ao valor efetivamente vendido."
                ),

            "tabela":
                tabela_financeira,
        },

        {
            "titulo":
                "Filtros Aplicados",

            "texto":
                (
                    f"O resultado contém "
                    f"{formatar_numero(resumo_filtrado.get('produtos'))} "
                    f"produto(s), "
                    f"{formatar_numero(resumo_filtrado.get('unidades_estoque'))} "
                    f"unidade(s) em estoque e "
                    f"{formatar_moeda(numero_seguro(resumo_filtrado.get('capital_estoque')))} "
                    f"em capital de estoque conhecido."
                ),

            "tabela":
                tabela_filtros,
        },

        {
            "titulo":
                "Detalhamento dos Produtos",

            "texto":
                (
                    "Relação dos produtos conforme os filtros "
                    "selecionados. Os indicadores de vendas e "
                    "desconto desta tabela consideram os "
                    "últimos 90 dias."
                ),

            "tabela":
                tabela_produtos,

            "observacao":
                (
                    "Cobertura estimada = estoque atual dividido "
                    "pela média mensal de vendas dos últimos "
                    "90 dias. Produtos sem venda no período "
                    "podem não possuir cobertura calculável."
                ),
        },

        {
            "titulo":
                "Histórico Disponível",

            "texto":
                texto_historico,

            "observacao":
                (
                    "A data de cadastro do produto no ERP não "
                    "é utilizada como prova da idade real do "
                    "produto na loja."
                ),
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
            "Relatório de Giro e "
            "Inteligência de Estoque"
        ),
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )


# ============================================================
# TELA PRINCIPAL
# ============================================================

def tela_relatorio_giro_estoque():

    st.title(
        "🔄 Giro e Inteligência de Estoque"
    )

    st.caption(
        "Análise de giro, estoque parado, rupturas, "
        "excessos, descontos e oportunidades comerciais."
    )

    st.divider()

    # ========================================================
    # CARREGAR DADOS
    # ========================================================

    with st.spinner(
        "Analisando vendas e estoque..."
    ):

        df = listar_giro_estoque()

        resumo_geral = (
            obter_resumo_giro_estoque()
        )

        conferencia = (
            conferir_giro_estoque()
        )

    if (
        df is None
        or df.empty
    ):

        st.warning(
            "Nenhum produto ativo foi encontrado "
            "para análise."
        )

        return

    # ========================================================
    # HISTORICO DISPONIVEL
    # ========================================================

    inicio_historico = conferencia.get(
        "inicio_historico"
    )

    fim_historico = conferencia.get(
        "fim_historico"
    )

    if (
        inicio_historico is not None
        and fim_historico is not None
    ):

        st.info(
            "Histórico de vendas disponível no ERP: "
            f"{formatar_data(inicio_historico)} "
            f"a {formatar_data(fim_historico)}."
        )

    # ========================================================
    # RESUMO EXECUTIVO
    # ========================================================

    st.subheader(
        "📊 Resumo Executivo"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Produtos ativos",
            formatar_numero(
                resumo_geral.get(
                    "produtos_ativos"
                )
            ),
        )

    with col2:

        st.metric(
            "Alto giro",
            formatar_numero(
                resumo_geral.get(
                    "alto_giro"
                )
            ),
        )

    with col3:

        st.metric(
            "Estoque parado",
            formatar_numero(
                resumo_geral.get(
                    "estoque_parado"
                )
            ),
        )

    with col4:

        st.metric(
            "Rupturas",
            formatar_numero(
                resumo_geral.get(
                    "ruptura"
                )
            ),
        )

    col5, col6, col7, col8 = (
        st.columns(4)
    )

    with col5:

        st.metric(
            "Possível excesso",
            formatar_numero(
                resumo_geral.get(
                    "possivel_excesso"
                )
            ),
        )

    with col6:

        st.metric(
            "Sem estoque mínimo",
            formatar_numero(
                resumo_geral.get(
                    "sem_minimo"
                )
            ),
        )

    with col7:

        st.metric(
            "Sem custo válido",
            formatar_numero(
                resumo_geral.get(
                    "sem_custo"
                )
            ),
        )

    with col8:

        st.metric(
            "Capital em estoque",
            formatar_moeda(
                numero_seguro(
                    resumo_geral.get(
                        "capital_estoque_conhecido"
                    )
                )
            ),
        )

    st.divider()

    # ========================================================
    # FINANCEIRO
    # ========================================================

    st.subheader(
        "💰 Vendas e Descontos"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Faturamento bruto",
            formatar_moeda(
                numero_seguro(
                    resumo_geral.get(
                        "faturamento_bruto_historico"
                    )
                )
            ),
        )

    with col2:

        st.metric(
            "Descontos",
            formatar_moeda(
                numero_seguro(
                    resumo_geral.get(
                        "desconto_historico"
                    )
                )
            ),
        )

    with col3:

        st.metric(
            "Faturamento líquido",
            formatar_moeda(
                numero_seguro(
                    resumo_geral.get(
                        "faturamento_historico"
                    )
                )
            ),
        )

    with col4:

        st.metric(
            "Desconto efetivo",
            formatar_percentual(
                resumo_geral.get(
                    "percentual_desconto_historico"
                )
            ),
        )

    st.caption(
        "O faturamento líquido corresponde ao valor "
        "efetivamente vendido após os descontos registrados."
    )

    st.divider()

    # ========================================================
    # FILTROS
    # ========================================================

    st.subheader(
        "🔎 Filtros"
    )

    categorias = sorted(
        [
            str(valor)
            for valor in
            df[
                "categoria"
            ]
            .dropna()
            .unique()
            if str(valor).strip()
        ]
    )

    classificacoes = [
        "TODAS",
        "ALTO GIRO",
        "MÉDIO GIRO",
        "BAIXO GIRO",
        "SEM GIRO",
    ]

    situacoes = [
        "TODAS",
        "RUPTURA",
        "SEM ESTOQUE",
        "ABAIXO DO MÍNIMO",
        "ESTOQUE PARADO",
        "POSSÍVEL EXCESSO",
        "ESTOQUE NORMAL",
    ]

    alertas = [
        "TODOS",
        "DESCONTO MUITO ELEVADO",
        "DESCONTO ELEVADO",
        "DESCONTO MODERADO",
        "DESCONTO BAIXO",
        "SEM DESCONTO",
        "SEM VENDAS NO PERÍODO",
    ]

    col1, col2 = (
        st.columns(2)
    )

    with col1:

        categoria = st.selectbox(
            "Categoria",
            options=[
                "TODAS"
            ]
            + categorias,
            index=0,
            key="giro_categoria",
        )

    with col2:

        classificacao = (
            st.selectbox(
                "Classificação de giro",
                options=classificacoes,
                index=0,
                key="giro_classificacao",
            )
        )

    col3, col4 = (
        st.columns(2)
    )

    with col3:

        situacao = st.selectbox(
            "Situação do estoque",
            options=situacoes,
            index=0,
            key="giro_situacao",
        )

    with col4:

        alerta = st.selectbox(
            "Alerta de desconto",
            options=alertas,
            index=0,
            key="giro_alerta_desconto",
        )

    busca = st.text_input(
        "Produto, código de barras ou SKU",
        value="",
        placeholder=(
            "Digite parte do nome, código ou SKU..."
        ),
        key="giro_busca",
    )

    somente_com_estoque = (
        st.checkbox(
            "Mostrar somente produtos com estoque",
            value=False,
            key="giro_somente_com_estoque",
        )
    )

    # ========================================================
    # APLICAR FILTROS
    # ========================================================

    df_filtrado = aplicar_filtros(
        df=df,
        categoria=categoria,
        classificacao=classificacao,
        situacao=situacao,
        alerta=alerta,
        busca=busca,
        somente_com_estoque=somente_com_estoque,
    )

    resumo_filtrado = (
        calcular_resumo_filtrado(
            df_filtrado
        )
    )

    st.divider()

    # ========================================================
    # RESULTADO DOS FILTROS
    # ========================================================

    st.subheader(
        "📌 Resultado Selecionado"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    with col1:

        st.metric(
            "Produtos",
            formatar_numero(
                resumo_filtrado.get(
                    "produtos"
                )
            ),
        )

    with col2:

        st.metric(
            "Unidades em estoque",
            formatar_numero(
                resumo_filtrado.get(
                    "unidades_estoque"
                )
            ),
        )

    with col3:

        st.metric(
            "Vendas em 90 dias",
            formatar_numero(
                resumo_filtrado.get(
                    "vendas_90_dias"
                )
            ),
        )

    with col4:

        st.metric(
            "Capital em estoque",
            formatar_moeda(
                numero_seguro(
                    resumo_filtrado.get(
                        "capital_estoque"
                    )
                )
            ),
        )

    col5, col6, col7, col8 = (
        st.columns(4)
    )

    with col5:

        st.metric(
            "Bruto 90 dias",
            formatar_moeda(
                numero_seguro(
                    resumo_filtrado.get(
                        "bruto_90_dias"
                    )
                )
            ),
        )

    with col6:

        st.metric(
            "Descontos 90 dias",
            formatar_moeda(
                numero_seguro(
                    resumo_filtrado.get(
                        "desconto_90_dias"
                    )
                )
            ),
        )

    with col7:

        st.metric(
            "Líquido 90 dias",
            formatar_moeda(
                numero_seguro(
                    resumo_filtrado.get(
                        "liquido_90_dias"
                    )
                )
            ),
        )

    with col8:

        st.metric(
            "% desconto 90 dias",
            formatar_percentual(
                resumo_filtrado.get(
                    "percentual_desconto_90_dias"
                )
            ),
        )

    # ========================================================
    # ALERTAS DE DESCONTO
    # ========================================================

    quantidade_desconto_alto = (
        (
            df_filtrado[
                "alerta_desconto"
            ]
            .isin(
                [
                    "DESCONTO ELEVADO",
                    "DESCONTO MUITO ELEVADO",
                ]
            )
        )
        .sum()
    )

    if quantidade_desconto_alto > 0:

        st.warning(
            f"{quantidade_desconto_alto} produto(s) "
            "do resultado apresentam desconto elevado "
            "ou muito elevado nos últimos 90 dias."
        )

    # ========================================================
    # TABELA
    # ========================================================

    st.subheader(
        "📋 Análise por Produto"
    )

    if df_filtrado.empty:

        st.warning(
            "Nenhum produto corresponde aos "
            "filtros selecionados."
        )

    else:

        st.dataframe(
            preparar_dataframe_exibicao(
                df_filtrado
            ),
            use_container_width=True,
            hide_index=True,
            height=650,
        )

    # ========================================================
    # CONFERENCIA
    # ========================================================

    st.divider()

    st.subheader(
        "✅ Conferência"
    )

    diferenca = numero_seguro(
        conferencia.get(
            "diferenca_conciliacao"
        )
    )

    if abs(
        diferenca
    ) < 0.01:

        st.success(
            "Faturamento bruto, descontos e "
            "faturamento líquido estão conciliados."
        )

    else:

        st.error(
            "Foi identificada divergência na "
            "conciliação do faturamento."
        )

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.write(
            "**Faturamento bruto:** "
            f"{formatar_moeda(numero_seguro(conferencia.get('faturamento_bruto_historico')))}"
        )

    with col2:

        st.write(
            "**Descontos:** "
            f"{formatar_moeda(numero_seguro(conferencia.get('desconto_historico')))}"
        )

    with col3:

        st.write(
            "**Faturamento líquido:** "
            f"{formatar_moeda(numero_seguro(conferencia.get('faturamento_historico')))}"
        )

    # ========================================================
    # PDF
    # ========================================================

    if not df_filtrado.empty:

        st.divider()

        st.subheader(
            "📄 Relatório em PDF"
        )

        try:

            filtros_texto = {
                "categoria":
                    categoria,

                "classificacao":
                    classificacao,

                "situacao":
                    situacao,

                "alerta":
                    alerta,

                "busca":
                    busca,

                "somente_com_estoque":
                    somente_com_estoque,
            }

            pdf = gerar_pdf_giro_estoque(
                df_filtrado=df_filtrado,
                resumo_geral=resumo_geral,
                resumo_filtrado=resumo_filtrado,
                conferencia=conferencia,
                filtros_texto=filtros_texto,
            )

            st.download_button(
                label=(
                    "📄 Baixar relatório em PDF"
                ),
                data=pdf,
                file_name=(
                    "relatorio_giro_"
                    "inteligencia_estoque.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
                key="download_giro_estoque",
            )

        except Exception as erro:

            st.error(
                "Não foi possível gerar o PDF."
            )

            st.exception(
                erro
            )