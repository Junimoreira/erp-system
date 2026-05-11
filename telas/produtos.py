import streamlit as st
from database.produto_db import *


def tela_produtos():

    st.title("📦 Produtos")

    abas = st.tabs([
        "➕ Novo Produto",
        "📋 Produtos",
        "✏️ Editar Produto"
    ])

    # ==========================================
    # NOVO PRODUTO
    # ==========================================
    with abas[0]:

        st.subheader("Cadastrar Produto")

        nome = st.text_input("Nome do Produto")

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

            cadastrar_produto(
                nome,
                preco,
                estoque
            )

            st.success("✅ Produto cadastrado com sucesso!")

            st.rerun()

    # ==========================================
    # LISTAGEM
    # ==========================================
    with abas[1]:

        st.subheader("Produtos Cadastrados")

        df = listar_produtos()

        st.dataframe(
            df,
            use_container_width=True
        )

    # ==========================================
    # EDITAR PRODUTO
    # ==========================================
    with abas[2]:

        st.subheader("Editar Produto")

        df = listar_produtos()

        if not df.empty:

            id_produto = st.selectbox(
                "Selecione o Produto",
                df["id"]
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

            st.divider()

            if st.button("🗑️ Excluir Produto"):

                excluir_produto(id_produto)

                st.success("Produto excluído!")

                st.rerun()

        else:

            st.info("Nenhum produto cadastrado.")