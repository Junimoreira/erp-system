import pandas as pd
import streamlit as st

from database.produto_db import (
    listar_produtos,
    buscar_produto_por_id,
    listar_produtos_sem_codigo,
    cadastrar_produto,
    atualizar_produto,
    atualizar_codigo_barras,
    excluir_produto,
    buscar_produto_por_codigo
)

from utils.precificacao import (
    calcular_preco_venda,
    buscar_margem_padrao
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)


UNIDADES_PRODUTO = [
    "UN",
    "KG",
    "CX",
    "PC",
    "LT"
]


def tratar_texto(valor):

    if valor is None:
        return ""

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def normalizar_campo(valor):

    valor = tratar_texto(valor)

    if valor == "":
        return None

    return valor


def limpar_formulario_novo_produto():

    valores_iniciais = {
        "novo_nome": "",
        "novo_codigo_barras": "",
        "novo_sku": "",
        "novo_referencia": "",
        "novo_marca": "",
        "novo_categoria": "",
        "novo_unidade": "UN",
        "novo_ncm": "",
        "novo_cest": "",
        "novo_cfop": "",
        "novo_custo": 0.0,
        "novo_imposto": 0.0,
        "novo_frete": 0.0,
        "novo_cartao": 0.0,
        "novo_estoque": 0,
        "novo_estoque_minimo": 0,
        "novo_localizacao": "",
        "novo_observacoes": "",
        "novo_ativo": True
    }

    for chave, valor in valores_iniciais.items():
        st.session_state[chave] = valor

    st.session_state.pop(
        "novo_preco",
        None
    )

    st.session_state.pop(
        "novo_margem",
        None
    )


def carregar_produto_para_edicao(produto):

    unidade = tratar_texto(
        produto.get(
            "unidade",
            "UN"
        )
    ).upper()

    if unidade not in UNIDADES_PRODUTO:
        unidade = "UN"

    st.session_state["edit_nome"] = tratar_texto(
        produto.get("nome")
    )

    st.session_state["edit_codigo"] = tratar_texto(
        produto.get("codigo_barras")
    )

    st.session_state["edit_sku"] = tratar_texto(
        produto.get("sku")
    )

    st.session_state["edit_referencia"] = tratar_texto(
        produto.get("referencia")
    )

    st.session_state["edit_marca"] = tratar_texto(
        produto.get("marca")
    )

    st.session_state["edit_categoria"] = tratar_texto(
        produto.get("categoria")
    )

    st.session_state["edit_unidade"] = unidade

    st.session_state["edit_ncm"] = tratar_texto(
        produto.get("ncm")
    )

    st.session_state["edit_cest"] = tratar_texto(
        produto.get("cest")
    )

    st.session_state["edit_cfop"] = tratar_texto(
        produto.get("cfop_padrao")
    )

    st.session_state["edit_custo"] = float(
        produto.get("custo") or 0
    )

    st.session_state["edit_preco"] = float(
        produto.get("preco") or 0
    )

    st.session_state["edit_estoque"] = int(
        produto.get("estoque") or 0
    )

    st.session_state["edit_estoque_minimo"] = int(
        produto.get("estoque_minimo") or 0
    )

    st.session_state["edit_localizacao"] = tratar_texto(
        produto.get("localizacao")
    )

    st.session_state["edit_observacoes"] = tratar_texto(
        produto.get("observacoes")
    )

    ativo = produto.get("ativo")

    if ativo is None:
        ativo = True

    st.session_state["edit_ativo"] = bool(ativo)


def limpar_estado_edicao():

    chaves = [
        "edit_nome",
        "edit_codigo",
        "edit_sku",
        "edit_referencia",
        "edit_marca",
        "edit_categoria",
        "edit_unidade",
        "edit_ncm",
        "edit_cest",
        "edit_cfop",
        "edit_custo",
        "edit_preco",
        "edit_estoque",
        "edit_estoque_minimo",
        "edit_localizacao",
        "edit_observacoes",
        "edit_ativo",
        "edit_produto_carregado_id"
    ]

    for chave in chaves:
        st.session_state.pop(
            chave,
            None
        )


def tela_produtos():

    if st.session_state.pop(
        "limpar_novo_produto_pendente",
        False
    ):
        limpar_formulario_novo_produto()

    abas = st.tabs(
        [
            "➕ Novo Produto",
            "📋 Produtos",
            "✏️ Editar Produto",
            "🏷️ Código de Barras"
        ]
    )

    # =========================================================
    # NOVO PRODUTO
    # =========================================================

    with abas[0]:

        mensagem_novo = st.session_state.pop(
            "mensagem_novo_produto",
            None
        )

        if mensagem_novo:
            st.success(mensagem_novo)

        st.subheader("📦 Cadastro de Produto")
        st.markdown("## 📦 Dados Básicos")

        col1, col2 = st.columns(2)

        with col1:

            nome = st.text_input(
                "Nome do Produto",
                key="novo_nome"
            )

            codigo_barras = st.text_input(
                "Código de Barras",
                key="novo_codigo_barras"
            )

            sku = st.text_input(
                "SKU",
                key="novo_sku"
            )

            referencia = st.text_input(
                "Referência",
                key="novo_referencia"
            )

            marca = st.text_input(
                "Marca",
                key="novo_marca"
            )

        with col2:

            categoria = st.text_input(
                "Categoria",
                key="novo_categoria"
            )

            unidade = st.selectbox(
                "Unidade",
                UNIDADES_PRODUTO,
                key="novo_unidade"
            )

            ncm = st.text_input(
                "NCM",
                key="novo_ncm"
            )

            cest = st.text_input(
                "CEST",
                key="novo_cest"
            )

            cfop_padrao = st.text_input(
                "CFOP",
                key="novo_cfop"
            )

        st.divider()
        st.markdown("## 💰 Financeiro")

        col3, col4, col5 = st.columns(3)

        with col3:

            custo = st.number_input(
                "Custo",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="novo_custo"
            )

            margem_padrao = float(
                buscar_margem_padrao() or 30
            )

            st.number_input(
                "Margem Padrão (%)",
                value=margem_padrao,
                disabled=True,
                format="%.2f",
                key="novo_margem"
            )

        with col4:

            imposto = st.number_input(
                "Imposto (%)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="novo_imposto"
            )

            frete = st.number_input(
                "Frete (%)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="novo_frete"
            )

            taxa_cartao = st.number_input(
                "Taxa Cartão (%)",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="novo_cartao"
            )

        preco_automatico = calcular_preco_venda(
            custo=custo,
            imposto=imposto,
            frete=frete,
            cartao=taxa_cartao,
            margem=margem_padrao
        )

        if "novo_preco" not in st.session_state:

            st.session_state["novo_preco"] = float(
                preco_automatico
            )

        lucro_estimado = round(
            float(st.session_state["novo_preco"]) -
            float(custo),
            2
        )

        with col5:

            st.info(
                "💡 Preço calculado automaticamente."
            )

            preco = st.number_input(
                "Preço Venda",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="novo_preco"
            )

            st.metric(
                "Preço Automático",
                formatar_moeda(
                    preco_automatico
                )
            )

            st.metric(
                "Lucro Estimado",
                formatar_moeda(
                    lucro_estimado
                )
            )

        st.divider()
        st.markdown("## 📦 Estoque")

        col6, col7 = st.columns(2)

        with col6:

            estoque = st.number_input(
                "Estoque",
                min_value=0,
                step=1,
                format="%d",
                key="novo_estoque"
            )

        with col7:

            estoque_minimo = st.number_input(
                "Estoque Mínimo",
                min_value=0,
                step=1,
                format="%d",
                key="novo_estoque_minimo"
            )

        localizacao = st.text_input(
            "Localização",
            key="novo_localizacao"
        )

        observacoes = st.text_area(
            "Observações",
            key="novo_observacoes"
        )

        ativo = st.checkbox(
            "Produto ativo",
            value=True,
            key="novo_ativo"
        )

        st.divider()

        salvar_novo = st.button(
            "💾 Salvar Produto",
            use_container_width=True,
            key="btn_salvar_produto"
        )

        if salvar_novo:

            nome_normalizado = tratar_texto(
                nome
            )

            if not nome_normalizado:

                st.warning(
                    "Informe o nome do produto."
                )

            else:

                sucesso = cadastrar_produto(
                    nome=nome_normalizado,
                    preco=float(preco),
                    estoque=int(estoque),
                    codigo_barras=normalizar_campo(
                        codigo_barras
                    ),
                    sku=normalizar_campo(
                        sku
                    ),
                    referencia=normalizar_campo(
                        referencia
                    ),
                    marca=normalizar_campo(
                        marca
                    ),
                    categoria=normalizar_campo(
                        categoria
                    ),
                    unidade=unidade,
                    ncm=normalizar_campo(
                        ncm
                    ),
                    cest=normalizar_campo(
                        cest
                    ),
                    cfop_padrao=normalizar_campo(
                        cfop_padrao
                    ),
                    custo=float(custo),
                    margem_lucro=float(
                        margem_padrao
                    ),
                    estoque_minimo=int(
                        estoque_minimo
                    ),
                    localizacao=normalizar_campo(
                        localizacao
                    ),
                    ativo=bool(ativo),
                    observacoes=normalizar_campo(
                        observacoes
                    )
                )

                if sucesso:

                    st.session_state[
                        "limpar_novo_produto_pendente"
                    ] = True

                    st.session_state[
                        "mensagem_novo_produto"
                    ] = (
                        "✅ Produto cadastrado "
                        "com sucesso!"
                    )

                    st.rerun()

    # =========================================================
    # LISTAGEM DE PRODUTOS
    # =========================================================

    with abas[1]:

        st.subheader("📋 Produtos")

        busca = st.text_input(
            "🔎 Buscar produto",
            key="buscar_produto"
        )

        df_produtos = listar_produtos()

        if df_produtos.empty:

            st.info(
                "Nenhum produto cadastrado."
            )

        else:

            df_produtos = df_produtos.fillna("")

            if busca:

                df_produtos = df_produtos[
                    df_produtos[
                        "nome"
                    ].astype(str).str.contains(
                        busca,
                        case=False,
                        na=False
                    )
                ]

            df_exibicao = formatar_dataframe_brasil(
                df_produtos,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                height=500
            )

    # =========================================================
    # EDITAR PRODUTO
    # =========================================================

    with abas[2]:

        mensagem_edicao = st.session_state.pop(
            "mensagem_edicao_produto",
            None
        )

        if mensagem_edicao:
            st.success(mensagem_edicao)

        st.subheader("✏️ Editar Produto")

        df_edicao = listar_produtos()

        if df_edicao.empty:

            st.info(
                "Sem produtos cadastrados."
            )

        else:

            produtos_resumo = {
                int(row["id"]): tratar_texto(
                    row["nome"]
                )
                for _, row in df_edicao.iterrows()
            }

            ids_produtos = list(
                produtos_resumo.keys()
            )

            produto_id = st.selectbox(
                "Selecione o Produto",
                options=ids_produtos,
                format_func=lambda identificador: (
                    f"{identificador} - "
                    f"{produtos_resumo[identificador]}"
                ),
                key="editar_select_id"
            )

            produto_carregado_id = (
                st.session_state.get(
                    "edit_produto_carregado_id"
                )
            )

            if produto_carregado_id != produto_id:

                produto_para_carregar = (
                    buscar_produto_por_id(
                        produto_id
                    )
                )

                if produto_para_carregar is not None:

                    carregar_produto_para_edicao(
                        produto_para_carregar
                    )

                    st.session_state[
                        "edit_produto_carregado_id"
                    ] = produto_id

            produto = buscar_produto_por_id(
                produto_id
            )

            if produto is None:

                st.error(
                    "Não foi possível carregar "
                    "o produto selecionado."
                )

            else:

                st.divider()

                col1, col2 = st.columns(2)

                with col1:

                    nome_edit = st.text_input(
                        "Nome",
                        key="edit_nome"
                    )

                    codigo_barras_edit = st.text_input(
                        "Código de Barras",
                        key="edit_codigo"
                    )

                    sku_edit = st.text_input(
                        "SKU",
                        key="edit_sku"
                    )

                    referencia_edit = st.text_input(
                        "Referência",
                        key="edit_referencia"
                    )

                    marca_edit = st.text_input(
                        "Marca",
                        key="edit_marca"
                    )

                with col2:

                    categoria_edit = st.text_input(
                        "Categoria",
                        key="edit_categoria"
                    )

                    unidade_edit = st.selectbox(
                        "Unidade",
                        UNIDADES_PRODUTO,
                        key="edit_unidade"
                    )

                    ncm_edit = st.text_input(
                        "NCM",
                        key="edit_ncm"
                    )

                    cest_edit = st.text_input(
                        "CEST",
                        key="edit_cest"
                    )

                    cfop_edit = st.text_input(
                        "CFOP",
                        key="edit_cfop"
                    )

                st.divider()

                col3, col4 = st.columns(2)

                with col3:

                    custo_edit = st.number_input(
                        "Custo",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        key="edit_custo"
                    )

                    preco_edit = st.number_input(
                        "Preço Venda",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        key="edit_preco"
                    )

                with col4:

                    estoque_edit = st.number_input(
                        "Estoque",
                        min_value=0,
                        step=1,
                        key="edit_estoque"
                    )

                    estoque_minimo_edit = st.number_input(
                        "Estoque Mínimo",
                        min_value=0,
                        step=1,
                        key="edit_estoque_minimo"
                    )

                st.divider()

                localizacao_edit = st.text_input(
                    "Localização",
                    key="edit_localizacao"
                )

                observacoes_edit = st.text_area(
                    "Observações",
                    key="edit_observacoes"
                )

                ativo_edit = st.checkbox(
                    "Produto ativo",
                    key="edit_ativo"
                )

                st.divider()

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:

                    salvar_edicao = st.button(
                        "💾 Salvar Alterações",
                        use_container_width=True,
                        key="btn_salvar_edicao"
                    )

                with col_btn2:

                    excluir = st.button(
                        "🗑️ Excluir Produto",
                        use_container_width=True,
                        key="btn_excluir_produto"
                    )

                if salvar_edicao:

                    nome_edit_normalizado = tratar_texto(
                        nome_edit
                    )

                    if not nome_edit_normalizado:

                        st.warning(
                            "Informe o nome do produto."
                        )

                    else:

                        sucesso = atualizar_produto(
                            produto_id,
                            nome_edit_normalizado,
                            float(preco_edit),
                            int(estoque_edit),
                            normalizar_campo(
                                codigo_barras_edit
                            ),
                            normalizar_campo(
                                sku_edit
                            ),
                            normalizar_campo(
                                referencia_edit
                            ),
                            normalizar_campo(
                                marca_edit
                            ),
                            normalizar_campo(
                                categoria_edit
                            ),
                            unidade_edit,
                            normalizar_campo(
                                ncm_edit
                            ),
                            normalizar_campo(
                                cest_edit
                            ),
                            normalizar_campo(
                                cfop_edit
                            ),
                            float(custo_edit),
                            float(
                                buscar_margem_padrao()
                                or 30
                            ),
                            int(
                                estoque_minimo_edit
                            ),
                            normalizar_campo(
                                localizacao_edit
                            ),
                            bool(ativo_edit),
                            normalizar_campo(
                                observacoes_edit
                            )
                        )

                        if sucesso:

                            st.session_state[
                                "edit_produto_carregado_id"
                            ] = None

                            st.session_state[
                                "mensagem_edicao_produto"
                            ] = (
                                "✅ Produto atualizado "
                                "com sucesso!"
                            )

                            st.rerun()

                if excluir:

                    resultado = excluir_produto(
                        produto_id
                    )

                    if resultado == "possui_vendas":

                        st.warning(
                            "Este produto não pode ser "
                            "excluído porque já possui "
                            "vendas vinculadas."
                        )

                    elif resultado is True:

                        limpar_estado_edicao()

                        st.session_state.pop(
                            "editar_select_id",
                            None
                        )

                        st.session_state[
                            "mensagem_edicao_produto"
                        ] = (
                            "🗑️ Produto excluído "
                            "com sucesso!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Não foi possível excluir "
                            "o produto."
                        )

    # =========================================================
    # CÓDIGO DE BARRAS
    # =========================================================

    with abas[3]:

        mensagem_codigo = st.session_state.pop(
            "mensagem_codigo_barras",
            None
        )

        if mensagem_codigo:
            st.success(mensagem_codigo)

        if st.session_state.pop(
            "limpar_codigo_barras_pendente",
            False
        ):
            st.session_state[
                "codigo_barras_rapido"
            ] = ""

        st.subheader(
            "🏷️ Atualizar Código de Barras"
        )

        st.info(
            "Use esta tela para atualizar rapidamente "
            "produtos sem código. No celular, abra o ERP "
            "e use um leitor/teclado de código de barras. "
            "Com leitor físico, clique no campo e leia "
            "o produto."
        )

        codigo_lido = st.text_input(
            "📷 Ler / Digitar Código de Barras",
            key="codigo_barras_rapido",
            placeholder=(
                "Clique aqui e leia o código"
            )
        )

        codigo_normalizado = tratar_texto(
            codigo_lido
        )

        produto_existente = None

        if codigo_normalizado:

            produto_existente = (
                buscar_produto_por_codigo(
                    codigo_normalizado
                )
            )

            if produto_existente:

                st.warning(
                    "Este código já está cadastrado "
                    f"no produto: {produto_existente[1]}"
                )

        df_sem_codigo = listar_produtos_sem_codigo()

        if df_sem_codigo.empty:

            st.success(
                "✅ Todos os produtos já possuem "
                "código de barras."
            )

        else:

            st.markdown(
                "### Produtos sem código"
            )

            produtos_map = {
                f"{row['id']} - {row['nome']}": int(
                    row["id"]
                )
                for _, row in df_sem_codigo.iterrows()
            }

            produto_escolhido = st.selectbox(
                "Selecione o produto",
                list(produtos_map.keys()),
                key="produto_codigo_barras_select"
            )

            produto_id_codigo = produtos_map[
                produto_escolhido
            ]

            df_sem_codigo_exibicao = (
                formatar_dataframe_brasil(
                    df_sem_codigo,
                    com_hora=False,
                    moedas=True
                )
            )

            st.dataframe(
                df_sem_codigo_exibicao,
                use_container_width=True,
                hide_index=True
            )

            salvar_codigo = st.button(
                "💾 Salvar Código neste Produto",
                use_container_width=True,
                key="btn_salvar_codigo_barras"
            )

            if salvar_codigo:

                if not codigo_normalizado:

                    st.warning(
                        "Leia ou digite o código "
                        "de barras."
                    )

                elif produto_existente:

                    st.warning(
                        "Este código já pertence "
                        "a outro produto."
                    )

                else:

                    sucesso = atualizar_codigo_barras(
                        produto_id_codigo,
                        codigo_normalizado
                    )

                    if sucesso:

                        st.session_state[
                            "limpar_codigo_barras_pendente"
                        ] = True

                        st.session_state[
                            "mensagem_codigo_barras"
                        ] = (
                            "✅ Código de barras "
                            "atualizado com sucesso!"
                        )

                        st.rerun()