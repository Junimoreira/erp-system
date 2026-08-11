import streamlit as st
import pandas as pd

from database.connection import conectar

from services.xml_nfe_service import (
    ler_xml_nfe
)

from services.xml_conversao_service import (
    detectar_conversao_por_descricao,
    aplicar_conversao_produto
)

from services.xml_import_db import (
    importar_nfe_xml,
    buscar_produto_por_codigo,
    buscar_conversao_produto
)

from database.compras_db import (
    cadastrar_compra,
    listar_compras,
    buscar_itens_compra,
    excluir_compra
)

from database.produto_db import (
    listar_produtos
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)


# ==========================================================
# BUSCAR FORNECEDORES
# ==========================================================

def buscar_fornecedores():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                razao_social
            FROM fornecedores
            ORDER BY razao_social
        """

        return pd.read_sql(
            query,
            conn
        )

    except Exception as erro:

        st.error(
            f"Erro ao buscar fornecedores: "
            f"{erro}"
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==========================================================
# GERAR PRÉVIA DE CONVERSÃO XML
# ==========================================================

def gerar_previa_conversao_xml(
    dados_xml
):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    cursor = conn.cursor()

    try:

        linhas = []

        produtos_xml = dados_xml.get(
            "produtos",
            []
        )

        for indice_item, item in enumerate(
            produtos_xml
        ):

            # ==================================================
            # DADOS DO ITEM XML
            # ==================================================

            nome = str(
                item.get(
                    "nome",
                    ""
                ) or ""
            ).strip()

            codigo_barras = str(
                item.get(
                    "ean",
                    ""
                ) or ""
            ).strip()

            codigo_fornecedor = str(
                item.get(
                    "codigo",
                    ""
                ) or ""
            ).strip()

            unidade_xml = str(
                item.get(
                    "unidade",
                    ""
                ) or ""
            ).strip()

            quantidade_xml = float(
                item.get(
                    "quantidade",
                    0
                ) or 0
            )

            custo_xml = float(
                item.get(
                    "custo",
                    0
                ) or 0
            )

            subtotal_xml = float(
                item.get(
                    "subtotal",
                    quantidade_xml *
                    custo_xml
                ) or 0
            )

            # ==================================================
            # LOCALIZAR PRODUTO
            # ==================================================

            produto_id = buscar_produto_por_codigo(
                cursor,
                codigo_barras,
                codigo_fornecedor
            )

            # ==================================================
            # SE NÃO ENCONTROU PELO CÓDIGO,
            # TENTAR PELO NOME
            # ==================================================

            if produto_id is None:

                cursor.execute("""
                    SELECT id
                    FROM produtos
                    WHERE LOWER(
                        TRIM(nome)
                    ) = LOWER(
                        TRIM(%s)
                    )
                    LIMIT 1
                """, (
                    nome,
                ))

                encontrado = (
                    cursor.fetchone()
                )

                if encontrado:
                    produto_id = (
                        encontrado[0]
                    )

            # ==================================================
            # BUSCAR CONVERSÃO CADASTRADA
            # ==================================================

            conversao = (
                buscar_conversao_produto(
                    cursor,
                    produto_id,
                    codigo_barras,
                    codigo_fornecedor
                )
            )

            if conversao is not None:

                origem_conversao = (
                    "Cadastrada"
                )

            else:

                # ==============================================
                # TENTAR DETECÇÃO AUTOMÁTICA
                # ==============================================

                conversao_detectada = (
                    detectar_conversao_por_descricao(
                        nome
                    )
                )

                if conversao_detectada.get(
                    "detectado"
                ):

                    conversao = (
                        conversao_detectada
                    )

                    origem_conversao = (
                        "Detectada automaticamente"
                    )

                else:

                    conversao = {
                        "tipo_compra":
                            "UNIDADE",

                        "unidade_compra":
                            "UNIDADE",

                        "unidade_estoque":
                            "UNIDADE",

                        "fator_conversao":
                            1.0
                    }

                    origem_conversao = (
                        "Padrão"
                    )

            # ==================================================
            # APLICAR CONVERSÃO
            # ==================================================

            dados_conversao = (
                aplicar_conversao_produto(
                    quantidade_xml=
                        quantidade_xml,

                    custo_xml=
                        custo_xml,

                    subtotal_xml=
                        subtotal_xml,

                    conversao=
                        conversao
                )
            )

            # ==================================================
            # MONTAR LINHA
            # ==================================================

            linhas.append({

                "Índice Item":
                    indice_item,

                "Produto XML":
                    nome,

                "Produto cadastrado":
                    (
                        "Sim"
                        if produto_id
                        else "Não"
                    ),

                "Código Barras":
                    codigo_barras,

                "Código Fornecedor":
                    codigo_fornecedor,

                "Unidade XML":
                    unidade_xml,

                "Origem Conversão":
                    origem_conversao,

                "Tipo Compra":
                    dados_conversao[
                        "tipo_compra"
                    ],

                "Unidade Compra":
                    dados_conversao[
                        "unidade_compra"
                    ],

                "Qtd XML":
                    quantidade_xml,

                "Fator":
                    dados_conversao[
                        "fator_conversao"
                    ],

                "Fator Original":
                    dados_conversao[
                        "fator_conversao"
                    ],

                "Qtd Estoque":
                    dados_conversao[
                        "quantidade_estoque"
                    ],

                "Unidade Estoque":
                    dados_conversao[
                        "unidade_estoque"
                    ],

                "Custo XML":
                    custo_xml,

                "Custo Unitário Final":
                    dados_conversao[
                        "custo_unitario_estoque"
                    ],

                "Subtotal":
                    subtotal_xml
            })

        return pd.DataFrame(
            linhas
        )

    except Exception as erro:

        print(
            "Erro gerar_previa_conversao_xml:",
            erro
        )

        return pd.DataFrame()

    finally:

        cursor.close()
        conn.close()


# ==========================================================
# TELA DE COMPRAS
# ==========================================================

def tela_compras():

    st.title(
        "📦 Compras ERP"
    )

    abas = st.tabs([
        "➕ Nova Compra",
        "📄 Importar XML NF-e",
        "📋 Histórico",
        "🗑️ Excluir Compra"
    ])

    # ======================================================
    # ABA 1 - NOVA COMPRA
    # ======================================================

    with abas[0]:

        st.subheader(
            "📦 Lançar Compra"
        )

        fornecedores = (
            buscar_fornecedores()
        )

        produtos_df = (
            listar_produtos()
        )

        if fornecedores.empty:

            st.warning(
                "Nenhum fornecedor cadastrado."
            )

        elif (
            produtos_df is None
            or produtos_df.empty
        ):

            st.warning(
                "Nenhum produto cadastrado."
            )

        else:

            fornecedor_map = {
                row["razao_social"]:
                    row["id"]

                for _, row
                in fornecedores.iterrows()
            }

            with st.form(
                "form_compra",
                clear_on_submit=True,
                enter_to_submit=False
            ):

                fornecedor_nome = (
                    st.selectbox(
                        "Fornecedor",
                        list(
                            fornecedor_map.keys()
                        )
                    )
                )

                fornecedor_id = (
                    fornecedor_map[
                        fornecedor_nome
                    ]
                )

                st.divider()

                quantidade_itens = (
                    st.number_input(
                        "Quantidade de Itens",
                        min_value=1,
                        max_value=50,
                        value=1,
                        step=1
                    )
                )

                st.divider()

                produtos_compra = []
                total_compra = 0

                for i in range(
                    int(
                        quantidade_itens
                    )
                ):

                    st.markdown(
                        f"### Produto {i + 1}"
                    )

                    col1, col2, col3 = (
                        st.columns(3)
                    )

                    with col1:

                        produto_nome = (
                            st.selectbox(
                                f"Produto {i + 1}",
                                produtos_df[
                                    "nome"
                                ].tolist(),
                                key=(
                                    f"produto_{i}"
                                )
                            )
                        )

                    produto_row = (
                        produtos_df[
                            produtos_df[
                                "nome"
                            ] == produto_nome
                        ].iloc[0]
                    )

                    with col2:

                        quantidade = (
                            st.number_input(
                                f"Quantidade {i + 1}",
                                min_value=0.001,
                                step=1.0,
                                format="%.3f",
                                key=(
                                    f"quantidade_{i}"
                                )
                            )
                        )

                    custo_padrao = (
                        produto_row.get(
                            "custo",
                            0
                        )
                    )

                    if pd.isna(
                        custo_padrao
                    ):
                        custo_padrao = 0

                    with col3:

                        custo = (
                            st.number_input(
                                (
                                    "Custo Unitário "
                                    f"{i + 1}"
                                ),
                                min_value=0.0,
                                step=0.01,
                                format="%.2f",
                                value=float(
                                    custo_padrao
                                ),
                                key=(
                                    f"custo_{i}"
                                )
                            )
                        )

                    subtotal = (
                        quantidade *
                        custo
                    )

                    total_compra += (
                        subtotal
                    )

                    st.info(
                        "Subtotal: "
                        f"{formatar_moeda(subtotal)}"
                    )

                    produtos_compra.append({
                        "produto_id":
                            int(
                                produto_row[
                                    "id"
                                ]
                            ),

                        "quantidade":
                            quantidade,

                        "custo":
                            custo
                    })

                    st.divider()

                st.metric(
                    "💰 Total da Compra",
                    formatar_moeda(
                        total_compra
                    )
                )

                observacoes = (
                    st.text_area(
                        "Observações"
                    )
                )

                salvar = (
                    st.form_submit_button(
                        "💾 Finalizar Compra",
                        use_container_width=True
                    )
                )

                if salvar:

                    sucesso = cadastrar_compra(
                        fornecedor_id=
                            fornecedor_id,

                        produtos=
                            produtos_compra,

                        usuario=
                            st.session_state.get(
                                "usuario",
                                "Sistema"
                            ),

                        observacoes=
                            observacoes
                    )

                    if sucesso:

                        st.success(
                            "✅ Compra lançada "
                            "com sucesso!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Erro ao lançar compra."
                        )

    # ======================================================
    # ABA 2 - IMPORTAR XML
    # ======================================================

    with abas[1]:

        st.subheader(
            "📄 Importar XML NF-e"
        )

        arquivo_xml = (
            st.file_uploader(
                "Selecione o XML da NF-e",
                type=[
                    "xml"
                ]
            )
        )

        if arquivo_xml is None:

            st.info(
                "Envie um arquivo XML de NF-e "
                "para iniciar a importação."
            )

        else:

            try:

                # ==========================================
                # LER XML
                # ==========================================

                dados_xml = ler_xml_nfe(
                    arquivo_xml
                )

                fornecedor = (
                    dados_xml[
                        "fornecedor"
                    ]
                )

                produtos = (
                    dados_xml[
                        "produtos"
                    ]
                )

                st.success(
                    "✅ XML lido com sucesso."
                )

                # ==========================================
                # RESUMO NF-E
                # ==========================================

                col_a, col_b, col_c = (
                    st.columns(3)
                )

                with col_a:

                    st.metric(
                        "Número NF-e",
                        dados_xml.get(
                            "numero_nfe",
                            ""
                        )
                    )

                with col_b:

                    st.metric(
                        "Produtos",
                        len(
                            produtos
                        )
                    )

                with col_c:

                    st.metric(
                        "Total da NF-e",
                        formatar_moeda(
                            dados_xml.get(
                                "valor_total",
                                0
                            )
                        )
                    )

                # ==========================================
                # FORNECEDOR
                # ==========================================

                st.markdown(
                    "### 🏢 Fornecedor"
                )

                fornecedor_resumo = (
                    pd.DataFrame([{
                        "Razão Social":
                            fornecedor.get(
                                "razao_social",
                                ""
                            ),

                        "Nome Fantasia":
                            fornecedor.get(
                                "nome_fantasia",
                                ""
                            ),

                        "CNPJ":
                            fornecedor.get(
                                "cnpj",
                                ""
                            ),

                        "IE":
                            fornecedor.get(
                                "inscricao_estadual",
                                ""
                            ),

                        "Cidade":
                            fornecedor.get(
                                "cidade",
                                ""
                            ),

                        "UF":
                            fornecedor.get(
                                "estado",
                                ""
                            )
                    }])
                )

                st.dataframe(
                    fornecedor_resumo,
                    use_container_width=True,
                    hide_index=True
                )

                # ==========================================
                # CONFERÊNCIA INTELIGENTE
                # ==========================================

                st.markdown(
                    "### 🧠 Conferência Inteligente "
                    "da Conversão"
                )

                st.info(
                    "💡 O ERP sugere automaticamente "
                    "o fator de conversão. "
                    "Você pode alterar manualmente "
                    "somente a coluna **Fator** antes "
                    "de importar a NF-e."
                )

                df_previa_original = (
                    gerar_previa_conversao_xml(
                        dados_xml
                    )
                )

                pode_importar = True
                conversoes_confirmadas = []

                if df_previa_original.empty:

                    st.warning(
                        "Não foi possível gerar "
                        "a prévia de conversão."
                    )

                    pode_importar = False

                else:

                    # ======================================
                    # GARANTIR FATOR NUMÉRICO
                    # ======================================

                    df_editor = (
                        df_previa_original.copy()
                    )

                    df_editor["Fator"] = (
                        pd.to_numeric(
                            df_editor["Fator"],
                            errors="coerce"
                        )
                        .fillna(1.0)
                    )

                    # ======================================
                    # COLUNAS QUE SERÃO MOSTRADAS
                    # ======================================

                    colunas_editor = [
                        "Produto XML",
                        "Produto cadastrado",
                        "Unidade XML",
                        "Origem Conversão",
                        "Tipo Compra",
                        "Qtd XML",
                        "Fator"
                    ]

                    # ======================================
                    # EDITOR
                    # ======================================

                    df_editado_visivel = (
                        st.data_editor(
                            df_editor[
                                colunas_editor
                            ],
                            use_container_width=True,
                            hide_index=True,
                            disabled=[
                                "Produto XML",
                                "Produto cadastrado",
                                "Unidade XML",
                                "Origem Conversão",
                                "Tipo Compra",
                                "Qtd XML",
                                "Qtd Estoque",
                                "Custo XML",
                                "Custo Unitário Final",
                                "Subtotal"
                            ],
                            column_config={

                                "Produto XML":
                                    st.column_config.TextColumn(
                                        "Produto XML",
                                        width="large"
                                    ),

                                "Fator":
                                    st.column_config.NumberColumn(
                                        "✏️ Fator",
                                        help=(
                                            "Informe quantas "
                                            "unidades entram "
                                            "no estoque para "
                                            "cada unidade "
                                            "do XML."
                                        ),
                                        min_value=1.0,
                                        step=1.0,
                                        format="%.0f"
                                    ),

                                "Qtd XML":
                                    st.column_config.NumberColumn(
                                        "Qtd XML",
                                        format="%.3f"
                                    ),

                                "Qtd Estoque":
                                    st.column_config.NumberColumn(
                                        "Qtd Estoque",
                                        format="%.3f"
                                    ),

                                "Custo XML":
                                    st.column_config.NumberColumn(
                                        "Custo XML",
                                        format="R$ %.2f"
                                    ),

                                "Custo Unitário Final":
                                    st.column_config.NumberColumn(
                                        "Custo Unitário Final",
                                        format="R$ %.4f"
                                    ),

                                "Subtotal":
                                    st.column_config.NumberColumn(
                                        "Subtotal",
                                        format="R$ %.2f"
                                    )
                            },
                            key=(
                                "editor_conversao_xml_"
                                f"{dados_xml.get('chave_nfe', '')}"
                            )
                        )
                    )

                    # ======================================
                    # COPIAR FATORES EDITADOS DE VOLTA
                    # ======================================

                    df_previa = (
                        df_previa_original.copy()
                    )

                    fatores_editados = (
                        pd.to_numeric(
                            df_editado_visivel[
                                "Fator"
                            ],
                            errors="coerce"
                        )
                        .fillna(1.0)
                    )

                    fatores_editados = (
                        fatores_editados.clip(
                            lower=1.0
                        )
                    )

                    df_previa["Fator"] = (
                        fatores_editados.values
                    )

                    # ======================================
                    # IDENTIFICAR ALTERAÇÃO MANUAL
                    # ======================================

                    fator_original = (
                        pd.to_numeric(
                            df_previa[
                                "Fator Original"
                            ],
                            errors="coerce"
                        )
                        .fillna(1.0)
                    )

                    alterado_manualmente = (
                        (
                            df_previa[
                                "Fator"
                            ] - fator_original
                        ).abs() > 0.000001
                    )

                    df_previa.loc[
                        alterado_manualmente,
                        "Origem Conversão"
                    ] = "Manual"

                    # ======================================
                    # RECALCULAR QUANTIDADE DE ESTOQUE
                    # ======================================

                    df_previa[
                        "Qtd Estoque"
                    ] = (
                        pd.to_numeric(
                            df_previa[
                                "Qtd XML"
                            ],
                            errors="coerce"
                        )
                        .fillna(0)
                        *
                        df_previa[
                            "Fator"
                        ]
                    )

                    # ======================================
                    # RECALCULAR CUSTO UNITÁRIO FINAL
                    # ======================================

                    df_previa[
                        "Custo Unitário Final"
                    ] = (
                        pd.to_numeric(
                            df_previa[
                                "Custo XML"
                            ],
                            errors="coerce"
                        )
                        .fillna(0)
                        /
                        df_previa[
                            "Fator"
                        ]
                    )

                    # ======================================
                    # RESULTADO FINAL DA CONFERÊNCIA
                    # ======================================

                    st.markdown(
                        "#### ✅ Resultado após aplicar "
                        "os fatores"
                    )

                    resumo_conversao = (
                        df_previa[[
                            "Produto XML",
                            "Origem Conversão",
                            "Qtd XML",
                            "Fator",
                            "Qtd Estoque",
                            "Custo XML",
                            "Custo Unitário Final",
                            "Subtotal"
                        ]].copy()
                    )

                    resumo_exibicao = (
                        formatar_dataframe_brasil(
                            resumo_conversao,
                            com_hora=False,
                            moedas=True
                        )
                    )

                    st.dataframe(
                        resumo_exibicao,
                        use_container_width=True,
                        hide_index=True
                    )

                    # ======================================
                    # PRODUTOS SEM CADASTRO
                    # ======================================

                    sem_cadastro = (
                        df_previa[
                            df_previa[
                                "Produto cadastrado"
                            ] == "Não"
                        ]
                    )

                    # ======================================
                    # FATOR 1
                    # ======================================

                    sem_conversao = (
                        df_previa[
                            pd.to_numeric(
                                df_previa[
                                    "Fator"
                                ],
                                errors="coerce"
                            ).fillna(1.0) == 1.0
                        ]
                    )

                    # ======================================
                    # CONVERSÃO AUTOMÁTICA
                    # ======================================

                    conversao_detectada = (
                        df_previa[
                            df_previa[
                                "Origem Conversão"
                            ] ==
                            "Detectada automaticamente"
                        ]
                    )

                    # ======================================
                    # CONVERSÃO CADASTRADA
                    # ======================================

                    conversao_cadastrada = (
                        df_previa[
                            df_previa[
                                "Origem Conversão"
                            ] ==
                            "Cadastrada"
                        ]
                    )

                    # ======================================
                    # CONVERSÃO MANUAL
                    # ======================================

                    conversao_manual = (
                        df_previa[
                            df_previa[
                                "Origem Conversão"
                            ] ==
                            "Manual"
                        ]
                    )

                    if not sem_cadastro.empty:

                        st.warning(
                            f"{len(sem_cadastro)} "
                            "produto(s) ainda não estão "
                            "cadastrados. Eles serão "
                            "criados automaticamente."
                        )

                    if not conversao_detectada.empty:

                        st.success(
                            f"{len(conversao_detectada)} "
                            "conversão(ões) foram "
                            "detectadas automaticamente "
                            "pela descrição."
                        )

                    if not conversao_cadastrada.empty:

                        st.info(
                            f"{len(conversao_cadastrada)} "
                            "item(ns) utilizarão "
                            "conversões já cadastradas "
                            "no ERP."
                        )

                    if not conversao_manual.empty:

                        st.success(
                            f"✏️ {len(conversao_manual)} "
                            "item(ns) tiveram o fator "
                            "alterado manualmente."
                        )

                    if not sem_conversao.empty:

                        st.info(
                            f"{len(sem_conversao)} "
                            "item(ns) estão com fator 1. "
                            "Cada unidade do XML entrará "
                            "como uma unidade no estoque."
                        )

                    # ======================================
                    # FATORES MAIORES QUE 1
                    # ======================================

                    fatores_maiores = (
                        df_previa[
                            pd.to_numeric(
                                df_previa[
                                    "Fator"
                                ],
                                errors="coerce"
                            ).fillna(1.0) > 1
                        ]
                    )

                    if not fatores_maiores.empty:

                        st.warning(
                            "⚠️ Existem itens com fator "
                            "de conversão maior que 1. "
                            "Confira atentamente a "
                            "quantidade final antes "
                            "de importar."
                        )

                    # ======================================
                    # MONTAR CONVERSÕES CONFIRMADAS
                    #
                    # MUITO IMPORTANTE:
                    #
                    # O importador receberá exatamente
                    # estes fatores.
                    # ======================================

                    conversoes_confirmadas = []

                    for _, row in (
                        df_previa.iterrows()
                    ):

                        conversoes_confirmadas.append({

                            "indice_item":
                                int(
                                    row[
                                        "Índice Item"
                                    ]
                                ),

                            "produto_xml":
                                str(
                                    row.get(
                                        "Produto XML",
                                        ""
                                    ) or ""
                                ),

                            "codigo_barras":
                                str(
                                    row.get(
                                        "Código Barras",
                                        ""
                                    ) or ""
                                ),

                            "codigo_fornecedor":
                                str(
                                    row.get(
                                        "Código Fornecedor",
                                        ""
                                    ) or ""
                                ),

                            "fator_conversao":
                                float(
                                    row.get(
                                        "Fator",
                                        1
                                    ) or 1
                                ),

                            "tipo_compra":
                                str(
                                    row.get(
                                        "Tipo Compra",
                                        "UNIDADE"
                                    ) or "UNIDADE"
                                ),

                            "unidade_compra":
                                str(
                                    row.get(
                                        "Unidade Compra",
                                        "UNIDADE"
                                    ) or "UNIDADE"
                                ),

                            "unidade_estoque":
                                str(
                                    row.get(
                                        "Unidade Estoque",
                                        "UNIDADE"
                                    ) or "UNIDADE"
                                ),

                            "origem_conversao":
                                str(
                                    row.get(
                                        "Origem Conversão",
                                        "Confirmada"
                                    ) or "Confirmada"
                                )
                        })

                # ==========================================
                # AVISO IMPORTAÇÃO
                # ==========================================

                st.warning(
                    "Ao confirmar, o ERP irá registrar "
                    "a compra, atualizar estoque, "
                    "atualizar custos, criar histórico "
                    "de custo e criar lotes de estoque."
                )

                # ==========================================
                # CONFIRMAÇÃO
                # ==========================================

                confirmar_importacao = (
                    st.checkbox(
                        "Confirmo que conferi os fatores "
                        "e as quantidades que entrarão "
                        "no estoque e desejo importar "
                        "esta NF-e",
                        key=(
                            "confirmar_importar_xml_"
                            f"{dados_xml.get('chave_nfe', '')}"
                        )
                    )
                )

                # ==========================================
                # BOTÃO IMPORTAR
                # ==========================================

                if st.button(
                    "📥 Importar NF-e",
                    use_container_width=True,
                    disabled=(
                        not confirmar_importacao
                        or not pode_importar
                    )
                ):

                    with st.spinner(
                        "Importando XML e "
                        "atualizando estoque..."
                    ):

                        resultado = (
                            importar_nfe_xml(
                                dados_xml=
                                    dados_xml,

                                usuario=
                                    st.session_state.get(
                                        "usuario",
                                        "Sistema"
                                    ),

                                conversoes_confirmadas=
                                    conversoes_confirmadas
                            )
                        )

                    # ======================================
                    # IMPORTAÇÃO COM SUCESSO
                    # ======================================

                    if resultado.get(
                        "sucesso"
                    ):

                        st.success(
                            "✅ NF-e importada "
                            "com sucesso!"
                        )

                        st.markdown(
                            "### 📌 Resumo da Importação"
                        )

                        col1, col2, col3 = (
                            st.columns(3)
                        )

                        with col1:

                            st.metric(
                                "Compra Nº",
                                resultado.get(
                                    "compra_id",
                                    ""
                                )
                            )

                        with col2:

                            st.metric(
                                "NF-e",
                                resultado.get(
                                    "numero_nfe",
                                    ""
                                )
                            )

                        with col3:

                            st.metric(
                                "Valor Total",
                                formatar_moeda(
                                    resultado.get(
                                        "valor_total",
                                        0
                                    )
                                )
                            )

                        col4, col5, col6 = (
                            st.columns(3)
                        )

                        with col4:

                            st.metric(
                                "Produtos na Nota",
                                resultado.get(
                                    "total_produtos",
                                    0
                                )
                            )

                        with col5:

                            st.metric(
                                "Produtos Novos",
                                resultado.get(
                                    "produtos_novos",
                                    0
                                )
                            )

                        with col6:

                            st.metric(
                                "Produtos Atualizados",
                                resultado.get(
                                    "produtos_atualizados",
                                    0
                                )
                            )

                        st.info(
                            "Fornecedor: "
                            f"{resultado.get('fornecedor', '')}"
                        )

                        # ==================================
                        # ITENS IMPORTADOS
                        # ==================================

                        itens_convertidos = (
                            resultado.get(
                                "itens_convertidos",
                                []
                            )
                        )

                        if itens_convertidos:

                            st.markdown(
                                "### 🔁 Resultado "
                                "das Conversões"
                            )

                            itens_convertidos_df = (
                                pd.DataFrame(
                                    itens_convertidos
                                )
                            )

                            itens_convertidos_df = (
                                formatar_dataframe_brasil(
                                    itens_convertidos_df,
                                    com_hora=False,
                                    moedas=True
                                )
                            )

                            st.dataframe(
                                itens_convertidos_df,
                                use_container_width=True,
                                hide_index=True
                            )

                        st.success(
                            "Estoque, custos, histórico "
                            "de custos e lotes foram "
                            "atualizados com sucesso."
                        )

                    # ======================================
                    # NF-E DUPLICADA
                    # ======================================

                    elif resultado.get(
                        "duplicada"
                    ):

                        st.warning(
                            "⚠️ Esta NF-e já foi "
                            "importada anteriormente."
                        )

                        st.markdown(
                            "### 📌 Dados da "
                            "importação existente"
                        )

                        col1, col2, col3 = (
                            st.columns(3)
                        )

                        with col1:

                            st.metric(
                                "Compra Nº",
                                resultado.get(
                                    "compra_id",
                                    ""
                                )
                            )

                        with col2:

                            st.metric(
                                "NF-e",
                                resultado.get(
                                    "numero_nfe",
                                    ""
                                )
                            )

                        with col3:

                            st.metric(
                                "Fornecedor",
                                resultado.get(
                                    "fornecedor",
                                    ""
                                )
                            )

                        st.info(
                            "Chave NF-e: "
                            f"{resultado.get('chave_nfe', '')}"
                        )

                        st.warning(
                            "Nenhuma alteração foi "
                            "realizada no estoque, "
                            "custos ou compras."
                        )

                    # ======================================
                    # ERRO
                    # ======================================

                    else:

                        st.error(
                            resultado.get(
                                "mensagem",
                                "Erro ao importar NF-e."
                            )
                        )

            except Exception as erro:

                st.error(
                    f"Erro ao ler XML: {erro}"
                )

    # ======================================================
    # ABA 3 - HISTÓRICO
    # ======================================================

    with abas[2]:

        st.subheader(
            "📋 Histórico de Compras"
        )

        compras = listar_compras()

        if (
            compras is None
            or compras.empty
        ):

            st.info(
                "Nenhuma compra cadastrada."
            )

        else:

            busca = st.text_input(
                "🔎 Buscar fornecedor"
            )

            if busca:

                compras = compras[
                    compras[
                        "fornecedor"
                    ]
                    .astype(str)
                    .str.contains(
                        busca,
                        case=False,
                        na=False
                    )
                ]

            compras_exibicao = (
                formatar_dataframe_brasil(
                    compras,
                    com_hora=True,
                    moedas=True
                )
            )

            st.dataframe(
                compras_exibicao,
                use_container_width=True,
                height=400
            )

            st.divider()

            if compras.empty:

                st.info(
                    "Nenhuma compra encontrada "
                    "para o filtro informado."
                )

            else:

                compra_id = (
                    st.selectbox(
                        "Selecionar Compra",
                        compras[
                            "id"
                        ].tolist()
                    )
                )

                itens = (
                    buscar_itens_compra(
                        compra_id
                    )
                )

                st.markdown(
                    "### 📦 Itens da Compra"
                )

                if (
                    itens is None
                    or itens.empty
                ):

                    st.info(
                        "Nenhum item encontrado "
                        "para esta compra."
                    )

                else:

                    itens_exibicao = (
                        formatar_dataframe_brasil(
                            itens,
                            com_hora=False,
                            moedas=True
                        )
                    )

                    st.dataframe(
                        itens_exibicao,
                        use_container_width=True
                    )

    # ======================================================
    # ABA 4 - EXCLUIR COMPRA
    # ======================================================

    with abas[3]:

        st.subheader(
            "🗑️ Excluir Compra"
        )

        compras = listar_compras()

        if (
            compras is None
            or compras.empty
        ):

            st.info(
                "Nenhuma compra cadastrada."
            )

        else:

            compras_map = {

                (
                    f"{row['id']} | "
                    f"{row['fornecedor']} | "
                    f"{formatar_moeda(row['valor_total'])}"
                ):
                    row["id"]

                for _, row
                in compras.iterrows()
            }

            selecionado = (
                st.selectbox(
                    "Selecione a compra",
                    list(
                        compras_map.keys()
                    )
                )
            )

            compra_id = (
                compras_map[
                    selecionado
                ]
            )

            st.warning(
                "⚠️ A exclusão remove apenas "
                "o registro da compra. "
                "O estoque não será revertido."
            )

            confirmar = (
                st.checkbox(
                    "Confirmo que desejo "
                    "excluir esta compra",
                    key=(
                        "confirmar_excluir_compra"
                    )
                )
            )

            if st.button(
                "🗑️ Excluir Compra",
                use_container_width=True
            ):

                if not confirmar:

                    st.warning(
                        "Marque a confirmação "
                        "antes de excluir."
                    )

                else:

                    sucesso = (
                        excluir_compra(
                            compra_id
                        )
                    )

                    if sucesso:

                        st.success(
                            "✅ Compra excluída!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Erro ao excluir compra."
                        )