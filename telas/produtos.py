import pandas as pd
import streamlit as st


from database.modelos_uniforme_db import (
    listar_modelos_uniforme,
    cadastrar_modelo_uniforme
)

from database.produto_db import (
    listar_produtos,
    buscar_produto_por_id,
    listar_produtos_sem_codigo,
    cadastrar_produto,
    atualizar_produto,
    atualizar_codigo_barras,
    excluir_produto,
    buscar_produto_por_codigo,
    gerar_codigo_uniforme,
    verificar_codigo_barras_disponivel
)

from utils.precificacao import (
    calcular_preco_venda,
    buscar_margem_padrao
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)

from services.etiquetas_service import gerar_pdf_etiquetas_produto


UNIDADES_PRODUTO = [
    "UN",
    "KG",
    "CX",
    "PC",
    "LT"
]


# =========================================================
# TRATAMENTO DE TEXTO
# =========================================================
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


def formatar_nome_tamanho(nome, tamanho=None):

    nome = tratar_texto(nome)
    tamanho = tratar_texto(tamanho)

    if tamanho:
        return f"{nome} | Tam. {tamanho}"

    return nome


# =========================================================
# LIMPAR FORMULÁRIO NOVO PRODUTO
# =========================================================
def limpar_formulario_novo_produto():

    valores_iniciais = {
        "novo_nome": "",
        "novo_tamanho": "",
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

    st.session_state.pop(
        "ultimo_codigo_existente_popup",
        None
    )


# =========================================================
# CARREGAR PRODUTO PARA EDIÇÃO
# =========================================================
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

    st.session_state["edit_tamanho"] = tratar_texto(
        produto.get("tamanho")
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

    st.session_state["edit_ativo"] = bool(
        ativo
    )


# =========================================================
# LIMPAR ESTADO DE EDIÇÃO
# =========================================================
def limpar_estado_edicao():

    chaves = [
        "edit_nome",
        "edit_tamanho",
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


# =========================================================
# TELA DE PRODUTOS
# =========================================================
def tela_produtos():

    # =====================================================
    # LIMPEZA PENDENTE DO NOVO PRODUTO
    # =====================================================
    if st.session_state.pop(
        "limpar_novo_produto_pendente",
        False
    ):
        limpar_formulario_novo_produto()

    # =====================================================
    # LIMPEZA PENDENTE DA EDIÇÃO
    # Executada antes da criação dos widgets
    # =====================================================
    if st.session_state.pop(
        "limpar_edicao_produto_pendente",
        False
    ):

        limpar_estado_edicao()

        st.session_state.pop(
            "editar_select_id",
            None
        )

    # =====================================================
    # LIMPEZA PENDENTE DO CÓDIGO DE BARRAS
    # Executada antes da criação dos widgets
    # =====================================================
    if st.session_state.pop(
        "limpar_codigo_barras_pendente",
        False
    ):

        st.session_state[
            "codigo_barras_rapido"
        ] = ""

        st.session_state.pop(
            "produto_codigo_barras_select",
            None
        )

        st.session_state.pop(
            "ultimo_codigo_rapido_popup",
            None
        )

    # =====================================================
    # POPUP - PRODUTO JÁ CADASTRADO
    # =====================================================
    @st.dialog("⚠️ Produto já cadastrado")
    def popup_produto_existente(produto):

        st.warning(
            "Este código de barras já pertence "
            "a um produto cadastrado."
        )

        nome_produto = formatar_nome_tamanho(
            produto.get("nome"),
            produto.get("tamanho")
        )

        codigo_produto = tratar_texto(
            produto.get("codigo_barras")
        )

        preco_produto = float(
            produto.get("preco") or 0
        )

        estoque_produto = int(
            produto.get("estoque") or 0
        )

        st.markdown(
            f"""
### 📦 {nome_produto}

**Código de Barras:** `{codigo_produto}`

**Preço de Venda:** {formatar_moeda(preco_produto)}

**Estoque Atual:** {estoque_produto}
            """
        )

        st.info(
            "Não é necessário cadastrar este produto "
            "novamente. Se precisar alterar algum dado, "
            "utilize a aba ✏️ Editar Produto."
        )

        if st.button(
            "✅ Fechar",
            use_container_width=True,
            key="btn_fechar_produto_existente"
        ):
            st.rerun()

    # =====================================================
    # POPUP - CÓDIGO JÁ CADASTRADO NA ABA RÁPIDA
    # =====================================================
    @st.dialog("⚠️ Código de barras já cadastrado")
    def popup_codigo_existente(produto):

        nome_produto = formatar_nome_tamanho(
            produto.get("nome"),
            produto.get("tamanho")
        )

        codigo_produto = tratar_texto(
            produto.get("codigo_barras")
        )

        st.warning(
            "Este código de barras já está cadastrado."
        )

        st.markdown(
            f"""
**Produto:** {nome_produto}

**Código:** `{codigo_produto}`
            """
        )

        if st.button(
            "✅ Fechar",
            use_container_width=True,
            key="btn_fechar_codigo_existente"
        ):
            st.rerun()

    # =====================================================
    # ABAS
    # =====================================================
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

            st.success(
                mensagem_novo
            )

        st.subheader(
            "📦 Cadastro de Produto"
        )

        # =====================================================
        # VERIFICAÇÃO PRÉVIA DO CÓDIGO DE BARRAS
        # =====================================================
        st.markdown(
            "### 🔎 Verificar Produto"
        )

        st.info(
            "Antes de cadastrar, clique no campo abaixo "
            "e faça a leitura do código de barras. "
            "O sistema verificará automaticamente se o "
            "produto já está cadastrado."
        )

        codigo_barras = st.text_input(
            "📷 Ler / Digitar Código de Barras",
            key="novo_codigo_barras",
            placeholder=(
                "Clique aqui e leia o código "
                "com o leitor"
            )
        )

        codigo_verificacao = tratar_texto(
            codigo_barras
        )

        produto_codigo_existente = None

        if codigo_verificacao:

            produto_codigo_existente = (
                buscar_produto_por_codigo(
                    codigo_verificacao
                )
            )

            if produto_codigo_existente:

                st.error(
                    "⚠️ Este código já está cadastrado no "
                    f"produto: "
                    f"{produto_codigo_existente['nome']}"
                )

                ultimo_codigo_popup = (
                    st.session_state.get(
                        "ultimo_codigo_existente_popup"
                    )
                )

                if (
                    ultimo_codigo_popup
                    != codigo_verificacao
                ):

                    st.session_state[
                        "ultimo_codigo_existente_popup"
                    ] = codigo_verificacao

                    popup_produto_existente(
                        produto_codigo_existente
                    )

            else:

                st.success(
                    "✅ Código não encontrado. "
                    "Pode continuar o cadastro "
                    "do novo produto."
                )

                st.session_state.pop(
                    "ultimo_codigo_existente_popup",
                    None
                )

        st.divider()

        st.markdown(
            "## 📦 Dados Básicos"
        )

        col1, col2 = st.columns(2)

        with col1:

            nome = st.text_input(
                "Nome do Produto",
                key="novo_nome"
            )

            tamanho = st.text_input(
                "Tamanho",
                key="novo_tamanho",
                placeholder=(
                    "Ex.: 6, 10, P, M, G, EG..."
                )
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

        # =====================================================
        # FINANCEIRO
        # =====================================================
        st.divider()

        st.markdown(
            "## 💰 Financeiro"
        )

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
                buscar_margem_padrao()
                or 30
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

        if (
            "novo_preco"
            not in st.session_state
        ):

            st.session_state[
                "novo_preco"
            ] = float(
                preco_automatico
            )

        lucro_estimado = round(
            float(
                st.session_state[
                    "novo_preco"
                ]
            )
            -
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

        # =====================================================
        # ESTOQUE
        # =====================================================
        st.divider()

        st.markdown(
            "## 📦 Estoque"
        )

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
            key="novo_ativo"
        )

        st.divider()

        salvar_novo = st.button(
            "💾 Salvar Produto",
            use_container_width=True,
            key="btn_salvar_produto"
        )

        # =====================================================
        # SALVAR NOVO PRODUTO
        # =====================================================
        if salvar_novo:

            nome_normalizado = tratar_texto(
                nome
            )

            if produto_codigo_existente:

                st.error(
                    "⚠️ Não é possível cadastrar. "
                    "Este código de barras já pertence "
                    f"ao produto: "
                    f"{produto_codigo_existente['nome']}."
                )

            elif not nome_normalizado:

                st.warning(
                    "Informe o nome do produto."
                )

            else:

                sucesso = cadastrar_produto(
                    nome=nome_normalizado,
                    tamanho=normalizar_campo(
                        tamanho
                    ),
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
                    ativo=bool(
                        ativo
                    ),
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

        st.subheader(
            "📋 Produtos"
        )

        busca = st.text_input(
            "🔎 Buscar produto",
            key="buscar_produto",
            placeholder=(
                "Digite parte do nome do produto..."
            )
        )

        df_produtos = listar_produtos()

        if df_produtos.empty:

            st.info(
                "Nenhum produto cadastrado."
            )

        else:

            df_produtos = (
                df_produtos.fillna("")
            )

            if busca:

                busca_normalizada = str(busca).strip()

                mascara_busca = (
                    df_produtos["nome"]
                    .astype(str)
                    .str.contains(
                        busca_normalizada,
                        case=False,
                        na=False
                    )
                )

                if "tamanho" in df_produtos.columns:
                    mascara_busca = (
                        mascara_busca
                        | df_produtos["tamanho"]
                        .astype(str)
                        .str.contains(
                            busca_normalizada,
                            case=False,
                            na=False
                        )
                    )

                if "codigo_barras" in df_produtos.columns:
                    mascara_busca = (
                        mascara_busca
                        | df_produtos["codigo_barras"]
                        .astype(str)
                        .str.contains(
                            busca_normalizada,
                            case=False,
                            na=False
                        )
                    )

                df_produtos = df_produtos[mascara_busca]

            df_exibicao = (
                formatar_dataframe_brasil(
                    df_produtos,
                    com_hora=False,
                    moedas=True
                )
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

        mensagem_edicao = (
            st.session_state.pop(
                "mensagem_edicao_produto",
                None
            )
        )

        if mensagem_edicao:

            st.success(
                mensagem_edicao
            )

        st.subheader(
            "✏️ Editar Produto"
        )

        st.info(
            "🔎 Digite o nome ou o código do produto "
            "no campo abaixo e selecione o registro correto."
        )

        df_edicao = listar_produtos()

        if df_edicao.empty:

            st.info(
                "Sem produtos cadastrados."
            )

        else:

            produtos_resumo = {
                int(row["id"]): {
                    "nome": tratar_texto(
                        row["nome"]
                    ),
                    "tamanho": tratar_texto(
                        row.get("tamanho")
                    ),
                    "codigo": tratar_texto(
                        row.get("codigo_barras")
                    )
                }
                for _, row
                in df_edicao.iterrows()
            }

            ids_produtos = list(
                produtos_resumo.keys()
            )

            produto_id = st.selectbox(
                "🔎 Procurar produto",
                options=ids_produtos,
                index=None,
                placeholder=(
                    "Digite o nome, código ou ID..."
                ),
                format_func=(
                    lambda identificador: (
                        f"{identificador} - "
                        f"{produtos_resumo[identificador]['nome']}"
                        +
                        (
                            f" | Tam. "
                            f"{produtos_resumo[identificador]['tamanho']}"
                            if produtos_resumo[
                                identificador
                            ]["tamanho"]
                            else ""
                        )
                        +
                        (
                            f" | Cód. "
                            f"{produtos_resumo[identificador]['codigo']}"
                            if produtos_resumo[
                                identificador
                            ]["codigo"]
                            else ""
                        )
                    )
                ),
                key="editar_select_id"
            )

            # =================================================
            # NENHUM PRODUTO SELECIONADO
            # =================================================
            if produto_id is None:

                limpar_estado_edicao()

                st.info(
                    "Selecione um produto acima "
                    "para visualizar e editar seus dados."
                )

            else:

                produto_carregado_id = (
                    st.session_state.get(
                        "edit_produto_carregado_id"
                    )
                )

                if (
                    produto_carregado_id
                    != produto_id
                ):

                    # Remove dados do produto anterior
                    # antes de carregar o novo
                    limpar_estado_edicao()

                    produto_para_carregar = (
                        buscar_produto_por_id(
                            produto_id
                        )
                    )

                    if (
                        produto_para_carregar
                        is not None
                    ):

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

                    st.caption(
                        f"Editando produto ID {produto_id}: "
                        f"{formatar_nome_tamanho(
                            produto.get('nome'),
                            produto.get('tamanho')
                        )}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        nome_edit = st.text_input(
                            "Nome",
                            key="edit_nome"
                        )

                        tamanho_edit = st.text_input(
                            "Tamanho",
                            key="edit_tamanho",
                            placeholder=(
                                "Ex.: 6, 10, P, M, G, EG..."
                            )
                        )

                        codigo_barras_edit = (
                            st.text_input(
                                "Código de Barras",
                                key="edit_codigo"
                            )
                        )

                        sku_edit = st.text_input(
                            "SKU",
                            key="edit_sku"
                        )

                        referencia_edit = (
                            st.text_input(
                                "Referência",
                                key="edit_referencia"
                            )
                        )

                        marca_edit = st.text_input(
                            "Marca",
                            key="edit_marca"
                        )

                    with col2:

                        categoria_edit = (
                            st.text_input(
                                "Categoria",
                                key="edit_categoria"
                            )
                        )

                        unidade_edit = (
                            st.selectbox(
                                "Unidade",
                                UNIDADES_PRODUTO,
                                key="edit_unidade"
                            )
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

                        custo_edit = (
                            st.number_input(
                                "Custo",
                                min_value=0.0,
                                step=0.01,
                                format="%.2f",
                                key="edit_custo"
                            )
                        )

                        preco_edit = (
                            st.number_input(
                                "Preço Venda",
                                min_value=0.0,
                                step=0.01,
                                format="%.2f",
                                key="edit_preco"
                            )
                        )

                    with col4:

                        estoque_edit = (
                            st.number_input(
                                "Estoque",
                                min_value=0,
                                step=1,
                                key="edit_estoque"
                            )
                        )

                        estoque_minimo_edit = (
                            st.number_input(
                                "Estoque Mínimo",
                                min_value=0,
                                step=1,
                                key="edit_estoque_minimo"
                            )
                        )

                    st.divider()

                    localizacao_edit = (
                        st.text_input(
                            "Localização",
                            key="edit_localizacao"
                        )
                    )

                    observacoes_edit = (
                        st.text_area(
                            "Observações",
                            key="edit_observacoes"
                        )
                    )

                    ativo_edit = st.checkbox(
                        "Produto ativo",
                        key="edit_ativo"
                    )

                    st.divider()

                    col_btn1, col_btn2 = (
                        st.columns(2)
                    )

                    with col_btn1:

                        salvar_edicao = (
                            st.button(
                                "💾 Salvar Alterações",
                                use_container_width=True,
                                key="btn_salvar_edicao"
                            )
                        )

                    with col_btn2:

                        excluir = st.button(
                            "🗑️ Excluir Produto",
                            use_container_width=True,
                            key="btn_excluir_produto"
                        )

                    # =================================================
                    # SALVAR EDIÇÃO
                    # =================================================
                    if salvar_edicao:

                        nome_edit_normalizado = (
                            tratar_texto(
                                nome_edit
                            )
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
                                bool(
                                    ativo_edit
                                ),
                                normalizar_campo(
                                    observacoes_edit
                                ),
                                normalizar_campo(
                                    tamanho_edit
                                )
                            )

                            if sucesso:

                                st.session_state[
                                    "limpar_edicao_produto_pendente"
                                ] = True

                                st.session_state[
                                    "mensagem_edicao_produto"
                                ] = (
                                    "✅ Produto atualizado "
                                    "com sucesso!"
                                )

                                st.rerun()

                    # =================================================
                    # EXCLUIR
                    # =================================================
                    if excluir:

                        resultado = excluir_produto(
                            produto_id
                        )

                        if (
                            resultado
                            == "possui_vendas"
                        ):

                            st.warning(
                                "Este produto não pode ser "
                                "excluído porque já possui "
                                "vendas vinculadas."
                            )

                        elif resultado is True:

                            st.session_state[
                                "limpar_edicao_produto_pendente"
                            ] = True

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

        mensagem_codigo = (
            st.session_state.pop(
                "mensagem_codigo_barras",
                None
            )
        )

        if mensagem_codigo:

            st.success(
                mensagem_codigo
            )

        st.subheader(
            "🏷️ Atualizar Código de Barras"
        )

        st.info(
            "Use esta tela para atualizar rapidamente "
            "produtos sem código. Com o leitor físico, "
            "localize o produto, clique no campo de "
            "código e faça a leitura."
        )

        # =====================================================
        # GERADOR DE CÓDIGO INTERNO PARA UNIFORMES
        # =====================================================
        st.markdown(
            "### 👕 Gerar código para uniforme"
        )

        st.caption(
            "Padrão: 26 + escola + modelo + tamanho. "
            "Exemplo: 26 + 01 + 001 + 08 = 260100108."
        )

        escolas_uniforme = {
            "01 - Colégio dos Santos Anjos": 1,
        }

        # Modelos carregados do banco de dados
        modelos_uniforme_db = listar_modelos_uniforme()

        modelos_uniforme = {
            (
                f"{int(modelo['codigo']):03d} - "
                f"{tratar_texto(modelo['nome'])}"
            ): int(modelo["codigo"])
            for modelo in modelos_uniforme_db
        }

        tamanhos_uniforme = [
            "2",
            "4",
            "6",
            "8",
            "10",
            "12",
            "14",
            "16",
            "P",
            "M",
            "G",
            "GG",
            "EG",
            "EXG",
        ]

        (
            col_uniforme_1,
            col_uniforme_2,
            col_uniforme_3
        ) = st.columns(3)

        with col_uniforme_1:

            escola_uniforme_label = st.selectbox(
                "Escola",
                options=list(
                    escolas_uniforme.keys()
                ),
                index=None,
                placeholder="Selecione a escola...",
                key="uniforme_escola"
            )

        with col_uniforme_2:

            if modelos_uniforme:

                modelo_uniforme_label = st.selectbox(
                    "Modelo",
                    options=list(
                        modelos_uniforme.keys()
                    ),
                    index=None,
                    placeholder="Selecione o modelo...",
                    key="uniforme_modelo"
                )

            else:

                modelo_uniforme_label = None

                st.warning(
                    "Nenhum modelo de uniforme cadastrado."
                )

        with col_uniforme_3:

            tamanho_uniforme = st.selectbox(
                "Tamanho",
                options=tamanhos_uniforme,
                index=None,
                placeholder="Selecione o tamanho...",
                key="uniforme_tamanho"
            )

        # =====================================================
        # CADASTRAR NOVO MODELO DE UNIFORME
        # =====================================================
        with st.expander(
            "➕ Cadastrar novo modelo de uniforme"
        ):

            novo_modelo_uniforme = st.text_input(
                "Nome do modelo",
                placeholder=(
                    "Ex.: Jaqueta, Saia, "
                    "Camiseta Polo..."
                ),
                key="novo_modelo_uniforme"
            )

            cadastrar_novo_modelo = st.button(
                "💾 Cadastrar modelo",
                use_container_width=True,
                key="btn_cadastrar_modelo_uniforme"
            )

            if cadastrar_novo_modelo:

                nome_novo_modelo = tratar_texto(
                    novo_modelo_uniforme
                )

                if not nome_novo_modelo:

                    st.warning(
                        "Informe o nome do modelo."
                    )

                else:

                    sucesso_modelo = (
                        cadastrar_modelo_uniforme(
                            nome_novo_modelo
                        )
                    )

                    if sucesso_modelo:

                        st.session_state.pop(
                            "uniforme_modelo",
                            None
                        )

                        st.session_state.pop(
                            "novo_modelo_uniforme",
                            None
                        )

                        st.success(
                            "✅ Modelo cadastrado com sucesso!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Não foi possível cadastrar "
                            "o modelo. Verifique se ele "
                            "já existe."
                        )

        codigo_uniforme_gerado = None

        if (
            escola_uniforme_label
            and
            modelo_uniforme_label
            and
            tamanho_uniforme
        ):

            codigo_uniforme_gerado = gerar_codigo_uniforme(
                codigo_escola=(
                    escolas_uniforme[
                        escola_uniforme_label
                    ]
                ),
                codigo_modelo=(
                    modelos_uniforme[
                        modelo_uniforme_label
                    ]
                ),
                tamanho=tamanho_uniforme
            )

        if codigo_uniforme_gerado:

            st.code(
                codigo_uniforme_gerado,
                language=None
            )

            verificacao_uniforme = (
                verificar_codigo_barras_disponivel(
                    codigo_uniforme_gerado
                )
            )

            if (
                verificacao_uniforme
                and
                verificacao_uniforme["disponivel"]
            ):

                st.success(
                    f"✅ Código "
                    f"{codigo_uniforme_gerado} "
                    f"disponível."
                )

                if st.button(
                    "👕 Usar código gerado",
                    use_container_width=True,
                    key="btn_usar_codigo_uniforme"
                ):

                    st.session_state[
                        "codigo_barras_rapido"
                    ] = codigo_uniforme_gerado

                    st.session_state.pop(
                        "ultimo_codigo_rapido_popup",
                        None
                    )

                    st.rerun()

            elif verificacao_uniforme:

                st.warning(
                    "⚠️ Este código já está cadastrado "
                    "no produto: "
                    f"{verificacao_uniforme['produto_nome']}"
                )

        st.divider()

        st.markdown(
            "### 📷 Ler ou digitar código"
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
                    "⚠️ Este código já está cadastrado "
                    f"no produto: "
                    f"{produto_existente['nome']}"
                )

                ultimo_codigo_rapido = (
                    st.session_state.get(
                        "ultimo_codigo_rapido_popup"
                    )
                )

                if (
                    ultimo_codigo_rapido
                    != codigo_normalizado
                ):

                    st.session_state[
                        "ultimo_codigo_rapido_popup"
                    ] = codigo_normalizado

                    popup_codigo_existente(
                        produto_existente
                    )

            else:

                st.session_state.pop(
                    "ultimo_codigo_rapido_popup",
                    None
                )

        df_sem_codigo = (
            listar_produtos_sem_codigo()
        )

        if df_sem_codigo.empty:

            st.success(
                "✅ Todos os produtos já possuem "
                "código de barras."
            )

        else:

            st.markdown(
                "### 🔎 Localizar produto sem código"
            )

            st.caption(
                "Digite parte do nome do produto "
                "e selecione o registro correto."
            )

            produtos_map = {
                (
                    f"{int(row['id'])} - "
                    f"{formatar_nome_tamanho(
                        row['nome'],
                        row.get('tamanho')
                    )}"
                ): int(row["id"])
                for _, row
                in df_sem_codigo.iterrows()
            }

            produto_escolhido = (
                st.selectbox(
                    "Produto",
                    options=list(
                        produtos_map.keys()
                    ),
                    index=None,
                    placeholder=(
                        "Digite o nome do produto..."
                    ),
                    key=(
                        "produto_codigo_barras_select"
                    )
                )
            )

            produto_id_codigo = None

            if produto_escolhido is not None:

                produto_id_codigo = (
                    produtos_map[
                        produto_escolhido
                    ]
                )

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

            if produto_escolhido is None:

                st.info(
                    "Selecione o produto que receberá "
                    "o código de barras."
                )

            salvar_codigo = st.button(
                "💾 Salvar Código neste Produto",
                use_container_width=True,
                key="btn_salvar_codigo_barras",
                disabled=(
                    produto_escolhido is None
                )
            )

            if salvar_codigo:

                if produto_id_codigo is None:

                    st.warning(
                        "Selecione o produto."
                    )

                elif not codigo_normalizado:

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

                    sucesso = (
                        atualizar_codigo_barras(
                            produto_id_codigo,
                            codigo_normalizado
                        )
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

        # =========================================================
        # GERADOR DE ETIQUETAS
        # =========================================================
        st.divider()

        st.markdown(
            "### 🖨️ Gerar Etiquetas"
        )

        st.info(
            "Digite o nome do produto que já possua "
            "código de barras. O sistema gera um PDF A4 "
            "com etiquetas de 50 x 30 mm em padrão Code 128."
        )

        df_etiquetas = listar_produtos()

        if df_etiquetas.empty:

            st.info(
                "Nenhum produto cadastrado "
                "para gerar etiquetas."
            )

        else:

            df_etiquetas = (
                df_etiquetas.fillna("")
            )

            df_etiquetas = df_etiquetas[
                df_etiquetas["codigo_barras"]
                .astype(str)
                .str.strip()
                .ne("")
            ]

            if df_etiquetas.empty:

                st.info(
                    "Nenhum produto com código de barras "
                    "disponível para gerar etiquetas."
                )

            else:

                produtos_etiqueta_map = {
                    (
                        f"{int(row['id'])} - "
                        f"{formatar_nome_tamanho(
                            row['nome'],
                            row.get('tamanho')
                        )} "
                        f"| Cód. "
                        f"{tratar_texto(row['codigo_barras'])}"
                    ): int(row["id"])
                    for _, row
                    in df_etiquetas.iterrows()
                }

                produto_etiqueta_label = (
                    st.selectbox(
                        "🔎 Produto para etiqueta",
                        options=list(
                            produtos_etiqueta_map.keys()
                        ),
                        index=None,
                        placeholder=(
                            "Digite o nome ou código "
                            "do produto..."
                        ),
                        key="produto_etiqueta_select"
                    )
                )

                if produto_etiqueta_label is None:

                    st.info(
                        "Selecione um produto para "
                        "preparar as etiquetas."
                    )

                else:

                    produto_etiqueta_id = (
                        produtos_etiqueta_map[
                            produto_etiqueta_label
                        ]
                    )

                    produto_etiqueta = (
                        buscar_produto_por_id(
                            produto_etiqueta_id
                        )
                    )

                    if produto_etiqueta is not None:

                        nome_etiqueta = formatar_nome_tamanho(
                            produto_etiqueta.get(
                                "nome"
                            ),
                            produto_etiqueta.get(
                                "tamanho"
                            )
                        )

                        codigo_etiqueta = tratar_texto(
                            produto_etiqueta.get(
                                "codigo_barras"
                            )
                        )

                        preco_etiqueta = float(
                            produto_etiqueta.get(
                                "preco"
                            )
                            or 0
                        )

                        col_etq1, col_etq2 = (
                            st.columns(2)
                        )

                        with col_etq1:

                            quantidade_etiquetas = (
                                st.number_input(
                                    "Quantidade de etiquetas",
                                    min_value=1,
                                    max_value=500,
                                    value=1,
                                    step=1,
                                    key="quantidade_etiquetas"
                                )
                            )

                        with col_etq2:

                            mostrar_preco_etiqueta = (
                                st.checkbox(
                                    "Mostrar preço na etiqueta",
                                    value=True,
                                    key=(
                                        "mostrar_preco_etiqueta"
                                    )
                                )
                            )

                        st.markdown(
                            f"""
**Produto:** {nome_etiqueta}  
**Código:** `{codigo_etiqueta}`  
**Preço:** {formatar_moeda(preco_etiqueta)}
                            """
                        )

                        if st.button(
                            "📄 Preparar PDF de Etiquetas",
                            use_container_width=True,
                            key="btn_preparar_pdf_etiquetas"
                        ):

                            try:

                                pdf_etiquetas = (
                                    gerar_pdf_etiquetas_produto(
                                        nome_produto=(
                                            nome_etiqueta
                                        ),
                                        codigo_barras=(
                                            codigo_etiqueta
                                        ),
                                        preco=(
                                            preco_etiqueta
                                        ),
                                        quantidade=int(
                                            quantidade_etiquetas
                                        ),
                                        mostrar_preco=bool(
                                            mostrar_preco_etiqueta
                                        )
                                    )
                                )

                                st.session_state[
                                    "pdf_etiquetas_gerado"
                                ] = pdf_etiquetas

                                st.session_state[
                                    "pdf_etiquetas_nome"
                                ] = (
                                    f"etiquetas_"
                                    f"{produto_etiqueta_id}_"
                                    f"{codigo_etiqueta}.pdf"
                                )

                                st.success(
                                    "✅ PDF de etiquetas "
                                    "preparado."
                                )

                            except Exception as erro:

                                st.error(
                                    "Erro ao gerar etiquetas: "
                                    f"{erro}"
                                )

                        pdf_etiquetas_gerado = (
                            st.session_state.get(
                                "pdf_etiquetas_gerado"
                            )
                        )

                        pdf_etiquetas_nome = (
                            st.session_state.get(
                                "pdf_etiquetas_nome",
                                "etiquetas.pdf"
                            )
                        )

                        if pdf_etiquetas_gerado:

                            st.download_button(
                                "⬇️ Baixar PDF para impressão",
                                data=pdf_etiquetas_gerado,
                                file_name=(
                                    pdf_etiquetas_nome
                                ),
                                mime="application/pdf",
                                use_container_width=True,
                                key="btn_baixar_pdf_etiquetas"
                            )