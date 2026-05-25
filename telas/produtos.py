import streamlit as st
import pandas as pd

from database.produto_db import (
    listar_produtos,
    cadastrar_produto,
    atualizar_produto,
    excluir_produto
)

from utils.precificacao import (
    calcular_preco_venda,
    buscar_margem_padrao
)


# ==================================================
# TRATAMENTO DE VALORES NULOS
# ==================================================
def tratar_texto(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


# ==================================================
# NORMALIZAR CAMPOS
# ==================================================
def normalizar_campo(valor):

    valor = tratar_texto(valor)

    if valor == "":
        return None

    return valor


# ==================================================
# TELA PRODUTOS
# ==================================================
def tela_produtos():

    abas = st.tabs([
        "➕ Novo Produto",
        "📋 Produtos",
        "✏️ Editar Produto"
    ])

    # ==================================================
    # NOVO PRODUTO
    # ==================================================
    with abas[0]:

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
                ["UN", "KG", "CX", "PC", "LT"],
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

        # ==================================================
        # FINANCEIRO
        # ==================================================
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
                value=float(margem_padrao),
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

        lucro_estimado = round(
            preco_automatico - custo,
            2
        )

        with col5:

            st.info(
                "💡 Preço calculado automaticamente."
            )

            preco = st.number_input(
                "Preço Venda",
                value=float(preco_automatico),
                min_value=0.0,
                step=0.01,
                format="%.2f",
                key="novo_preco"
            )

            st.metric(
                "Preço Automático",
                f"R$ {preco_automatico:,.2f}"
            )

            st.metric(
                "Lucro Estimado",
                f"R$ {lucro_estimado:,.2f}"
            )

        st.divider()

        # ==================================================
        # ESTOQUE
        # ==================================================
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

        # ==================================================
        # SALVAR PRODUTO
        # ==================================================
        if st.button(
            "💾 Salvar Produto",
            use_container_width=True,
            key="btn_salvar_produto"
        ):

            if not nome.strip():

                st.warning(
                    "Informe o nome do produto."
                )

            else:

                codigo_barras = normalizar_campo(codigo_barras)
                sku = normalizar_campo(sku)
                referencia = normalizar_campo(referencia)
                marca = normalizar_campo(marca)
                categoria = normalizar_campo(categoria)
                ncm = normalizar_campo(ncm)
                cest = normalizar_campo(cest)
                cfop_padrao = normalizar_campo(cfop_padrao)
                localizacao = normalizar_campo(localizacao)
                observacoes = normalizar_campo(observacoes)

                cadastrar_produto(
                    nome=nome.strip(),
                    preco=preco,
                    estoque=estoque,
                    codigo_barras=codigo_barras,
                    sku=sku,
                    referencia=referencia,
                    marca=marca,
                    categoria=categoria,
                    unidade=unidade,
                    ncm=ncm,
                    cest=cest,
                    cfop_padrao=cfop_padrao,
                    custo=custo,
                    margem_lucro=margem_padrao,
                    estoque_minimo=estoque_minimo,
                    localizacao=localizacao,
                    ativo=ativo,
                    observacoes=observacoes
                )

                st.success(
                    "✅ Produto cadastrado com sucesso!"
                )

                st.rerun()

    # ==================================================
    # LISTAGEM
    # ==================================================
    with abas[1]:

        st.subheader("📋 Produtos")

        busca = st.text_input(
            "🔎 Buscar produto",
            key="buscar_produto"
        )

        df = listar_produtos()

        if df.empty:

            st.info(
                "Nenhum produto cadastrado."
            )

        else:

            df = df.fillna("")

            if busca:

                df = df[
                    df["nome"].astype(str).str.contains(
                        busca,
                        case=False,
                        na=False
                    )
                ]

            st.dataframe(
                df,
                use_container_width=True,
                height=500
            )

    # ==================================================
    # EDITAR PRODUTO
    # ==================================================
    with abas[2]:

        st.subheader("✏️ Editar Produto")

        df = listar_produtos()

        if df.empty:

            st.info(
                "Sem produtos cadastrados."
            )

        else:

            produtos = {
                f"{row['id']} - {row['nome']}": row
                for _, row in df.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione o Produto",
                list(produtos.keys()),
                key="editar_select"
            )

            produto = produtos[selecionado]

            st.divider()

            col1, col2 = st.columns(2)

            with col1:

                nome_edit = st.text_input(
                    "Nome",
                    value=tratar_texto(
                        produto.get("nome", "")
                    ),
                    key="edit_nome"
                )

                codigo_barras_edit = st.text_input(
                    "Código de Barras",
                    value=tratar_texto(
                        produto.get("codigo_barras", "")
                    ),
                    key="edit_codigo"
                )

                sku_edit = st.text_input(
                    "SKU",
                    value=tratar_texto(
                        produto.get("sku", "")
                    ),
                    key="edit_sku"
                )

                referencia_edit = st.text_input(
                    "Referência",
                    value=tratar_texto(
                        produto.get("referencia", "")
                    ),
                    key="edit_referencia"
                )

                marca_edit = st.text_input(
                    "Marca",
                    value=tratar_texto(
                        produto.get("marca", "")
                    ),
                    key="edit_marca"
                )

            with col2:

                categoria_edit = st.text_input(
                    "Categoria",
                    value=tratar_texto(
                        produto.get("categoria", "")
                    ),
                    key="edit_categoria"
                )

                lista_unidades = [
                    "UN",
                    "KG",
                    "CX",
                    "PC",
                    "LT"
                ]

                unidade_atual = tratar_texto(
                    produto.get("unidade", "UN")
                )

                if unidade_atual not in lista_unidades:
                    unidade_atual = "UN"

                unidade_edit = st.selectbox(
                    "Unidade",
                    lista_unidades,
                    index=lista_unidades.index(
                        unidade_atual
                    ),
                    key="edit_unidade"
                )

                ncm_edit = st.text_input(
                    "NCM",
                    value=tratar_texto(
                        produto.get("ncm", "")
                    ),
                    key="edit_ncm"
                )

                cest_edit = st.text_input(
                    "CEST",
                    value=tratar_texto(
                        produto.get("cest", "")
                    ),
                    key="edit_cest"
                )

                cfop_edit = st.text_input(
                    "CFOP",
                    value=tratar_texto(
                        produto.get("cfop_padrao", "")
                    ),
                    key="edit_cfop"
                )

            st.divider()

            col3, col4 = st.columns(2)

            with col3:

                custo_edit = st.number_input(
                    "Custo",
                    value=float(
                        produto.get("custo", 0) or 0
                    ),
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="edit_custo"
                )

                preco_edit = st.number_input(
                    "Preço Venda",
                    value=float(
                        produto.get("preco", 0) or 0
                    ),
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="edit_preco"
                )

            with col4:

                estoque_edit = st.number_input(
                    "Estoque",
                    value=int(
                        produto.get("estoque", 0) or 0
                    ),
                    min_value=0,
                    step=1,
                    key="edit_estoque"
                )

                estoque_minimo_edit = st.number_input(
                    "Estoque Mínimo",
                    value=int(
                        produto.get(
                            "estoque_minimo",
                            0
                        ) or 0
                    ),
                    min_value=0,
                    step=1,
                    key="edit_estoque_minimo"
                )

            st.divider()

            localizacao_edit = st.text_input(
                "Localização",
                value=tratar_texto(
                    produto.get(
                        "localizacao",
                        ""
                    )
                ),
                key="edit_localizacao"
            )

            observacoes_edit = st.text_area(
                "Observações",
                value=tratar_texto(
                    produto.get(
                        "observacoes",
                        ""
                    )
                ),
                key="edit_observacoes"
            )

            ativo_edit = st.checkbox(
                "Produto ativo",
                value=bool(
                    produto.get(
                        "ativo",
                        True
                    )
                ),
                key="edit_ativo"
            )

            st.divider()

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:

                salvar = st.button(
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

            # ==================================================
            # SALVAR
            # ==================================================
            if salvar:

                codigo_barras_edit = normalizar_campo(codigo_barras_edit)
                sku_edit = normalizar_campo(sku_edit)
                referencia_edit = normalizar_campo(referencia_edit)
                marca_edit = normalizar_campo(marca_edit)
                categoria_edit = normalizar_campo(categoria_edit)
                ncm_edit = normalizar_campo(ncm_edit)
                cest_edit = normalizar_campo(cest_edit)
                cfop_edit = normalizar_campo(cfop_edit)
                localizacao_edit = normalizar_campo(localizacao_edit)
                observacoes_edit = normalizar_campo(observacoes_edit)

                atualizar_produto(
                    produto["id"],
                    nome_edit.strip(),
                    preco_edit,
                    estoque_edit,
                    codigo_barras_edit,
                    sku_edit,
                    referencia_edit,
                    marca_edit,
                    categoria_edit,
                    unidade_edit,
                    ncm_edit,
                    cest_edit,
                    cfop_edit,
                    custo_edit,
                    buscar_margem_padrao(),
                    estoque_minimo_edit,
                    localizacao_edit,
                    ativo_edit,
                    observacoes_edit
                )

                st.success(
                    "✅ Produto atualizado com sucesso!"
                )

                st.rerun()

            # ==================================================
            # EXCLUIR
            # ==================================================
            if excluir:

                excluir_produto(
                    produto["id"]
                )

                st.success(
                    "🗑️ Produto excluído com sucesso!"
                )

                st.rerun()