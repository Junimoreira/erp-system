# telas/produtos.py

import streamlit as st
import pandas as pd

from database.produto_db import (
    listar_produtos,
    cadastrar_produto,
    atualizar_produto,
    excluir_produto
)


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

        st.subheader("📦 Cadastrar Produto")

        with st.form("form_produto"):

            # ==========================================
            # BÁSICO
            # ==========================================
            st.markdown("### 📦 Dados Básicos")

            col1, col2 = st.columns(2)

            with col1:

                nome = st.text_input(
                    "Nome do Produto"
                )

                codigo_barras = st.text_input(
                    "Código de Barras"
                )

                sku = st.text_input(
                    "SKU"
                )

                referencia = st.text_input(
                    "Referência"
                )

                marca = st.text_input(
                    "Marca"
                )

            with col2:

                categoria = st.text_input(
                    "Categoria"
                )

                unidade = st.selectbox(
                    "Unidade",
                    ["UN", "KG", "CX", "PC", "LT"]
                )

                ncm = st.text_input(
                    "NCM"
                )

                cest = st.text_input(
                    "CEST"
                )

                cfop_padrao = st.text_input(
                    "CFOP Padrão"
                )

            st.divider()

            # ==========================================
            # FINANCEIRO
            # ==========================================
            st.markdown("### 💰 Financeiro")

            col3, col4, col5 = st.columns(3)

            with col3:

                custo = st.number_input(
                    "Custo",
                    min_value=0.0,
                    format="%.2f"
                )

            with col4:

                preco = st.number_input(
                    "Preço Venda",
                    min_value=0.0,
                    format="%.2f"
                )

            with col5:

                margem_lucro = st.number_input(
                    "Margem Lucro %",
                    min_value=0.0,
                    format="%.2f"
                )

            st.divider()

            # ==========================================
            # ESTOQUE
            # ==========================================
            st.markdown("### 📦 Estoque")

            col6, col7 = st.columns(2)

            with col6:

                estoque = st.number_input(
                    "Estoque Atual",
                    min_value=0.0,
                    format="%.3f"
                )

            with col7:

                estoque_minimo = st.number_input(
                    "Estoque Mínimo",
                    min_value=0.0,
                    format="%.3f"
                )

            localizacao = st.text_input(
                "Localização"
            )

            st.divider()

            # ==========================================
            # OBSERVAÇÕES
            # ==========================================
            observacoes = st.text_area(
                "Observações"
            )

            ativo = st.checkbox(
                "Produto Ativo",
                value=True
            )

            salvar = st.form_submit_button(
                "💾 Cadastrar Produto"
            )

            # ==========================================
            # SALVAR
            # ==========================================
            if salvar:

                if nome.strip() == "":

                    st.warning(
                        "Informe o nome do produto."
                    )

                else:

                    cadastrar_produto(

                        nome=nome,
                        preco=preco,
                        estoque=estoque,
                        codigo_barras=codigo_barras if codigo_barras else None,

                        sku=sku,
                        referencia=referencia,
                        marca=marca,
                        categoria=categoria,

                        unidade=unidade,
                        ncm=ncm,
                        cest=cest,
                        cfop_padrao=cfop_padrao,

                        custo=custo,
                        margem_lucro=margem_lucro,

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

        st.subheader("📋 Produtos Cadastrados")

        df = listar_produtos()

        if df.empty:

            st.info(
                "Nenhum produto cadastrado."
            )

        else:

            st.dataframe(
                df,
                use_container_width=True
            )

    # ==================================================
    # EDITAR / EXCLUIR PRODUTO
    # ==================================================
    with abas[2]:

        st.subheader("✏️ Editar Produto")

        df = listar_produtos()

        if df.empty:

            st.info(
                "Nenhum produto cadastrado."
            )

        else:

            produtos = {
                f"{row['id']} - {row['nome']}": row
                for _, row in df.iterrows()
            }

            produto_selecionado = st.selectbox(
                "Selecione o Produto",
                list(produtos.keys())
            )

            produto = produtos[produto_selecionado]

            # ==========================================
            # BÁSICO
            # ==========================================
            st.markdown("### 📦 Dados Básicos")

            col1, col2 = st.columns(2)

            with col1:

                novo_nome = st.text_input(
                    "Nome",
                    value=produto["nome"]
                )

                novo_codigo_barras = st.text_input(
                    "Código de Barras",
                    value=produto["codigo_barras"] if produto["codigo_barras"] else ""
                )

                novo_sku = st.text_input(
                    "SKU",
                    value=produto["sku"] if "sku" in produto else ""
                )

                nova_referencia = st.text_input(
                    "Referência",
                    value=produto["referencia"] if "referencia" in produto else ""
                )

                nova_marca = st.text_input(
                    "Marca",
                    value=produto["marca"] if "marca" in produto else ""
                )

            with col2:

                nova_categoria = st.text_input(
                    "Categoria",
                    value=produto["categoria"] if "categoria" in produto else ""
                )

                nova_unidade = st.text_input(
                    "Unidade",
                    value=produto["unidade"] if "unidade" in produto else "UN"
                )

                novo_ncm = st.text_input(
                    "NCM",
                    value=produto["ncm"] if "ncm" in produto else ""
                )

                novo_cest = st.text_input(
                    "CEST",
                    value=produto["cest"] if "cest" in produto else ""
                )

                novo_cfop = st.text_input(
                    "CFOP",
                    value=produto["cfop_padrao"] if "cfop_padrao" in produto else ""
                )

            st.divider()

            # ==========================================
            # FINANCEIRO
            # ==========================================
            st.markdown("### 💰 Financeiro")

            col3, col4, col5 = st.columns(3)

            with col3:

                novo_custo = st.number_input(
                    "Custo",
                    min_value=0.0,
                    value=float(produto["custo"]) if "custo" in produto else 0.0,
                    format="%.2f"
                )

            with col4:

                novo_preco = st.number_input(
                    "Preço",
                    min_value=0.0,
                    value=float(produto["preco"]),
                    format="%.2f"
                )

            with col5:

                nova_margem = st.number_input(
                    "Margem %",
                    min_value=0.0,
                    value=float(produto["margem_lucro"]) if "margem_lucro" in produto else 0.0,
                    format="%.2f"
                )

            st.divider()

            # ==========================================
            # ESTOQUE
            # ==========================================
            st.markdown("### 📦 Estoque")

            col6, col7 = st.columns(2)

            with col6:

                novo_estoque = st.number_input(
                    "Estoque",
                    min_value=0.0,
                    value=float(produto["estoque"]),
                    format="%.3f"
                )

            with col7:

                novo_estoque_minimo = st.number_input(
                    "Estoque Mínimo",
                    min_value=0.0,
                    value=float(produto["estoque_minimo"]) if "estoque_minimo" in produto else 0.0,
                    format="%.3f"
                )

            nova_localizacao = st.text_input(
                "Localização",
                value=produto["localizacao"] if "localizacao" in produto else ""
            )

            observacoes = st.text_area(
                "Observações",
                value=produto["observacoes"] if "observacoes" in produto else ""
            )

            ativo = st.checkbox(
                "Produto Ativo",
                value=bool(produto["ativo"]) if "ativo" in produto else True
            )

            st.divider()

            # ==========================================
            # ATUALIZAR
            # ==========================================
            if st.button("💾 Salvar Alterações"):

                atualizar_produto(

                    produto["id"],

                    novo_nome,
                    novo_preco,
                    novo_estoque,

                    novo_codigo_barras,

                    novo_sku,
                    nova_referencia,
                    nova_marca,
                    nova_categoria,

                    nova_unidade,
                    novo_ncm,
                    novo_cest,
                    novo_cfop,

                    novo_custo,
                    nova_margem,

                    novo_estoque_minimo,
                    nova_localizacao,

                    ativo,
                    observacoes
                )

                st.success(
                    "✅ Produto atualizado!"
                )

                st.rerun()

            st.divider()

            # ==========================================
            # EXCLUIR
            # ==========================================
            st.subheader("🗑️ Excluir Produto")

            st.warning(
                f"Tem certeza que deseja excluir o produto: {produto['nome']}?"
            )

            if st.button("🗑️ Excluir Produto"):

                resultado = excluir_produto(
                    produto["id"]
                )

                if resultado == True:

                    st.success(
                        "Produto excluído com sucesso!"
                    )

                    st.rerun()

                elif resultado == "possui_vendas":

                    st.error(
                        "Não é permitido excluir produto com vendas vinculadas."
                    )

                else:

                    st.error(
                        "Erro ao excluir produto."
                    )