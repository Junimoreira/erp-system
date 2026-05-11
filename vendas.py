import streamlit as st
import pandas as pd
from database.vendas_db import *


def tela_vendas():

    st.title("🛒 Vendas")

    abas = st.tabs([
        "➕ Nova Venda",
        "📋 Histórico"
    ])

    # ==================================================
    # NOVA VENDA
    # ==================================================
    with abas[0]:

        st.subheader("Nova Venda")

        clientes = listar_clientes()

        produtos = listar_produtos()

        if clientes.empty:

            st.warning("Cadastre clientes primeiro.")

            return

        if produtos.empty:

            st.warning("Cadastre produtos primeiro.")

            return

        # ==========================================
        # CLIENTE
        # ==========================================

        cliente_nome = st.selectbox(
            "Cliente",
            clientes["nome"],
            key="cliente_venda"
        )

        cliente_id = clientes[
            clientes["nome"] == cliente_nome
        ]["id"].values[0]

        # ==========================================
        # CARRINHO
        # ==========================================

        if "carrinho" not in st.session_state:

            st.session_state.carrinho = []

        st.divider()

        st.subheader("Adicionar Produto")

        produto_nome = st.selectbox(
            "Produto",
            produtos["nome"],
            key="produto_venda"
        )

        produto = produtos[
            produtos["nome"] == produto_nome
        ].iloc[0]

        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            step=1,
            key="quantidade_venda"
        )

        subtotal = (
            float(produto["preco"]) * quantidade
        )

        st.info(
            f"Subtotal: R$ {subtotal:,.2f}"
        )

        if st.button(
            "Adicionar ao Carrinho",
            key="botao_add_carrinho"
        ):

            if quantidade > produto["estoque"]:

                st.error(
                    "❌ Estoque insuficiente!"
                )

            else:

                st.session_state.carrinho.append({
                    "produto_id": int(produto["id"]),
                    "produto": produto["nome"],
                    "quantidade": quantidade,
                    "preco_unitario": float(produto["preco"]),
                    "subtotal": subtotal
                })

                st.success(
                    "✅ Produto adicionado!"
                )

                st.rerun()

        # ==========================================
        # EXIBIR CARRINHO
        # ==========================================

        st.divider()

        st.subheader("Carrinho")

        if st.session_state.carrinho:

            df_carrinho = pd.DataFrame(
                st.session_state.carrinho
            )

            st.dataframe(
                df_carrinho,
                use_container_width=True
            )

            total = df_carrinho[
                "subtotal"
            ].sum()

            st.success(
                f"💰 Total da Venda: R$ {total:,.2f}"
            )

            # ======================================
            # FINALIZAR VENDA
            # ======================================

            if st.button(
                "Finalizar Venda",
                key="finalizar_venda"
            ):

                venda_id = criar_venda(
                    cliente_id,
                    total
                )

                for item in st.session_state.carrinho:

                    adicionar_item_venda(
                        venda_id,
                        item["produto_id"],
                        item["quantidade"],
                        item["preco_unitario"],
                        item["subtotal"]
                    )

                lancar_financeiro_venda(total)

                st.session_state.carrinho = []

                st.success(
                    "✅ Venda finalizada!"
                )

                st.rerun()

        else:

            st.info(
                "Carrinho vazio."
            )

    # ==================================================
    # HISTÓRICO
    # ==================================================
    with abas[1]:

        st.subheader("Histórico de Vendas")

        df = listar_vendas()

        st.dataframe(
            df,
            use_container_width=True
        )