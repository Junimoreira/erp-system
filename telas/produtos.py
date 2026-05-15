import streamlit as st

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

            nome = st.text_input(
                "Nome do Produto"
            )

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

            salvar = st.form_submit_button(
                "💾 Cadastrar Produto"
            )

            if salvar:

                if nome.strip() == "":

                    st.warning(
                        "Informe o nome do produto."
                    )

                else:

                    cadastrar_produto(
                        nome,
                        preco,
                        estoque
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

            produto = produtos[
                produto_selecionado
            ]

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

            # ==========================================
            # ATUALIZAR
            # ==========================================

            if st.button(
                "💾 Salvar Alterações"
            ):

                atualizar_produto(
                    produto["id"],
                    novo_nome,
                    novo_preco,
                    novo_estoque
                )

                st.success(
                    "✅ Produto atualizado!"
                )

                st.rerun()

            st.divider()

            # ==========================================
            # EXCLUIR
            # ==========================================

            st.subheader(
                "🗑️ Excluir Produto"
            )

            st.warning(
                f"Tem certeza que deseja excluir o produto: {produto['nome']}?"
            )

            if st.button(
                "🗑️ Excluir Produto"
            ):

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