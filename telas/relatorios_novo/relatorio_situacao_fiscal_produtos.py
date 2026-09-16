import streamlit as st
import pandas as pd

from database.relatorios_produtos_db import (
    listar_pendencias_fiscais_produtos,
    classificar_situacao_fiscal_produtos,
)


from services.relatorios.pdf_relatorio import (
    gerar_pdf_profissional,
    criar_tabela_relatorio,
)


# ==========================================================
# CONSTANTES
# ==========================================================

CLASSIFICACOES_FISCAIS = [
    "TODAS",
    "SEM NCM",
    "NCM INADEQUADO",
    "A PARAMETRIZAR",
    "REVISADO INCOMPLETO",
    "APTO",
]


# ==========================================================
# FUNCOES AUXILIARES
# ==========================================================

def texto_seguro(valor):

    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except Exception:
        pass

    texto = str(valor).strip()

    if texto.lower() in {
        "",
        "nan",
        "none",
        "null",
    }:
        return ""

    return texto


def sim_nao(valor):
    return "SIM" if bool(valor) else "NAO"


def calcular_resumo(df):

    resumo = {
        "produtos_ativos": 0,
        "sem_ncm": 0,
        "ncm_inadequado": 0,
        "a_parametrizar": 0,
        "revisado_incompleto": 0,
        "apto": 0,
        "percentual_apto": 0.0,
    }

    if df is None or df.empty:
        return resumo

    resumo["produtos_ativos"] = len(df)

    contagem = (
        df["classificacao_fiscal"]
        .value_counts()
    )

    resumo["sem_ncm"] = int(
        contagem.get(
            "SEM NCM",
            0,
        )
    )

    resumo["ncm_inadequado"] = int(
        contagem.get(
            "NCM INADEQUADO",
            0,
        )
    )

    resumo["a_parametrizar"] = int(
        contagem.get(
            "A PARAMETRIZAR",
            0,
        )
    )

    resumo["revisado_incompleto"] = int(
        contagem.get(
            "REVISADO INCOMPLETO",
            0,
        )
    )

    resumo["apto"] = int(
        contagem.get(
            "APTO",
            0,
        )
    )

    if resumo["produtos_ativos"]:

        resumo["percentual_apto"] = (
            resumo["apto"]
            / resumo["produtos_ativos"]
            * 100
        )

    return resumo


def preparar_analitico_resumido(df):

    if df is None or df.empty:
        return pd.DataFrame()

    resultado = pd.DataFrame()

    resultado["ID"] = df["id"]

    resultado["Produto"] = (
        df["nome"]
        .fillna("")
        .astype(str)
    )

    resultado["Categoria"] = (
        df["categoria"]
        .apply(texto_seguro)
    )

    resultado["NCM"] = (
        df["ncm_normalizado"]
        .apply(texto_seguro)
    )

    resultado["Revisado"] = (
        df["fiscal_revisado"]
        .apply(sim_nao)
    )

    resultado["Situacao"] = (
        df["classificacao_fiscal"]
    )

    resultado["Pendencias"] = (
        df["pendencias_fiscais"]
        .apply(texto_seguro)
    )

    return resultado


def preparar_analitico_completo(df):

    if df is None or df.empty:
        return pd.DataFrame()

    resultado = pd.DataFrame()

    mapa = [
        ("ID", "id"),
        ("Produto", "nome"),
        ("Codigo Barras", "codigo_barras"),
        ("Categoria", "categoria"),
        ("NCM Cadastrado", "ncm"),
        ("NCM Normalizado", "ncm_normalizado"),
        ("CEST", "cest"),
        ("Origem", "origem_mercadoria"),
        ("Perfil ICMS", "perfil_icms"),
        ("CFOP Interno", "cfop_saida_interna"),
        ("CSOSN Interno", "csosn_saida_interna"),
        (
            "CFOP Interestadual",
            "cfop_saida_interestadual",
        ),
        (
            "CSOSN Interestadual",
            "csosn_saida_interestadual",
        ),
        ("CST PIS", "cst_pis_saida"),
        ("Aliquota PIS", "aliquota_pis_saida"),
        ("CST COFINS", "cst_cofins_saida"),
        (
            "Aliquota COFINS",
            "aliquota_cofins_saida",
        ),
        ("CST IBS/CBS", "cst_ibs_cbs_saida"),
        (
            "Classificacao Tributaria",
            "classificacao_tributaria_saida",
        ),
        ("Confianca", "fiscal_confianca"),
        ("Pendencias", "pendencias_fiscais"),
    ]

    for titulo, coluna in mapa:

        if coluna not in df.columns:
            continue

        resultado[titulo] = (
            df[coluna]
            .apply(texto_seguro)
        )

    resultado["Revisado"] = (
        df["fiscal_revisado"]
        .apply(sim_nao)
    )

    resultado["Situacao"] = (
        df["classificacao_fiscal"]
    )

    return resultado


# ==========================================================
# PDF SINTETICO
# ==========================================================

def gerar_pdf_fiscal_sintetico(df):

    resumo = calcular_resumo(
        df
    )

    indicadores = [
        {
            "titulo": "Produtos ativos",
            "valor": resumo["produtos_ativos"],
        },
        {
            "titulo": "Sem NCM",
            "valor": resumo["sem_ncm"],
        },
        {
            "titulo": "A parametrizar",
            "valor": resumo["a_parametrizar"],
        },
        {
            "titulo": "NCM inadequado",
            "valor": resumo["ncm_inadequado"],
        },
        {
            "titulo": "Revisado incompleto",
            "valor": resumo["revisado_incompleto"],
        },
        {
            "titulo": "Apto",
            "valor": resumo["apto"],
        },
    ]

    ordem = [
        "SEM NCM",
        "NCM INADEQUADO",
        "A PARAMETRIZAR",
        "REVISADO INCOMPLETO",
        "APTO",
    ]

    contagem = (
        df["classificacao_fiscal"]
        .value_counts()
        .reindex(
            ordem,
            fill_value=0,
        )
    )

    linhas_situacao = [
        [
            situacao,
            int(
                contagem.get(
                    situacao,
                    0,
                )
            ),
        ]
        for situacao in ordem
    ]

    tabela_situacao = (
        criar_tabela_relatorio(
            colunas=[
                "Situacao",
                "Produtos",
            ],
            linhas=linhas_situacao,
            larguras=[
                300,
                100,
            ],
            alinhamentos=[
                "LEFT",
                "RIGHT",
            ],
        )
    )

    df_categoria = df.copy()

    df_categoria[
        "categoria_relatorio"
    ] = (
        df_categoria["categoria"]
        .apply(texto_seguro)
        .replace(
            "",
            "SEM CATEGORIA",
        )
    )

    por_categoria = (
        df_categoria
        .groupby(
            [
                "categoria_relatorio",
                "classificacao_fiscal",
            ],
            dropna=False,
        )
        .size()
        .unstack(
            fill_value=0
        )
        .reindex(
            columns=ordem,
            fill_value=0,
        )
        .reset_index()
    )

    por_categoria[
        "Total"
    ] = por_categoria[
        ordem
    ].sum(
        axis=1
    )

    por_categoria = (
        por_categoria
        .sort_values(
            "Total",
            ascending=False,
        )
    )

    linhas_categoria = []

    for _, linha in (
        por_categoria.iterrows()
    ):

        linhas_categoria.append(
            [
                linha[
                    "categoria_relatorio"
                ],
                int(
                    linha[
                        "SEM NCM"
                    ]
                ),
                int(
                    linha[
                        "A PARAMETRIZAR"
                    ]
                ),
                int(
                    linha[
                        "REVISADO INCOMPLETO"
                    ]
                ),
                int(
                    linha[
                        "APTO"
                    ]
                ),
                int(
                    linha[
                        "Total"
                    ]
                ),
            ]
        )

    tabela_categoria = (
        criar_tabela_relatorio(
            colunas=[
                "Categoria",
                "Sem NCM",
                "A parametrizar",
                "Rev. incompleto",
                "Apto",
                "Total",
            ],
            linhas=linhas_categoria,
            larguras=[
                190,
                70,
                90,
                95,
                55,
                55,
            ],
            alinhamentos=[
                "LEFT",
                "RIGHT",
                "RIGHT",
                "RIGHT",
                "RIGHT",
                "RIGHT",
            ],
        )
    )

    percentual = float(
        resumo[
            "percentual_apto"
        ]
    )

    texto_progresso = (
        f"{percentual:.1f}% dos produtos ativos "
        "estao classificados como APTO segundo "
        "a regra cadastral avaliada pelo ERP."
    )

    secoes = [
        {
            "titulo":
                "Distribuicao por Situacao Fiscal",

            "texto":
                (
                    "Distribuicao dos produtos ativos "
                    "conforme o nivel atual de "
                    "preparacao cadastral fiscal."
                ),

            "tabela":
                tabela_situacao,

            "observacao":
                (
                    "As classificacoes sao exclusivas: "
                    "cada produto aparece em apenas "
                    "uma situacao."
                ),
        },
        {
            "titulo":
                "Progresso do Saneamento Fiscal",

            "texto":
                texto_progresso,

            "observacao":
                (
                    "APTO significa cadastro completo "
                    "segundo a regra avaliada pelo ERP. "
                    "Nao representa validacao juridica "
                    "da classificacao tributaria."
                ),
        },
        {
            "titulo":
                "Situacao por Categoria",

            "texto":
                (
                    "Distribuicao das pendencias fiscais "
                    "entre as categorias cadastradas."
                ),

            "tabela":
                tabela_categoria,
        },
        {
            "titulo":
                "Criterio do Relatorio",

            "texto":
                (
                    "O relatorio identifica campos "
                    "ausentes e problemas de formato "
                    "conforme as regras cadastrais "
                    "implementadas no ERP."
                ),

            "observacao":
                (
                    "A existencia de NCM em formato "
                    "utilizavel nao confirma que sua "
                    "classificacao fiscal esteja "
                    "legalmente correta. CEST e "
                    "parametrizacao interestadual "
                    "dependem da operacao e nao sao "
                    "tratados automaticamente como "
                    "erro neste resumo."
                ),
        },
    ]

    return gerar_pdf_profissional(
        titulo=(
            "Relatorio Sintetico da "
            "Situacao Fiscal dos Produtos"
        ),
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )



# ==========================================================
# PDF ANALITICO
# ==========================================================

def gerar_pdf_fiscal_analitico(
    df,
    categoria="TODAS",
    situacao="TODAS",
    busca="",
):

    quantidade = len(
        df
    )

    # ======================================================
    # INDICADORES
    # ======================================================

    revisados = 0
    nao_revisados = 0

    if (
        "fiscal_revisado"
        in df.columns
    ):

        revisados = int(
            df[
                "fiscal_revisado"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        nao_revisados = (
            quantidade
            - revisados
        )

    com_ncm = 0
    sem_ncm = 0

    if (
        "ncm_formato_valido"
        in df.columns
    ):

        com_ncm = int(
            df[
                "ncm_formato_valido"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        sem_ncm = (
            quantidade
            - com_ncm
        )

    indicadores = [
        {
            "titulo":
                "Produtos encontrados",
            "valor":
                quantidade,
        },
        {
            "titulo":
                "Com NCM utilizavel",
            "valor":
                com_ncm,
        },
        {
            "titulo":
                "Sem NCM utilizavel",
            "valor":
                sem_ncm,
        },
        {
            "titulo":
                "Revisados",
            "valor":
                revisados,
        },
        {
            "titulo":
                "Nao revisados",
            "valor":
                nao_revisados,
        },
    ]

    # ======================================================
    # FILTROS
    # ======================================================

    filtros = [
        (
            "Categoria: "
            f"{categoria}"
        ),
        (
            "Situacao fiscal: "
            f"{situacao}"
        ),
    ]

    if busca.strip():

        filtros.append(
            "Busca: "
            f"{busca.strip()}"
        )

    else:

        filtros.append(
            "Busca: nenhuma"
        )

    texto_filtros = (
        " | ".join(
            filtros
        )
    )

    # ======================================================
    # PRODUTOS
    # ======================================================

    linhas_produtos = []

    ordenado = (
        df.copy()
        .sort_values(
            by=[
                "classificacao_fiscal",
                "categoria",
                "nome",
                "id",
            ],
            na_position="last",
        )
    )

    for _, produto in (
        ordenado.iterrows()
    ):

        produto_id = (
            texto_seguro(
                produto.get(
                    "id"
                )
            )
        )

        nome = (
            texto_seguro(
                produto.get(
                    "nome"
                )
            )
        )

        categoria_produto = (
            texto_seguro(
                produto.get(
                    "categoria"
                )
            )
            or
            "SEM CATEGORIA"
        )

        ncm = (
            texto_seguro(
                produto.get(
                    "ncm_normalizado"
                )
            )
        )

        if not ncm:

            ncm = "-"

        revisado = (
            "SIM"
            if bool(
                produto.get(
                    "fiscal_revisado",
                    False,
                )
            )
            else "NAO"
        )

        classificacao = (
            texto_seguro(
                produto.get(
                    "classificacao_fiscal"
                )
            )
            or
            "-"
        )

        pendencias = (
            texto_seguro(
                produto.get(
                    "pendencias_fiscais"
                )
            )
            or
            "SEM PENDENCIAS CADASTRAIS"
        )

        linhas_produtos.append(
            [
                produto_id,
                nome,
                categoria_produto,
                ncm,
                revisado,
                classificacao,
                pendencias,
            ]
        )

    tabela_produtos = (
        criar_tabela_relatorio(
            colunas=[
                "ID",
                "Produto",
                "Categoria",
                "NCM",
                "Rev.",
                "Situacao",
                "Pendencias",
            ],
            linhas=linhas_produtos,
            larguras=[
                32,
                180,
                105,
                60,
                35,
                90,
                220,
            ],
            alinhamentos=[
                "RIGHT",
                "LEFT",
                "LEFT",
                "CENTER",
                "CENTER",
                "LEFT",
                "LEFT",
            ],
            quebrar_texto=True,
        )
    )

    # ======================================================
    # SECOES
    # ======================================================

    secoes = [
        {
            "titulo":
                "Filtros Aplicados",

            "texto":
                texto_filtros,

            "observacao":
                (
                    "O PDF apresenta somente os produtos "
                    "encontrados pelos filtros utilizados "
                    "na tela analitica."
                ),
        },
        {
            "titulo":
                "Produtos para Conferencia Fiscal",

            "texto":
                (
                    f"Foram encontrados {quantidade} "
                    "produto(s) para conferencia e "
                    "saneamento cadastral."
                ),

            "tabela":
                tabela_produtos,

            "observacao":
                (
                    "As pendencias representam o checklist "
                    "cadastral atualmente implementado "
                    "no ERP."
                ),
        },
        {
            "titulo":
                "Criterio do Relatorio",

            "texto":
                (
                    "A coluna NCM utiliza a versao "
                    "normalizada do codigo cadastrado "
                    "quando disponivel."
                ),

            "observacao":
                (
                    "NCM em formato utilizavel nao confirma "
                    "classificacao tributaria legalmente "
                    "correta. A classificacao APTO indica "
                    "somente completude segundo a regra "
                    "cadastral avaliada pelo ERP. CEST e "
                    "parametrizacao interestadual dependem "
                    "da operacao e sua ausencia nao e "
                    "automaticamente tratada como erro."
                ),
        },
    ]

    return gerar_pdf_profissional(
        titulo=(
            "Relatorio Analitico da "
            "Situacao Fiscal dos Produtos"
        ),
        indicadores=indicadores,
        secoes=secoes,
        orientacao="paisagem",
    )



# ==========================================================
# TELA
# ==========================================================

def tela_relatorio_situacao_fiscal_produtos():

    st.title(
        "Situação Fiscal dos Produtos"
    )

    st.caption(
        "Acompanhamento do saneamento e da "
        "parametrizacao fiscal dos produtos ativos."
    )

    st.info(
        "Este relatorio identifica campos ausentes "
        "e problemas de formato conforme as regras "
        "cadastrais do ERP. Ele nao confirma, por si "
        "so, que NCM ou tributacao estejam legalmente "
        "corretos."
    )

    # ======================================================
    # CONSULTA UNICA
    # ======================================================

    df = listar_pendencias_fiscais_produtos(
        somente_ativos=True
    )

    if df is None or df.empty:

        st.warning(
            "Nenhum produto ativo encontrado."
        )

        return

    df = classificar_situacao_fiscal_produtos(
        df
    )

    # ======================================================
    # VISAO
    # ======================================================

    visao = st.radio(
        "Tipo de relatorio",
        [
            "Sintetico",
            "Analitico",
        ],
        horizontal=True,
        key="relatorio_fiscal_visao",
    )

    st.divider()

    # ======================================================
    # SINTETICO
    # ======================================================

    if visao == "Sintetico":

        resumo = calcular_resumo(
            df
        )

        st.subheader(
            "Resumo da situação fiscal"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Produtos ativos",
            resumo["produtos_ativos"],
        )

        col2.metric(
            "Sem NCM",
            resumo["sem_ncm"],
        )

        col3.metric(
            "A parametrizar",
            resumo["a_parametrizar"],
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "NCM inadequado",
            resumo["ncm_inadequado"],
        )

        col5.metric(
            "Revisado incompleto",
            resumo["revisado_incompleto"],
        )

        col6.metric(
            "Apto",
            resumo["apto"],
        )

        st.markdown(
            "### Progresso do saneamento fiscal"
        )

        percentual = float(
            resumo["percentual_apto"]
        )

        st.progress(
            min(
                max(
                    percentual / 100,
                    0.0,
                ),
                1.0,
            )
        )

        st.caption(
            f"{percentual:.1f}% dos produtos ativos "
            "estao classificados como APTO pela "
            "regra cadastral atual do ERP."
        )

        st.markdown(
            "### Distribuição por situação"
        )

        ordem = [
            "SEM NCM",
            "NCM INADEQUADO",
            "A PARAMETRIZAR",
            "REVISADO INCOMPLETO",
            "APTO",
        ]

        distribuicao = (
            df["classificacao_fiscal"]
            .value_counts()
            .reindex(
                ordem,
                fill_value=0,
            )
            .rename_axis(
                "Situacao"
            )
            .reset_index(
                name="Produtos"
            )
        )

        st.dataframe(
            distribuicao,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown(
            "### Situação por categoria"
        )

        df_categoria = df.copy()

        df_categoria[
            "categoria_relatorio"
        ] = (
            df_categoria["categoria"]
            .apply(texto_seguro)
            .replace(
                "",
                "SEM CATEGORIA",
            )
        )

        por_categoria = (
            df_categoria
            .groupby(
                [
                    "categoria_relatorio",
                    "classificacao_fiscal",
                ],
                dropna=False,
            )
            .size()
            .unstack(
                fill_value=0
            )
            .reindex(
                columns=ordem,
                fill_value=0,
            )
            .reset_index()
            .rename(
                columns={
                    "categoria_relatorio":
                        "Categoria",
                }
            )
        )

        por_categoria[
            "Total"
        ] = por_categoria[
            ordem
        ].sum(
            axis=1
        )

        por_categoria = (
            por_categoria
            .sort_values(
                by="Total",
                ascending=False,
            )
        )

        st.dataframe(
            por_categoria,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        st.caption(
            "O indicador APTO representa somente o "
            "preenchimento completo da regra cadastral "
            "avaliada por este relatorio."
        )

        st.divider()

        st.subheader(
            "Documento profissional"
        )

        try:

            pdf_sintetico = (
                gerar_pdf_fiscal_sintetico(
                    df
                )
            )

            st.download_button(
                label=(
                    "Baixar relatorio sintetico em PDF"
                ),
                data=pdf_sintetico.getvalue(),
                file_name=(
                    "relatorio_sintetico_"
                    "situacao_fiscal_produtos.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
                key=(
                    "download_pdf_fiscal_"
                    "sintetico"
                ),
            )

        except Exception as erro:

            st.error(
                "Nao foi possivel gerar o "
                "PDF sintetico."
            )

            st.exception(
                erro
            )

        return

    # ======================================================
    # ANALITICO
    # ======================================================

    st.subheader(
        "Detalhamento dos produtos"
    )

    categorias = sorted(
        {
            texto_seguro(valor)
            for valor in df["categoria"]
            if texto_seguro(valor)
        }
    )

    filtro1, filtro2 = st.columns(2)

    with filtro1:

        categoria = st.selectbox(
            "Categoria",
            ["TODAS"] + categorias,
            index=0,
            key=(
                "relatorio_fiscal_"
                "categoria_analitico"
            ),
        )

    with filtro2:

        situacao = st.selectbox(
            "Situacao fiscal",
            CLASSIFICACOES_FISCAIS,
            index=0,
            key=(
                "relatorio_fiscal_"
                "situacao_analitico"
            ),
        )

    busca = st.text_input(
        "Buscar produto",
        placeholder=(
            "Digite nome, ID, codigo de barras ou NCM..."
        ),
        key=(
            "relatorio_fiscal_"
            "busca_analitico"
        ),
    )

    filtrado = df.copy()

    if categoria != "TODAS":

        filtrado = filtrado[
            filtrado["categoria"]
            .fillna("")
            .astype(str)
            == categoria
        ].copy()

    if situacao != "TODAS":

        filtrado = filtrado[
            filtrado["classificacao_fiscal"]
            == situacao
        ].copy()

    if busca.strip():

        termo = busca.strip().lower()

        mascara = pd.Series(
            False,
            index=filtrado.index,
        )

        campos_busca = [
            "id",
            "nome",
            "codigo_barras",
            "ncm",
            "ncm_normalizado",
            "categoria",
        ]

        for campo in campos_busca:

            if campo not in filtrado.columns:
                continue

            mascara = (
                mascara
                | filtrado[campo]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(
                    termo,
                    regex=False,
                )
            )

        filtrado = filtrado[
            mascara
        ].copy()

    st.markdown(
        f"**Produtos encontrados: {len(filtrado)}**"
    )

    if filtrado.empty:

        st.warning(
            "Nenhum produto encontrado "
            "para os filtros selecionados."
        )

        return

    st.markdown(
        "### Pendências para trabalho"
    )

    resumido = preparar_analitico_resumido(
        filtrado
    )

    st.dataframe(
        resumido,
        use_container_width=True,
        hide_index=True,
        height=600,
    )

    with st.expander(
        "Ver parametrização fiscal completa",
        expanded=False,
    ):

        completo = (
            preparar_analitico_completo(
                filtrado
            )
        )

        st.dataframe(
            completo,
            use_container_width=True,
            hide_index=True,
            height=600,
        )

    st.caption(
        "CEST e parametrizacao interestadual sao "
        "exibidos para conferencia, mas a ausencia "
        "desses campos nao e classificada "
        "automaticamente como erro neste relatorio."
    )


    st.divider()

    st.subheader(
        "Documento profissional"
    )

    try:

        pdf_analitico = (
            gerar_pdf_fiscal_analitico(
                filtrado,
                categoria=categoria,
                situacao=situacao,
                busca=busca,
            )
        )

        st.download_button(
            label=(
                "Baixar relatorio analitico em PDF"
            ),
            data=pdf_analitico.getvalue(),
            file_name=(
                "relatorio_analitico_"
                "situacao_fiscal_produtos.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
            key="download_pdf_fiscal_analitico",
        )

    except Exception as erro:

        st.error(
            "Nao foi possivel gerar o "
            "PDF analitico."
        )

        st.exception(
            erro
        )
