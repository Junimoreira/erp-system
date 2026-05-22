import streamlit as st
import pandas as pd

from database.produto_db import (
    listar_produtos,
    cadastrar_produto,
    atualizar_produto,
    excluir_produto
)

from utils.preco_produto import (
    calcular_preco_venda,
    buscar_margem_padrao
)


# ==================================================
# TELA PRODUTOS (VERSÃO ERP PROFISSIONAL)
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

        with st.form("form_produto", clear_on_submit=True):

            st.markdown("### 📦 Dados Básicos")

            col1, col2 = st.columns(2)

            with col1:
                nome = st.text_input("Nome do Produto")
                codigo_barras = st.text_input("Código de Barras")
                sku = st.text_input("SKU")
                referencia = st.text_input("Referência")
                marca = st.text_input("Marca")

            with col2:
                categoria = st.text_input("Categoria")

                unidade = st.selectbox(
                    "Unidade",
                    ["UN", "KG", "CX", "PC", "LT"]
                )

                ncm = st.text_input("NCM")
                cest = st.text_input("CEST")
                cfop_padrao = st.text_input("CFOP")

            st.divider()

            # =========================
            # FINANCEIRO
            # =========================
            st.markdown("### 💰 Financeiro")

            col3, col4, col5 = st.columns(3)

            with col3:
                custo = st.number_input(
                    "Custo",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )

            # margem padrão do sistema
            margem_padrao = float(buscar_margem_padrao() or 0)

            with col4:
                taxa_cartao = st.number_input(
                    "Taxa Cartão (%)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )

                imposto = st.number_input(
                    "Imposto (%)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )

                frete = st.number_input(
                    "Frete (%)",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f"
                )

            # cálculo automático
            preco_automatico = calcular_preco_venda(
                custo,
                imposto,
                taxa_cartao,
                frete,
                margem_padrao
            )

            with col5:

                usar_manual = st.checkbox("Preço manual?")

                if usar_manual:
                    preco = st.number_input(
                        "Preço Venda",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f"
                    )
                else:
                    preco = preco_automatico
                    st.number_input(
                        "Preço Venda (Auto)",
                        value=float(preco),
                        disabled=True,
                        format="%.2f"
                    )

            st.divider()

            st.markdown("### 📦 Estoque")

            estoque = st.number_input(
                "Estoque",
                min_value=0,
                step=1,
                format="%d"
            )

            estoque_minimo = st.number_input(
                "Estoque Mínimo",
                min_value=0,
                step=1,
                format="%d"
            )

            localizacao = st.text_input("Localização")

            observacoes = st.text_area("Observações")

            ativo = st.checkbox("Ativo", value=True)

            salvar = st.form_submit_button("💾 Salvar")

            if salvar and nome:

                cadastrar_produto(
                    nome=nome,
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

                st.success("Produto cadastrado!")
                st.rerun()

    # ==================================================
    # LISTAGEM COM BUSCA
    # ==================================================
    with abas[1]:

        st.subheader("📋 Produtos")

        busca = st.text_input("🔎 Buscar produto")

        df = listar_produtos()

        if busca:
            df = df[df["nome"].str.contains(busca, case=False, na=False)]

        st.dataframe(df, use_container_width=True)

    # ==================================================
    # EDITAR
    # ==================================================
    with abas[2]:

        st.subheader("✏️ Editar Produto")

        df = listar_produtos()

        if df.empty:
            st.info("Sem produtos")
            return

        produtos = {
            f"{row['id']} - {row['nome']}": row
            for _, row in df.iterrows()
        }

        selecionado = st.selectbox("Produto", list(produtos.keys()))
        produto = produtos[selecionado]

        st.markdown("### Dados")

        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("Nome", produto["nome"])
            marca = st.text_input("Marca", produto.get("marca", ""))  # FIX
            sku = st.text_input("SKU", produto.get("sku", ""))

        with col2:
            categoria = st.text_input("Categoria", produto.get("categoria", ""))

        st.divider()

        custo = st.number_input(
            "Custo",
            value=float(produto.get("custo", 0)),
            step=0.01,
            format="%.2f"
        )

        margem_padrao = float(buscar_margem_padrao() or 0)

        preco = calcular_preco_venda(custo, margem_padrao)

        st.number_input(
            "Preço calculado",
            value=float(preco),
            disabled=True,
            format="%.2f"
        )

        estoque = st.number_input(
            "Estoque",
            value=int(produto.get("estoque", 0)),
            step=1,
            format="%d"
        )

        if st.button("Salvar alterações"):

            atualizar_produto(
                produto["id"],
                nome,
                preco,
                estoque,
                produto.get("codigo_barras"),
                sku,
                produto.get("referencia"),
                marca,  # FIX MARCA
                categoria,
                produto.get("unidade"),
                produto.get("ncm"),
                produto.get("cest"),
                produto.get("cfop_padrao"),
                custo,
                margem_padrao,
                produto.get("estoque_minimo"),
                produto.get("localizacao"),
                produto.get("ativo"),
                produto.get("observacoes")
            )

            st.success("Atualizado!")
            st.rerun()