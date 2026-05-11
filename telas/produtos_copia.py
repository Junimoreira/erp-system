import streamlit as st
from database.produto_db import *


def tela_produtos():

    st.subheader("📦 Produtos")

    abas = st.tabs([
        "➕ Novo Produto",
        "📋 Produtos",
        "✏️ Editar Produto"
    ])

    # =========================================
    # NOVO PRODUTO
    # =========================================
    with abas[0]:

        nome = st.text_input("Nome do produto")

        preco = st.number_input(
            "Preço",
            min_value=0.0,
            format="%.2f"
        )

        estoque = st.number_input(
            "Estoque",
            min_value=0,
            step=1
        )

        if st.button("Cadastrar Produto"):

            if nome == "":

                st.warning("Digite o nome do produto")

            else:

                cadastrar_produto(
                    nome,
                    preco,
                    estoque
                )

                st.success("✅ Produto cadastrado!")

                st.rerun()

    # =========================================
    # LISTAGEM
    # =========================================
    with abas[1]:

        df = listar_produtos()

        st.dataframe(
            df,
            use_container_width=True
        )

        st.divider()

        id_excluir = st.number_input(
            "ID para excluir",
            min_value=1,
            step=1,
            key="excluir_produto"
        )

        if st.button("🗑️ Excluir Produto"):

            excluir_produto(id_excluir)

            st.success("Produto excluído!")

            st.rerun()

    # =========================================
    # EDITAR
    # =========================================
    with abas[2]:

        df = listar_produtos()

        lista_ids = df["id"].tolist()

        if len(lista_ids) > 0:

            id_produto = st.selectbox(
                "Selecione o produto",
                lista_ids
            )

            produto = df[df["id"] == id_produto].iloc[0]

            novo_nome = st.text_input(
                "Nome",
                value=produto["nome"]
            )

            novo_preco = st.number_input(
                "Preço",
                min_value=0.0,
                value=float(produto["preco"]),
                format="%.2f"
            )

            novo_estoque = st.number_input(
                "Estoque",
                min_value=0,
                value=int(produto["estoque"]),
                step=1
            )

            if st.button("Salvar Alterações"):

                atualizar_produto(
                    id_produto,
                    novo_nome,
                    novo_preco,
                    novo_estoque
                )

                st.success("✅ Produto atualizado!")

                st.rerun()

        else:

            st.info("Nenhum produto cadastrado.")