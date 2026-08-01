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
    formatar_moeda
)


# ==================================================
# NORMALIZAR FORMA DE PAGAMENTO
# ==================================================
def normalizar_forma(forma):

    texto = str(forma).upper().strip()

    texto = texto.replace("Á", "A")
    texto = texto.replace("À", "A")
    texto = texto.replace("Â", "A")
    texto = texto.replace("Ã", "A")
    texto = texto.replace("É", "E")
    texto = texto.replace("Ê", "E")
    texto = texto.replace("Í", "I")
    texto = texto.replace("Ó", "O")
    texto = texto.replace("Ô", "O")
    texto = texto.replace("Õ", "O")
    texto = texto.replace("Ú", "U")
    texto = texto.replace("Ç", "C")

    return texto


# ==================================================
# TELA DE VENDAS
# ==================================================
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

        clientes = listar_clientes()
        produtos = listar_produtos()
        df_bancos = listar_bancos()

        if clientes.empty:
            st.warning("Nenhum cliente cadastrado.")
            return

        if produtos.empty:
            st.warning("Nenhum produto cadastrado.")
            return

        # ==================================================
        # SESSION STATE
        # ==================================================
        if "carrinho" not in st.session_state:
            st.session_state["carrinho"] = []

        # Controla uma nova venda.
        # Ao incrementar, os widgets recebem novas chaves
        # e aparecem limpos sem alterar widgets já criados.
        if "venda_form_seq" not in st.session_state:
            st.session_state["venda_form_seq"] = 0

        # Controla a limpeza somente dos campos de produto.
        if "produto_form_seq" not in st.session_state:
            st.session_state["produto_form_seq"] = 0

        venda_seq = st.session_state["venda_form_seq"]
        produto_seq = st.session_state["produto_form_seq"]

        # ==================================================
        # DADOS DA VENDA
        # ==================================================
        st.subheader("🧾 Dados da Venda")

        col1, col2 = st.columns(2)

        with col1:
            data_venda = st.date_input(
                "📅 Data da Venda",
                value=datetime.today().date(),
                format="DD/MM/YYYY",
                key=f"data_venda_{venda_seq}"
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
                ],
                key=f"forma_pagamento_venda_{venda_seq}"
            )

        forma_normalizada = normalizar_forma(
            forma_pagamento
        )

        cliente_nome = st.selectbox(
            "👤 Cliente",
            options=clientes["nome"].tolist(),
            index=None,
            placeholder="Selecione um cliente",
            key=f"cliente_venda_{venda_seq}"
        )

        cliente_id = None

        if cliente_nome is not None:

            cliente_encontrado = clientes.loc[
                clientes["nome"] == cliente_nome
            ]

            if not cliente_encontrado.empty:
                cliente_id = int(
                    cliente_encontrado.iloc[0]["id"]
                )

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

        # ==================================================
        # VENDA EM DINHEIRO
        # ==================================================
        if forma_normalizada == "DINHEIRO":

            caixa_aberto = verificar_caixa_aberto()

            if caixa_aberto:
                st.success(
                    "✅ Caixa aberto. "
                    "Venda em dinheiro será somada ao caixa."
                )
            else:
                st.error(
                    "⚠️ Não há caixa aberto. "
                    "Abra o caixa antes de vender em dinheiro."
                )

        # ==================================================
        # VENDA COM ENTRADA EM BANCO
        # ==================================================
        elif forma_normalizada in formas_banco:

            st.info(
                "Essa venda será lançada em conta bancária."
            )

            if df_bancos.empty:

                st.error(
                    "Nenhuma conta bancária cadastrada. "
                    "Cadastre uma conta bancária antes "
                    "de finalizar essa venda."
                )

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
                    options=df_bancos["opcao"].tolist(),
                    index=None,
                    placeholder="Selecione uma conta bancária",
                    key=f"conta_bancaria_venda_{venda_seq}"
                )

                if banco_opcao is not None:
                    conta_bancaria_id = int(
                        banco_opcao.split(" - ")[0]
                    )

        # ==================================================
        # VENDA PARCELADA
        # ==================================================
        elif forma_normalizada in formas_parceladas:

            st.info(
                "Essa venda será registrada "
                "em Contas a Receber."
            )

            numero_parcelas = st.number_input(
                "Nº de parcelas",
                min_value=1,
                max_value=24,
                value=1,
                step=1,
                key=f"numero_parcelas_venda_{venda_seq}"
            )

            st.caption(
                "A 1ª parcela vencerá em 30 dias. "
                "As demais vencem mês a mês."
            )

        st.divider()

        # ==================================================
        # ADICIONAR PRODUTO
        # ==================================================
        st.subheader("📦 Adicionar Produto")

        codigo = st.text_input(
            "Código de Barras",
            key=f"codigo_barras_{produto_seq}",
            placeholder="Digite ou leia o código de barras"
        )

        produto = None
        produto_nome = None

        # ==================================================
        # BUSCA POR CÓDIGO DE BARRAS
        # ==================================================
        if codigo:

            produto = buscar_produto_por_codigo(
                codigo.strip()
            )

            if produto is None:
                st.error("Produto não encontrado.")

        # ==================================================
        # SELEÇÃO MANUAL DO PRODUTO
        # ==================================================
        if produto is None:

            produto_nome = st.selectbox(
                "Produto",
                options=produtos["nome"].tolist(),
                index=None,
                placeholder="Selecione um produto",
                key=f"produto_venda_{produto_seq}"
            )

            if produto_nome is not None:

                produto_encontrado = produtos.loc[
                    produtos["nome"] == produto_nome
                ]

                if not produto_encontrado.empty:

                    produto_linha = (
                        produto_encontrado.iloc[0]
                    )

                    produto = {
                        "id": produto_linha["id"],
                        "nome": produto_linha["nome"],
                        "preco": produto_linha["preco"],
                        "estoque": produto_linha["estoque"]
                    }

        if produto is None:

            st.info(
                "Selecione um produto ou informe "
                "o código de barras."
            )

        else:

            st.success(
                f"Produto selecionado: {produto['nome']}"
            )

            st.info(
                f"Estoque disponível: {produto['estoque']}"
            )

        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            value=1,
            step=1,
            key=f"quantidade_venda_{produto_seq}"
        )

        desconto_item = st.number_input(
            "Desconto no item",
            min_value=0.0,
            value=0.00,
            step=0.01,
            format="%.2f",
            key=f"desconto_item_venda_{produto_seq}"
        )

        preco = 0.0
        subtotal = 0.0
        valor_item = 0.0

        if produto is not None:

            preco = float(
                produto["preco"] or 0
            )

            subtotal = (
                preco * int(quantidade)
            )

            valor_item = (
                subtotal - float(desconto_item)
            )

            if valor_item < 0:
                valor_item = 0.0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Preço Unitário",
                formatar_moeda(preco)
            )

        with col2:
            st.metric(
                "Subtotal",
                formatar_moeda(subtotal)
            )

        with col3:
            st.metric(
                "Valor do Item",
                formatar_moeda(valor_item)
            )

        # ==================================================
        # BOTÃO ADICIONAR AO CARRINHO
        # ==================================================
        if st.button(
            "➕ Adicionar ao Carrinho",
            use_container_width=True,
            key=f"adicionar_carrinho_{produto_seq}"
        ):

            if produto is None:

                st.warning(
                    "Selecione um produto antes "
                    "de adicionar ao carrinho."
                )

            elif int(quantidade) > int(
                produto["estoque"] or 0
            ):

                st.error(
                    "Estoque insuficiente."
                )

            elif float(desconto_item) > float(subtotal):

                st.warning(
                    "O desconto não pode ser maior "
                    "que o subtotal do item."
                )

            else:

                st.session_state["carrinho"].append({
                    "produto_id": int(
                        produto["id"]
                    ),
                    "produto": produto["nome"],
                    "quantidade": int(
                        quantidade
                    ),
                    "preco": float(
                        preco
                    ),
                    "subtotal": float(
                        subtotal
                    ),
                    "desconto": float(
                        desconto_item
                    ),
                    "valor_final": float(
                        valor_item
                    )
                })

                # Não altera diretamente os widgets já criados.
                # Apenas incrementa o controle para que, no rerun,
                # novos campos de produto sejam criados vazios.
                st.session_state["produto_form_seq"] += 1

                st.rerun()

        st.divider()

        # ==================================================
        # CARRINHO
        # ==================================================
        st.subheader("🛒 Carrinho")

        if st.session_state["carrinho"]:

            df = pd.DataFrame(
                st.session_state["carrinho"]
            )

            df_exibicao = (
                formatar_dataframe_brasil(
                    df.copy(),
                    com_hora=False,
                    moedas=True
                )
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True
            )

            total_bruto = float(
                df["subtotal"].sum()
            )

            desconto_total = float(
                df["desconto"].sum()
            )

            total_final = float(
                df["valor_final"].sum()
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.info(
                    f"Subtotal: "
                    f"{formatar_moeda(total_bruto)}"
                )

            with col2:
                st.warning(
                    f"Descontos: "
                    f"{formatar_moeda(desconto_total)}"
                )

            with col3:
                st.success(
                    f"Total: "
                    f"{formatar_moeda(total_final)}"
                )

            if forma_normalizada in formas_parceladas:

                valor_parcela = (
                    total_final
                    /
                    int(numero_parcelas)
                )

                st.info(
                    f"💳 Parcelamento: "
                    f"{int(numero_parcelas)}x de "
                    f"{formatar_moeda(valor_parcela)}"
                )

            # ==================================================
            # LIMPAR CARRINHO
            # ==================================================
            if st.button(
                "🧹 Limpar Carrinho",
                use_container_width=True,
                key="limpar_carrinho_venda"
            ):

                st.session_state["carrinho"] = []

                # Limpa também a área do produto na próxima execução.
                st.session_state["produto_form_seq"] += 1

                st.rerun()

            st.divider()

            confirmar = st.checkbox(
                "Confirmo que desejo finalizar esta venda",
                key=f"confirmar_finalizar_venda_{venda_seq}"
            )

            # ==================================================
            # FINALIZAR VENDA
            # ==================================================
            if st.button(
                "💾 Finalizar Venda",
                use_container_width=True,
                key=f"finalizar_venda_{venda_seq}"
            ):

                if cliente_id is None:

                    st.warning(
                        "Selecione um cliente antes "
                        "de finalizar a venda."
                    )

                    return

                if not confirmar:

                    st.warning(
                        "Marque a confirmação antes "
                        "de finalizar."
                    )

                    return

                if total_final <= 0:

                    st.warning(
                        "O valor total da venda deve "
                        "ser maior que zero."
                    )

                    return

                if forma_normalizada == "DINHEIRO":

                    caixa_aberto = (
                        verificar_caixa_aberto()
                    )

                    if not caixa_aberto:

                        st.error(
                            "Não é possível finalizar "
                            "venda em dinheiro sem caixa aberto."
                        )

                        return

                if (
                    forma_normalizada in formas_banco
                    and conta_bancaria_id is None
                ):

                    st.error(
                        "Selecione uma conta bancária "
                        "para essa venda."
                    )

                    return

                sucesso = salvar_venda(
                    cliente_id=int(
                        cliente_id
                    ),
                    valor_total=float(
                        total_bruto
                    ),
                    desconto=float(
                        desconto_total
                    ),
                    valor_final=float(
                        total_final
                    ),
                    forma_pagamento=forma_pagamento,
                    data_venda=datetime.combine(
                        data_venda,
                        datetime.now().time()
                    ),
                    itens=st.session_state["carrinho"],
                    conta_bancaria_id=conta_bancaria_id,
                    numero_parcelas=int(
                        numero_parcelas
                    )
                )

                if sucesso:

                    st.session_state["carrinho"] = []

                    # Inicia uma nova venda com campos vazios.
                    # Como as chaves mudam, não ocorre o erro
                    # de alteração de widget já instanciado.
                    st.session_state["venda_form_seq"] += 1
                    st.session_state["produto_form_seq"] += 1

                    st.rerun()

                else:

                    st.error(
                        "Erro ao finalizar venda."
                    )

        else:

            st.info("Carrinho vazio.")

    # ==================================================
    # HISTÓRICO DE VENDAS
    # ==================================================
    with abas[1]:

        st.subheader(
            "📋 Histórico de Vendas"
        )

        df = historico_vendas()

        if df.empty:

            st.info(
                "Nenhuma venda cadastrada."
            )

            return

        col1, col2 = st.columns(2)

        with col1:

            data_inicio = st.date_input(
                "Data Inicial",
                value=datetime.today().date(),
                format="DD/MM/YYYY",
                key="hist_inicio"
            )

        with col2:

            data_fim = st.date_input(
                "Data Final",
                value=datetime.today().date(),
                format="DD/MM/YYYY",
                key="hist_fim"
            )

        if data_inicio > data_fim:

            st.error(
                "A data inicial não pode ser "
                "maior que a data final."
            )

            return

        pesquisa = st.text_input(
            "🔎 Buscar Pedido ou Cliente",
            key="pesquisa_historico_vendas"
        )

        df = df.copy()

        df["data_venda"] = pd.to_datetime(
            df["data_venda"],
            errors="coerce"
        )

        df = df[
            df["data_venda"].notna()
        ]

        df = df[
            (
                df["data_venda"].dt.date
                >= data_inicio
            )
            &
            (
                df["data_venda"].dt.date
                <= data_fim
            )
        ]

        if pesquisa:

            pesquisa_normalizada = (
                pesquisa
                .strip()
                .lower()
            )

            filtro_pedido = pd.Series(
                False,
                index=df.index
            )

            filtro_cliente = pd.Series(
                False,
                index=df.index
            )

            if "pedido" in df.columns:
                filtro_pedido = (
                    df["pedido"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        pesquisa_normalizada,
                        na=False
                    )
                )

            if "cliente" in df.columns:
                filtro_cliente = (
                    df["cliente"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        pesquisa_normalizada,
                        na=False
                    )
                )

            df = df[
                filtro_pedido
                |
                filtro_cliente
            ]

        df_exibicao = (
            formatar_dataframe_brasil(
                df.copy(),
                com_hora=True,
                moedas=True
            )
        )

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True
        )