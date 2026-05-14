# telas/vendas.py

import streamlit as st
import pandas as pd

from database.vendas_db import (
    listar_clientes,
    listar_produtos,
    salvar_venda,
    historico_vendas
)


def tela_vendas():

    # ==================================================
    # ABAS
    # ==================================================

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

        # ==============================================
        # VALIDAR CLIENTES
        # ==============================================

        if clientes.empty:

            st.warning(
                "Cadastre clientes primeiro."
            )

            return

        # ==============================================
        # VALIDAR PRODUTOS
        # ==============================================

        if produtos.empty:

            st.warning(
                "Cadastre produtos primeiro."
            )

            return

        # ==============================================
        # CLIENTE
        # ==============================================

                # ==============================================
        # CLIENTE
        # ==============================================

        cliente_nome = st.selectbox(
            "Cliente",
            clientes["nome"],
            key="cliente_venda"
        )

        cliente_id = clientes[
            clientes["nome"] == cliente_nome
        ]["id"].values[0]

        # ==============================================
        # FORMA DE PAGAMENTO
        # ==============================================

        forma_pagamento = st.selectbox(

            "Forma de Pagamento",

            [
                "Dinheiro",
                "PIX",
                "Cartão",
                "Prazo"
            ],

            key="forma_pagamento"
        )

        # ==============================================
        # CARRINHO
        # ==============================================
        # ==============================================
        # CARRINHO
        # ==============================================

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

        # ==============================================
        # ADICIONAR AO CARRINHO
        # ==============================================

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

                    "quantidade": int(quantidade),

                    "preco": float(produto["preco"]),

                    "subtotal": float(subtotal)
                })

                st.success(
                    "✅ Produto adicionado!"
                )

                st.rerun()

        # ==============================================
        # EXIBIR CARRINHO
        # ==============================================

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

            # ==========================================
            # FINALIZAR VENDA
            # ==========================================

            if st.button(
                "Finalizar Venda",
                key="finalizar_venda"
            ):

                sucesso = salvar_venda(

                    cliente_id=int(cliente_id),

                    valor_total=float(total),

                    forma_pagamento=forma_pagamento,

                    itens=st.session_state.carrinho
                )

                if sucesso:

                    st.session_state.carrinho = []

                    st.success(
                        "✅ Venda finalizada!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Erro ao finalizar venda."
                    )

        else:

            st.info(
                "Carrinho vazio."
            )

    # ==================================================
    # HISTÓRICO
    # ==================================================

    with abas[1]:

        st.subheader(
            "📋 Histórico de Vendas"
        )

        df = historico_vendas()

        # ==============================================
        # FILTRO
        # ==============================================

        filtro = st.text_input(
            "🔎 Buscar pedido"
        )

        if filtro:

            df = df[
                df["pedido"].astype(str).str.contains(filtro)
            ]

        # ==============================================
        # FORMATAR MOEDA
        # ==============================================

        if not df.empty:

            if "valor_unitario" in df.columns:

                df["valor_unitario"] = df[
                    "valor_unitario"
                ].map(
                    lambda x: f"R$ {x:,.2f}"
                )

            if "subtotal" in df.columns:

                df["subtotal"] = df[
                    "subtotal"
                ].map(
                    lambda x: f"R$ {x:,.2f}"
                )

            if "total" in df.columns:

                df["total"] = df[
                    "total"
                ].map(
                    lambda x: f"R$ {x:,.2f}"
                )

        st.dataframe(
            df,
            use_container_width=True
        )