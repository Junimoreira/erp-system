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
from database.contas_bancarias import listar_contas as listar_bancos
from database.caixa_db import verificar_caixa_aberto

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda,
    formatar_data
)


def normalizar_forma(forma):

    texto = str(forma).upper().strip()

    texto = texto.replace("Á", "A")
    texto = texto.replace("Ã", "A")
    texto = texto.replace("É", "E")
    texto = texto.replace("Ê", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O")
    texto = texto.replace("Õ", "O")
    texto = texto.replace("Ú", "U")
    texto = texto.replace("Ç", "C")

    return texto


def tela_vendas():

    st.title("🛒 Vendas")

    abas = st.tabs([
        "➕ Nova Venda",
        "📋 Histórico"
    ])

    with abas[0]:

        clientes = listar_clientes()
        produtos = listar_produtos()
        df_bancos = listar_bancos()

        if clientes.empty:
            st.warning("Nenhum cliente cadastrado.")
            return

        if produtos.empty:
            st.warning("Nenhum produto cadastrado.")
            return

        if "carrinho" not in st.session_state:
            st.session_state.carrinho = []

        st.subheader("🧾 Dados da Venda")

        col1, col2 = st.columns(2)

        with col1:
            data_venda = st.date_input(
                "📅 Data da Venda",
                value=datetime.today(),
                format="DD/MM/YYYY"
            )

        with col2:
            forma_pagamento = st.selectbox(
                "💳 Forma de Pagamento",
                [
                    "Dinheiro",
                    "PIX",
                    "Cartão Débito",
                    "Cartão Crédito",
                    "Transferência",
                    "Boleto",
                    "Prazo"
                ]
            )

        forma_normalizada = normalizar_forma(forma_pagamento)

        cliente_nome = st.selectbox(
            "👤 Cliente",
            clientes["nome"]
        )

        cliente_id = clientes.loc[
            clientes["nome"] == cliente_nome,
            "id"
        ].values[0]

        conta_bancaria_id = None
        numero_parcelas = 1

        formas_banco = [
            "PIX",
            "CARTAO DEBITO",
            "TRANSFERENCIA",
            "BOLETO"
        ]

        formas_parceladas = [
            "CARTAO CREDITO",
            "PRAZO",
            "FIADO"
        ]

        if forma_normalizada == "DINHEIRO":

            caixa_aberto = verificar_caixa_aberto()

            if caixa_aberto:
                st.success("✅ Caixa aberto. Venda em dinheiro será somada ao caixa.")
            else:
                st.error("⚠️ Não há caixa aberto. Abra o caixa antes de vender em dinheiro.")

        elif forma_normalizada in formas_banco:

            st.info("Essa venda será lançada em conta bancária.")

            if df_bancos.empty:
                st.error("Nenhuma conta bancária cadastrada. Cadastre uma conta bancária antes de finalizar essa venda.")
            else:
                df_bancos = df_bancos.copy()

                df_bancos["opcao"] = df_bancos.apply(
                    lambda row: (
                        f'{row["id"]} - {row["banco"]} | '
                        f'Ag: {row["agencia"]} | '
                        f'Conta: {row["conta"]} | '
                        f'Saldo: {formatar_moeda(row["saldo"])}'
                    ),
                    axis=1
                )

                banco_opcao = st.selectbox(
                    "🏦 Conta Bancária",
                    df_bancos["opcao"].tolist(),
                    key="conta_bancaria_venda"
                )

                conta_bancaria_id = int(banco_opcao.split(" - ")[0])

        elif forma_normalizada in formas_parceladas:

            st.info("Essa venda será registrada em Contas a Receber.")

            numero_parcelas = st.number_input(
                "Nº de parcelas",
                min_value=1,
                max_value=24,
                value=1,
                step=1,
                key="numero_parcelas_venda"
            )

            st.caption("A 1ª parcela vencerá em 30 dias. As demais vencem mês a mês.")

        st.divider()

        st.subheader("📦 Adicionar Produto")

        codigo = st.text_input(
            "Código de Barras",
            key="codigo_barras"
        )

        produto = None

        if codigo:
            produto = buscar_produto_por_codigo(codigo)

            if produto is None:
                st.error("Produto não encontrado.")

        if produto is None:

            produto_nome = st.selectbox(
                "Produto",
                produtos["nome"]
            )

            produto_linha = produtos[
                produtos["nome"] == produto_nome
            ].iloc[0]

            produto = {
                "id": produto_linha["id"],
                "nome": produto_linha["nome"],
                "preco": produto_linha["preco"],
                "estoque": produto_linha["estoque"]
            }

        st.success(f"Produto: {produto['nome']}")
        st.info(f"Estoque: {produto['estoque']}")

        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            value=1,
            step=1
        )

        desconto_item = st.number_input(
            "Desconto no item",
            min_value=0.0,
            value=0.00,
            step=0.01,
            format="%.2f"
        )

        preco = float(produto["preco"])
        subtotal = preco * quantidade
        valor_item = subtotal - desconto_item

        if valor_item < 0:
            valor_item = 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Preço Unitário", formatar_moeda(preco))

        with col2:
            st.metric("Subtotal", formatar_moeda(subtotal))

        with col3:
            st.metric("Valor do Item", formatar_moeda(valor_item))

        if st.button("➕ Adicionar ao Carrinho", use_container_width=True):

            if quantidade > int(produto["estoque"]):
                st.error("Estoque insuficiente.")

            else:
                st.session_state.carrinho.append({
                    "produto_id": int(produto["id"]),
                    "produto": produto["nome"],
                    "quantidade": int(quantidade),
                    "preco": float(preco),
                    "subtotal": float(subtotal),
                    "desconto": float(desconto_item),
                    "valor_final": float(valor_item)
                })

                st.success("Produto adicionado ao carrinho.")
                st.rerun()

        st.divider()
        st.subheader("🛒 Carrinho")

        if st.session_state.carrinho:

            df = pd.DataFrame(st.session_state.carrinho)

            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=True
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True
            )

            total_bruto = df["subtotal"].sum()
            desconto_total = df["desconto"].sum()
            total_final = df["valor_final"].sum()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.info(f"Subtotal: {formatar_moeda(total_bruto)}")

            with col2:
                st.warning(f"Descontos: {formatar_moeda(desconto_total)}")

            with col3:
                st.success(f"Total: {formatar_moeda(total_final)}")

            if forma_normalizada in formas_parceladas:

                valor_parcela = total_final / int(numero_parcelas)

                st.info(
                    f"💳 Parcelamento: {int(numero_parcelas)}x de {formatar_moeda(valor_parcela)}"
                )

            if st.button("🧹 Limpar Carrinho", use_container_width=True):
                st.session_state.carrinho = []
                st.rerun()

            st.divider()

            confirmar = st.checkbox(
                "Confirmo que desejo finalizar esta venda",
                key="confirmar_finalizar_venda"
            )

            if st.button("💾 Finalizar Venda", use_container_width=True):

                if not confirmar:
                    st.warning("Marque a confirmação antes de finalizar.")
                    return

                if forma_normalizada == "DINHEIRO":
                    caixa_aberto = verificar_caixa_aberto()

                    if not caixa_aberto:
                        st.error("Não é possível finalizar venda em dinheiro sem caixa aberto.")
                        return

                if forma_normalizada in formas_banco and conta_bancaria_id is None:
                    st.error("Selecione uma conta bancária para essa venda.")
                    return

                sucesso = salvar_venda(
                    cliente_id=int(cliente_id),
                    valor_total=float(total_bruto),
                    desconto=float(desconto_total),
                    valor_final=float(total_final),
                    forma_pagamento=forma_pagamento,
                    data_venda=datetime.combine(data_venda, datetime.now().time()),
                    itens=st.session_state.carrinho,
                    conta_bancaria_id=conta_bancaria_id,
                    numero_parcelas=int(numero_parcelas)
                )

                if sucesso:
                    st.success("Venda realizada com sucesso.")
                    st.session_state.carrinho = []
                    st.rerun()
                else:
                    st.error("Erro ao finalizar venda.")

        else:
            st.info("Carrinho vazio.")

    with abas[1]:

        st.subheader("📋 Histórico de Vendas")

        df = historico_vendas()

        if df.empty:
            st.info("Nenhuma venda cadastrada.")
            return

        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data Inicial",
                value=datetime.today(),
                key="hist_inicio"
            )

        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=datetime.today(),
                key="hist_fim"
            )

        pesquisa = st.text_input(
            "🔎 Buscar Pedido ou Cliente"
        )

        df["data_venda"] = pd.to_datetime(df["data_venda"])

        df = df[
            (df["data_venda"].dt.date >= data_inicio)
            &
            (df["data_venda"].dt.date <= data_fim)
        ]

        if pesquisa:

            pesquisa = pesquisa.lower()

            df = df[
                df["pedido"].astype(str).str.lower().str.contains(pesquisa)
                |
                df["cliente"].astype(str).str.lower().str.contains(pesquisa)
            ]

        df_exibicao = formatar_dataframe_brasil(
            df,
            com_hora=True,
            moedas=True
        )

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True
        )