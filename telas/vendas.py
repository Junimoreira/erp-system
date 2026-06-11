import streamlit as st
import pandas as pd

from datetime import datetime

from database.vendas_db import (
    listar_clientes,
    listar_produtos,
    salvar_venda,
    historico_vendas
)

from database.produto_db import buscar_produto_por_codigo


# ==================================================
# TELA VENDAS
# ==================================================
def tela_vendas():

    abas = st.tabs([
        "➕ Nova Venda",
        "📋 Histórico"
    ])

    # ==================================================
    # NOVA VENDA
    # ==================================================
    with abas[0]:

        st.subheader("🛒 Nova Venda")

        clientes = listar_clientes()
        produtos = listar_produtos()

        if clientes.empty:
            st.warning("Cadastre clientes primeiro.")
            return

        if produtos.empty:
            st.warning("Cadastre produtos primeiro.")
            return

        # ==============================================
        # DATA DA VENDA
        # ==============================================
        data_venda = st.date_input(
            "📅 Data da Venda",
            value=datetime.today(),
            key="data_venda"
        )

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
        # FORMA PAGAMENTO
        # ==============================================
        forma_pagamento = st.selectbox(
            "Forma de Pagamento",
            ["Dinheiro", "PIX", "Cartão Débito", "Cartão Crédito","Boleto","Transferência", "Prazo"],
            key="forma_pagamento"
        )

        # ==============================================
        # CARRINHO
        # ==============================================
        if "carrinho" not in st.session_state:
            st.session_state.carrinho = []

        st.divider()

        # ==================================================
        # PRODUTO (PDV COM CÓDIGO DE BARRAS)
        # ==================================================
        st.subheader("📦 Adicionar Produto")

        codigo_barras = st.text_input(
            "📷 Código de Barras (escaneie ou digite)",
            key="codigo_barras_venda"
        )

        produto = None

        produto_id = None
        produto_nome = None
        produto_preco = 0
        produto_estoque = 0

        # ==============================================
        # BUSCA POR CÓDIGO DE BARRAS
        # ==============================================
        if codigo_barras:

            produto = buscar_produto_por_codigo(codigo_barras)

            if produto:

                st.success(f"Produto encontrado: {produto[1]}")

                produto_id = produto[0]
                produto_nome = produto[1]
                produto_preco = produto[2]
                produto_estoque = produto[3]

            else:

                st.error("Produto não encontrado pelo código de barras")

        # ==============================================
        # FALLBACK MANUAL
        # ==============================================
        if not produto_id:

            produto_nome_select = st.selectbox(
                "Selecione o Produto",
                produtos["nome"],
                key="produto_venda"
            )

            produto = produtos[
                produtos["nome"] == produto_nome_select
            ].iloc[0]

            produto_id = produto["id"]
            produto_nome = produto["nome"]
            produto_preco = produto["preco"]
            produto_estoque = produto["estoque"]

        # ==============================================
        # QUANTIDADE
        # ==============================================
        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            step=1,
            key="quantidade_venda"
        )

        # ==============================================
        # DESCONTO
        # ==============================================
        desconto = st.number_input(
            "Desconto",
            min_value=0.0,
            value=0.0,
            format="%.2f",
            key="desconto_venda"
        )

        subtotal = float(produto_preco) * quantidade
        valor_final = subtotal - desconto

        if valor_final < 0:
            valor_final = 0

        st.info(f"💰 Subtotal: R$ {subtotal:,.2f}")
        st.info(f"🏷️ Valor Final: R$ {valor_final:,.2f}")

        # ==============================================
        # ADICIONAR AO CARRINHO
        # ==============================================
        if st.button("➕ Adicionar ao Carrinho"):

            if quantidade > produto_estoque:

                st.error("❌ Estoque insuficiente!")

            else:

                st.session_state.carrinho.append({

                    "produto_id": int(produto_id),
                    "produto": produto_nome,
                    "quantidade": int(quantidade),
                    "preco": float(produto_preco),
                    "subtotal": float(subtotal),
                    "desconto": float(desconto),
                    "valor_final": float(valor_final)
                })

                st.success("✅ Produto adicionado!")
                st.rerun()

        # ==============================================
        # CARRINHO
        # ==============================================
        st.divider()
        st.subheader("🛒 Carrinho")

        if st.session_state.carrinho:

            df_carrinho = pd.DataFrame(st.session_state.carrinho)

            st.dataframe(df_carrinho, use_container_width=True)

            total = df_carrinho["valor_final"].sum()
            desconto_total = df_carrinho["desconto"].sum()

            st.success(f"💰 Total da Venda: R$ {total:,.2f}")
            st.info(f"🏷️ Desconto Total: R$ {desconto_total:,.2f}")

            # ==========================================
            # FINALIZAR VENDA
            # ==========================================
            if st.button("💾 Finalizar Venda"):

                sucesso = salvar_venda(

                    cliente_id=int(cliente_id),
                    valor_total=float(total),
                    desconto=float(desconto_total),
                    valor_final=float(total),
                    forma_pagamento=forma_pagamento,
                    data_venda=data_venda,
                    itens=st.session_state.carrinho
                )

                if sucesso:

                    st.session_state.carrinho = []
                    st.success("✅ Venda finalizada!")
                    st.rerun()

                else:

                    st.error("❌ Erro ao finalizar venda.")

        else:

            st.info("Carrinho vazio.")

    # ==================================================
    # HISTÓRICO
    # ==================================================
    with abas[1]:

        st.subheader("📋 Histórico de Vendas")

        df = historico_vendas()

        # ==============================================
        # FILTRO POR DATA
        # ==============================================
        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data Inicial",
                value=datetime.today(),
                key="data_inicio"
            )

        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=datetime.today(),
                key="data_fim"
            )

        # ==============================================
        # FILTRO PEDIDO
        # ==============================================
        filtro = st.text_input("🔎 Buscar pedido")

        # ==============================================
        # FILTRO DATA
        # ==============================================
        if not df.empty and "data_venda" in df.columns:

            df["data_venda"] = pd.to_datetime(df["data_venda"])

            df = df[
                (df["data_venda"].dt.date >= data_inicio) &
                (df["data_venda"].dt.date <= data_fim)
            ]

        # ==============================================
        # FILTRO PEDIDO
        # ==============================================
        if filtro and "pedido" in df.columns:
            df = df[df["pedido"].astype(str).str.contains(filtro)]

        # ==============================================
        # FORMATAÇÃO
        # ==============================================
        if not df.empty:

            if "data_venda" in df.columns:
                df["data_venda"] = df["data_venda"].dt.strftime("%d/%m/%Y")

            if "valor_unitario" in df.columns:
                df["valor_unitario"] = df["valor_unitario"].map(
                    lambda x: f"R$ {x:,.2f}"
                )

            if "subtotal" in df.columns:
                df["subtotal"] = df["subtotal"].map(
                    lambda x: f"R$ {x:,.2f}"
                )

            if "valor_final" in df.columns:
                df["valor_final"] = df["valor_final"].map(
                    lambda x: f"R$ {x:,.2f}"
                )

        st.dataframe(df, use_container_width=True)