import streamlit as st
import pandas as pd

from database.relatorios_produtos_db import (
    listar_posicao_estoque,
    obter_resumo_estoque,
    listar_categorias_produtos,
    conferir_posicao_estoque,
)

from services.relatorios.relatorio_base import (
    formatar_moeda,
)

from services.relatorios.pdf_relatorio import (
    gerar_pdf_profissional,
    criar_tabela_relatorio,
)


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
SITUACOES_ESTOQUE = [
    "TODAS",
    "SEM ESTOQUE",
    "ABAIXO DO MÍNIMO",
    "NO MÍNIMO",
    "SEM MÍNIMO",
    "NORMAL",
]


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================
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


def formatar_numero(valor):

    try:

        numero = float(valor)

        if numero.is_integer():

            return (
                f"{int(numero):,}"
                .replace(",", ".")
            )

        return (
            f"{numero:,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except (TypeError, ValueError):

        return "0"


# ==========================================================
# PREPARAR DATAFRAME PARA TELA
# ==========================================================
def preparar_dataframe_exibicao(df):

    if df is None or df.empty:
        return pd.DataFrame()

    resultado = df.copy()

    colunas = [
        "id",
        "codigo_barras",
        "sku",
        "nome",
        "tamanho",
        "categoria",
        "estoque",
        "estoque_minimo",
        "custo",
        "preco",
        "valor_estoque_custo",
        "valor_estoque_venda",
        "situacao_estoque",
    ]

    colunas_existentes = [
        coluna
        for coluna in colunas
        if coluna in resultado.columns
    ]

    resultado = (
        resultado[
            colunas_existentes
        ]
        .copy()
    )

    resultado = resultado.rename(
        columns={
            "id": "ID",
            "codigo_barras": "Código de Barras",
            "sku": "SKU",
            "nome": "Produto",
            "tamanho": "Tamanho",
            "categoria": "Categoria",
            "estoque": "Estoque",
            "estoque_minimo": "Mínimo",
            "custo": "Custo",
            "preco": "Preço",
            "valor_estoque_custo":
                "Valor a Custo",
            "valor_estoque_venda":
                "Potencial de Venda",
            "situacao_estoque":
                "Situação",
        }
    )

    return resultado


# ==========================================================
# GERAR PDF
# ==========================================================
def gerar_pdf_posicao_estoque(
    df,
    resumo,
    conferencia,
    categoria_selecionada,
    situacao_selecionada,
):

    # ======================================================
    # INDICADORES GERAIS
    # ======================================================
    produtos_ativos = inteiro_seguro(
        resumo.get(
            "produtos_ativos"
        )
    )

    quantidade_total = inteiro_seguro(
        resumo.get(
            "quantidade_total_estoque"
        )
    )

    valor_custo = numero_seguro(
        resumo.get(
            "valor_custo_conhecido"
        )
    )

    valor_venda = numero_seguro(
        resumo.get(
            "valor_potencial_venda"
        )
    )

    indicadores = [
        {
            "titulo":
                "Produtos ativos",

            "valor":
                formatar_numero(
                    produtos_ativos
                ),
        },
        {
            "titulo":
                "Unidades em estoque",

            "valor":
                formatar_numero(
                    quantidade_total
                ),
        },
        {
            "titulo":
                "Custo conhecido",

            "valor":
                formatar_moeda(
                    valor_custo
                ),
        },
        {
            "titulo":
                "Potencial de venda",

            "valor":
                formatar_moeda(
                    valor_venda
                ),
        },
    ]

    # ======================================================
    # SITUAÇÃO GERAL
    # ======================================================
    linhas_situacao = [
        [
            "Sem estoque",
            inteiro_seguro(
                resumo.get(
                    "produtos_sem_estoque"
                )
            ),
        ],
        [
            "Abaixo do mínimo",
            inteiro_seguro(
                resumo.get(
                    "produtos_abaixo_minimo"
                )
            ),
        ],
        [
            "No mínimo",
            inteiro_seguro(
                resumo.get(
                    "produtos_no_minimo"
                )
            ),
        ],
        [
            "Sem mínimo cadastrado",
            inteiro_seguro(
                resumo.get(
                    "produtos_sem_minimo"
                )
            ),
        ],
        [
            "Normal",
            inteiro_seguro(
                resumo.get(
                    "produtos_normais"
                )
            ),
        ],
    ]

    tabela_situacao = criar_tabela_relatorio(
        colunas=[
            "Situação",
            "Produtos",
        ],
        linhas=linhas_situacao,
        larguras=[
            280,
            100,
        ],
        alinhamentos=[
            "LEFT",
            "CENTER",
        ],
    )

    # ======================================================
    # QUALIDADE CADASTRAL
    # ======================================================
    linhas_qualidade = [
        [
            "Produtos ativos sem custo válido",
            inteiro_seguro(
                resumo.get(
                    "produtos_sem_custo"
                )
            ),
        ],
        [
            "Produtos ativos sem preço válido",
            inteiro_seguro(
                resumo.get(
                    "produtos_sem_preco"
                )
            ),
        ],
        [
            "Produtos inativos",
            inteiro_seguro(
                resumo.get(
                    "produtos_inativos"
                )
            ),
        ],
    ]

    tabela_qualidade = criar_tabela_relatorio(
        colunas=[
            "Verificação",
            "Quantidade",
        ],
        linhas=linhas_qualidade,
        larguras=[
            280,
            100,
        ],
        alinhamentos=[
            "LEFT",
            "CENTER",
        ],
    )

    # ======================================================
    # RESULTADO DOS FILTROS
    # ======================================================
    quantidade_produtos_filtro = 0
    quantidade_unidades_filtro = 0
    valor_custo_filtro = 0
    valor_venda_filtro = 0

    if (
        df is not None
        and not df.empty
    ):

        quantidade_produtos_filtro = len(df)

        quantidade_unidades_filtro = (
            pd.to_numeric(
                df["estoque"],
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
            .sum()
        )

        valor_custo_filtro = (
            pd.to_numeric(
                df["valor_estoque_custo"],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

        valor_venda_filtro = (
            pd.to_numeric(
                df["valor_estoque_venda"],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

    texto_filtros = (
        f"Categoria: {categoria_selecionada}. "
        f"Situação do estoque: "
        f"{situacao_selecionada}. "
        f"O resultado contém "
        f"{formatar_numero(quantidade_produtos_filtro)} "
        f"produto(s), "
        f"{formatar_numero(quantidade_unidades_filtro)} "
        f"unidade(s), "
        f"{formatar_moeda(valor_custo_filtro)} "
        f"em custo conhecido e "
        f"{formatar_moeda(valor_venda_filtro)} "
        f"em potencial de venda."
    )

    # ======================================================
    # DETALHAMENTO
    # ======================================================
    linhas_produtos = []

    if (
        df is not None
        and not df.empty
    ):

        for _, linha in df.iterrows():

            codigo = (
                linha.get(
                    "codigo_barras"
                )
                or
                linha.get(
                    "sku"
                )
                or
                ""
            )

            tamanho = (
                linha.get(
                    "tamanho"
                )
                or
                ""
            )

            categoria = (
                linha.get(
                    "categoria"
                )
                or
                ""
            )

            linhas_produtos.append(
                [
                    inteiro_seguro(
                        linha.get(
                            "id"
                        )
                    ),

                    str(codigo),

                    linha.get(
                        "nome",
                        "",
                    ),

                    str(tamanho),

                    str(categoria),

                    formatar_numero(
                        linha.get(
                            "estoque"
                        )
                    ),

                    formatar_numero(
                        linha.get(
                            "estoque_minimo"
                        )
                    ),

                    formatar_moeda(
                        numero_seguro(
                            linha.get(
                                "custo"
                            )
                        )
                    ),

                    formatar_moeda(
                        numero_seguro(
                            linha.get(
                                "preco"
                            )
                        )
                    ),

                    linha.get(
                        "situacao_estoque",
                        "",
                    ),
                ]
            )

    tabela_produtos = criar_tabela_relatorio(
        colunas=[
            "ID",
            "Código",
            "Produto",
            "Tam.",
            "Categoria",
            "Est.",
            "Mín.",
            "Custo",
            "Preço",
            "Situação",
        ],
        linhas=linhas_produtos,
        larguras=[
            34,
            82,
            185,
            45,
            95,
            42,
            42,
            65,
            65,
            95,
        ],
        alinhamentos=[
            "CENTER",
            "LEFT",
            "LEFT",
            "CENTER",
            "LEFT",
            "CENTER",
            "CENTER",
            "RIGHT",
            "RIGHT",
            "CENTER",
        ],
    )

    # ======================================================
    # CONFERÊNCIA
    # ======================================================
    soma_situacoes = (
        inteiro_seguro(
            resumo.get(
                "produtos_sem_estoque"
            )
        )
        +
        inteiro_seguro(
            resumo.get(
                "produtos_abaixo_minimo"
            )
        )
        +
        inteiro_seguro(
            resumo.get(
                "produtos_no_minimo"
            )
        )
        +
        inteiro_seguro(
            resumo.get(
                "produtos_sem_minimo"
            )
        )
        +
        inteiro_seguro(
            resumo.get(
                "produtos_normais"
            )
        )
    )

    quantidade_banco = inteiro_seguro(
        conferencia.get(
            "quantidade_produtos"
        )
    )

    quantidade_estoque_banco = inteiro_seguro(
        conferencia.get(
            "quantidade_estoque"
        )
    )

    custo_banco = numero_seguro(
        conferencia.get(
            "valor_custo_conhecido"
        )
    )

    venda_banco = numero_seguro(
        conferencia.get(
            "valor_potencial_venda"
        )
    )

    conferencia_ok = (
        soma_situacoes
        ==
        produtos_ativos
        ==
        quantidade_banco

        and
        quantidade_total
        ==
        quantidade_estoque_banco

        and
        abs(
            valor_custo
            -
            custo_banco
        )
        < 0.01

        and
        abs(
            valor_venda
            -
            venda_banco
        )
        < 0.01
    )

    texto_conferencia = (
        f"Produtos ativos no resumo: "
        f"{formatar_numero(produtos_ativos)}. "
        f"Soma das situações: "
        f"{formatar_numero(soma_situacoes)}. "
        f"Produtos ativos na base: "
        f"{formatar_numero(quantidade_banco)}. "
        f"Unidades em estoque: "
        f"{formatar_numero(quantidade_estoque_banco)}. "
        f"Custo conhecido: "
        f"{formatar_moeda(custo_banco)}. "
        f"Potencial de venda: "
        f"{formatar_moeda(venda_banco)}."
    )

    if conferencia_ok:

        observacao_conferencia = (
            "OK - posição de estoque conciliada "
            "com a base do ERP."
        )

    else:

        observacao_conferencia = (
            "ATENÇÃO - foi identificada divergência "
            "na conferência da posição de estoque."
        )

    # ======================================================
    # SEÇÕES DO PDF
    # ======================================================
    secoes = [
        {
            "titulo":
                "Situação Geral do Estoque",

            "texto":
                (
                    "Distribuição dos produtos ativos "
                    "de acordo com a posição atual do estoque "
                    "e o estoque mínimo cadastrado."
                ),

            "tabela":
                tabela_situacao,

            "observacao":
                (
                    "As situações são exclusivas: cada produto "
                    "ativo é classificado em apenas uma situação."
                ),
        },
        {
            "titulo":
                "Qualidade dos Cadastros",

            "texto":
                (
                    "Verificação de informações que podem "
                    "afetar a análise financeira e operacional "
                    "do estoque."
                ),

            "tabela":
                tabela_qualidade,

            "observacao":
                (
                    "O valor apresentado como custo conhecido "
                    "considera somente produtos com custo válido "
                    "e estoque positivo."
                ),
        },
        {
            "titulo":
                "Filtros Aplicados",

            "texto":
                texto_filtros,
        },
        {
            "titulo":
                "Detalhamento dos Produtos",

            "texto":
                (
                    "Relação dos produtos encontrados conforme "
                    "os filtros selecionados. Produtos críticos "
                    "são apresentados primeiro."
                ),

            "tabela":
                tabela_produtos,
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
            "Relatório de Posição de Estoque"
        ),
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )


# ==========================================================
# TELA PRINCIPAL
# ==========================================================
def tela_relatorio_posicao_estoque():

    st.title(
        "📦 Posição de Estoque"
    )

    st.caption(
        "Visão gerencial da posição atual dos produtos, "
        "níveis mínimos, custos e potencial de venda."
    )

    # ======================================================
    # RESUMO GERAL
    # ======================================================
    resumo = obter_resumo_estoque()

    if not resumo:

        st.error(
            "Não foi possível carregar "
            "o resumo do estoque."
        )

        return

    st.subheader(
        "Resumo geral"
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    col1.metric(
        "Produtos ativos",
        formatar_numero(
            resumo.get(
                "produtos_ativos",
                0,
            )
        ),
    )

    col2.metric(
        "Unidades em estoque",
        formatar_numero(
            resumo.get(
                "quantidade_total_estoque",
                0,
            )
        ),
    )

    col3.metric(
        "Custo conhecido",
        formatar_moeda(
            resumo.get(
                "valor_custo_conhecido",
                0,
            )
        ),
    )

    col4.metric(
        "Potencial de venda",
        formatar_moeda(
            resumo.get(
                "valor_potencial_venda",
                0,
            )
        ),
    )

    # ======================================================
    # SITUAÇÃO
    # ======================================================
    st.subheader(
        "Situação do estoque"
    )

    c1, c2, c3, c4, c5 = (
        st.columns(5)
    )

    c1.metric(
        "Sem estoque",
        resumo.get(
            "produtos_sem_estoque",
            0,
        ),
    )

    c2.metric(
        "Abaixo do mínimo",
        resumo.get(
            "produtos_abaixo_minimo",
            0,
        ),
    )

    c3.metric(
        "No mínimo",
        resumo.get(
            "produtos_no_minimo",
            0,
        ),
    )

    c4.metric(
        "Sem mínimo",
        resumo.get(
            "produtos_sem_minimo",
            0,
        ),
    )

    c5.metric(
        "Normal",
        resumo.get(
            "produtos_normais",
            0,
        ),
    )

    # ======================================================
    # QUALIDADE CADASTRAL
    # ======================================================
    with st.expander(
        "⚠️ Qualidade dos cadastros",
        expanded=False,
    ):

        q1, q2, q3 = (
            st.columns(3)
        )

        q1.metric(
            "Produtos sem custo",
            resumo.get(
                "produtos_sem_custo",
                0,
            ),
        )

        q2.metric(
            "Produtos sem preço",
            resumo.get(
                "produtos_sem_preco",
                0,
            ),
        )

        q3.metric(
            "Produtos inativos",
            resumo.get(
                "produtos_inativos",
                0,
            ),
        )

        if resumo.get(
            "produtos_sem_custo",
            0,
        ) > 0:

            st.warning(
                "Existem produtos ativos sem custo válido. "
                "Por esse motivo, o indicador financeiro é "
                "apresentado como Custo conhecido."
            )

    st.divider()

    # ======================================================
    # FILTROS
    # ======================================================
    st.subheader(
        "Filtros"
    )

    categorias = (
        listar_categorias_produtos()
    )

    opcoes_categoria = (
        ["TODAS"]
        +
        categorias
    )

    col1, col2 = (
        st.columns(2)
    )

    with col1:

        categoria_selecionada = (
            st.selectbox(
                "Categoria",
                options=opcoes_categoria,
                index=0,
                key=(
                    "relatorio_estoque_"
                    "categoria"
                ),
            )
        )

    with col2:

        situacao_selecionada = (
            st.selectbox(
                "Situação do estoque",
                options=SITUACOES_ESTOQUE,
                index=0,
                key=(
                    "relatorio_estoque_"
                    "situacao"
                ),
            )
        )

    categoria_filtro = None

    if (
        categoria_selecionada
        !=
        "TODAS"
    ):

        categoria_filtro = (
            categoria_selecionada
        )

    situacao_filtro = None

    if (
        situacao_selecionada
        !=
        "TODAS"
    ):

        situacao_filtro = (
            situacao_selecionada
        )

    # ======================================================
    # BUSCAR PRODUTOS
    # ======================================================
    df = listar_posicao_estoque(
        somente_ativos=True,
        categoria=categoria_filtro,
        situacao=situacao_filtro,
    )

    conferencia = (
        conferir_posicao_estoque()
    )

    st.divider()

    # ======================================================
    # PRODUTOS
    # ======================================================
    st.subheader(
        "Produtos"
    )

    if df is None or df.empty:

        st.info(
            "Nenhum produto encontrado "
            "para os filtros selecionados."
        )

    else:

        quantidade_produtos = (
            len(df)
        )

        quantidade_unidades = (
            pd.to_numeric(
                df["estoque"],
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
            .sum()
        )

        valor_custo_filtro = (
            pd.to_numeric(
                df[
                    "valor_estoque_custo"
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

        valor_venda_filtro = (
            pd.to_numeric(
                df[
                    "valor_estoque_venda"
                ],
                errors="coerce",
            )
            .fillna(0)
            .sum()
        )

        r1, r2, r3, r4 = (
            st.columns(4)
        )

        r1.metric(
            "Produtos encontrados",
            formatar_numero(
                quantidade_produtos
            ),
        )

        r2.metric(
            "Unidades",
            formatar_numero(
                quantidade_unidades
            ),
        )

        r3.metric(
            "Custo conhecido",
            formatar_moeda(
                valor_custo_filtro
            ),
        )

        r4.metric(
            "Potencial de venda",
            formatar_moeda(
                valor_venda_filtro
            ),
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
            column_config={
                "ID":
                    st.column_config.NumberColumn(
                        "ID",
                        format="%d",
                    ),

                "Estoque":
                    st.column_config.NumberColumn(
                        "Estoque",
                        format="%d",
                    ),

                "Mínimo":
                    st.column_config.NumberColumn(
                        "Mínimo",
                        format="%.0f",
                    ),

                "Custo":
                    st.column_config.NumberColumn(
                        "Custo",
                        format="R$ %.2f",
                    ),

                "Preço":
                    st.column_config.NumberColumn(
                        "Preço",
                        format="R$ %.2f",
                    ),

                "Valor a Custo":
                    st.column_config.NumberColumn(
                        "Valor a Custo",
                        format="R$ %.2f",
                    ),

                "Potencial de Venda":
                    st.column_config.NumberColumn(
                        "Potencial de Venda",
                        format="R$ %.2f",
                    ),
            },
        )

    # ======================================================
    # CONFERÊNCIA
    # ======================================================
    st.divider()

    with st.expander(
        "🔎 Conferência do relatório",
        expanded=False,
    ):

        if not conferencia:

            st.warning(
                "Não foi possível realizar "
                "a conferência."
            )

        else:

            conf1, conf2 = (
                st.columns(2)
            )

            with conf1:

                st.write(
                    "**Produtos ativos no banco:** "
                    f"{formatar_numero(conferencia.get('quantidade_produtos', 0))}"
                )

                st.write(
                    "**Unidades em estoque:** "
                    f"{formatar_numero(conferencia.get('quantidade_estoque', 0))}"
                )

            with conf2:

                st.write(
                    "**Custo conhecido:** "
                    f"{formatar_moeda(conferencia.get('valor_custo_conhecido', 0))}"
                )

                st.write(
                    "**Potencial de venda:** "
                    f"{formatar_moeda(conferencia.get('valor_potencial_venda', 0))}"
                )

            soma_situacoes = (
                resumo.get(
                    "produtos_sem_estoque",
                    0,
                )
                +
                resumo.get(
                    "produtos_abaixo_minimo",
                    0,
                )
                +
                resumo.get(
                    "produtos_no_minimo",
                    0,
                )
                +
                resumo.get(
                    "produtos_sem_minimo",
                    0,
                )
                +
                resumo.get(
                    "produtos_normais",
                    0,
                )
            )

            if (
                soma_situacoes
                ==
                resumo.get(
                    "produtos_ativos",
                    0,
                )
            ):

                st.success(
                    "Conferência OK: as situações "
                    "de estoque totalizam todos "
                    "os produtos ativos."
                )

            else:

                st.error(
                    "A soma das situações de estoque "
                    "não corresponde ao total "
                    "de produtos ativos."
                )

    # ======================================================
    # PDF
    # ======================================================
    st.divider()

    try:

        pdf = gerar_pdf_posicao_estoque(
            df=df,
            resumo=resumo,
            conferencia=conferencia,
            categoria_selecionada=(
                categoria_selecionada
            ),
            situacao_selecionada=(
                situacao_selecionada
            ),
        )

        nome_categoria = (
            str(
                categoria_selecionada
            )
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

        nome_situacao = (
            str(
                situacao_selecionada
            )
            .lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

        nome_arquivo = (
            "relatorio_posicao_estoque_"
            f"{nome_categoria}_"
            f"{nome_situacao}.pdf"
        )

        st.download_button(
            label=(
                "📄 Baixar relatório em PDF"
            ),
            data=pdf,
            file_name=nome_arquivo,
            mime="application/pdf",
            use_container_width=True,
            key=(
                "download_relatorio_"
                "posicao_estoque"
            ),
        )

    except Exception as erro:

        st.error(
            "Não foi possível gerar o PDF "
            "de posição de estoque."
        )

        st.exception(
            erro
        )