# telas/trocas.py

import streamlit as st
import pandas as pd

from database.trocas_db import (
    buscar_venda_para_troca,
    listar_itens_disponiveis_troca,
    listar_produtos_para_troca,
    registrar_troca,
    historico_trocas,
    listar_itens_troca
)

from database.contas_bancarias import (
    listar_contas as listar_bancos
)

from database.caixa_db import (
    verificar_caixa_aberto
)

from utils.formatacao import (
    formatar_dataframe_brasil,
    formatar_moeda
)


# ============================================================
# NORMALIZAR FORMA DE PAGAMENTO
# ============================================================

def normalizar_forma(forma):

    texto = str(
        forma or ""
    ).upper().strip()

    substituicoes = {
        "Á": "A",
        "À": "A",
        "Â": "A",
        "Ã": "A",
        "É": "E",
        "Ê": "E",
        "Í": "I",
        "Ó": "O",
        "Ô": "O",
        "Õ": "O",
        "Ú": "U",
        "Ç": "C"
    }

    for antigo, novo in substituicoes.items():

        texto = texto.replace(
            antigo,
            novo
        )

    return texto


# ============================================================
# INICIALIZAR SESSION STATE
# ============================================================

def inicializar_estado_troca():

    if "troca_venda_id" not in st.session_state:
        st.session_state["troca_venda_id"] = None

    if "troca_novos" not in st.session_state:
        st.session_state["troca_novos"] = []

    if "troca_form_seq" not in st.session_state:
        st.session_state["troca_form_seq"] = 0

    if "troca_produto_seq" not in st.session_state:
        st.session_state["troca_produto_seq"] = 0


# ============================================================
# LIMPAR TROCA
# ============================================================

def limpar_troca():

    st.session_state["troca_venda_id"] = None
    st.session_state["troca_novos"] = []

    st.session_state["troca_form_seq"] += 1
    st.session_state["troca_produto_seq"] += 1


# ============================================================
# VALOR UNITÁRIO DE CRÉDITO
# ============================================================

def calcular_credito_unitario(row):

    quantidade = int(
        row.get(
            "quantidade_vendida",
            0
        ) or 0
    )

    valor_final = float(
        row.get(
            "valor_final",
            0
        ) or 0
    )

    if quantidade <= 0:
        return 0.0

    return round(
        valor_final / quantidade,
        2
    )


# ============================================================
# TELA PRINCIPAL
# ============================================================

def tela_trocas():

    inicializar_estado_troca()

    st.title("🔄 Trocas")

    abas = st.tabs(
        [
            "🔄 Nova Troca",
            "📋 Histórico"
        ]
    )

    # ========================================================
    # NOVA TROCA
    # ========================================================

    with abas[0]:

        mensagem = st.session_state.pop(
            "mensagem_troca",
            None
        )

        if mensagem:

            st.success(
                mensagem
            )

        st.info(
            "A troca não altera a venda original. "
            "O produto devolvido volta ao estoque, "
            "o novo produto sai do estoque e somente "
            "uma eventual diferença é registrada no "
            "movimento financeiro atual."
        )

        form_seq = st.session_state[
            "troca_form_seq"
        ]

        produto_seq = st.session_state[
            "troca_produto_seq"
        ]

        # ====================================================
        # LOCALIZAR VENDA
        # ====================================================

        st.subheader(
            "1️⃣ Localizar Venda Original"
        )

        col_busca1, col_busca2 = st.columns(
            [
                3,
                1
            ]
        )

        with col_busca1:

            venda_digitada = st.number_input(
                "Número da Venda",
                min_value=1,
                step=1,
                value=None,
                placeholder=(
                    "Informe o número da venda"
                ),
                key=f"troca_busca_venda_{form_seq}"
            )

        with col_busca2:

            st.write("")

            st.write("")

            buscar = st.button(
                "🔎 Buscar Venda",
                use_container_width=True,
                key=f"btn_buscar_troca_{form_seq}"
            )

        if buscar:

            if venda_digitada is None:

                st.warning(
                    "Informe o número da venda."
                )

            else:

                venda = buscar_venda_para_troca(
                    int(venda_digitada)
                )

                if venda is None:

                    st.error(
                        "Venda não encontrada."
                    )

                elif (
                    str(
                        venda.get(
                            "status",
                            ""
                        )
                    )
                    .strip()
                    .upper()
                    ==
                    "CANCELADA"
                ):

                    st.error(
                        "Esta venda está cancelada "
                        "e não pode ser utilizada "
                        "para troca."
                    )

                else:

                    st.session_state[
                        "troca_venda_id"
                    ] = int(
                        venda_digitada
                    )

                    st.session_state[
                        "troca_novos"
                    ] = []

                    st.session_state[
                        "troca_produto_seq"
                    ] += 1

                    st.rerun()

        venda_id = st.session_state.get(
            "troca_venda_id"
        )

        # ====================================================
        # VENDA CARREGADA
        # ====================================================

        if venda_id is not None:

            venda = buscar_venda_para_troca(
                venda_id
            )

            if venda is None:

                st.error(
                    "Não foi possível carregar "
                    "a venda selecionada."
                )

            else:

                st.divider()

                st.subheader(
                    "🧾 Venda Selecionada"
                )

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.metric(
                        "Venda",
                        f"#{venda['id']}"
                    )

                with col2:

                    st.metric(
                        "Cliente",
                        str(
                            venda.get(
                                "cliente",
                                ""
                            )
                            or
                            "Não informado"
                        )
                    )

                with col3:

                    st.metric(
                        "Valor da Venda",
                        formatar_moeda(
                            float(
                                venda.get(
                                    "valor_final",
                                    0
                                )
                                or 0
                            )
                        )
                    )

                with col4:

                    data_venda = venda.get(
                        "data_venda"
                    )

                    if data_venda:

                        try:

                            texto_data = (
                                pd.to_datetime(
                                    data_venda
                                )
                                .strftime(
                                    "%d/%m/%Y"
                                )
                            )

                        except Exception:

                            texto_data = str(
                                data_venda
                            )

                    else:

                        texto_data = "-"

                    st.metric(
                        "Data",
                        texto_data
                    )

                if st.button(
                    "🔄 Escolher outra venda",
                    key=(
                        f"troca_outra_venda_"
                        f"{form_seq}"
                    )
                ):

                    limpar_troca()
                    st.rerun()

                # =============================================
                # PRODUTOS DEVOLVIDOS
                # =============================================

                st.divider()

                st.subheader(
                    "2️⃣ Produto(s) Devolvido(s)"
                )

                itens_venda = (
                    listar_itens_disponiveis_troca(
                        venda_id
                    )
                )

                itens_devolvidos = []

                valor_credito = 0.0

                if itens_venda.empty:

                    st.warning(
                        "Esta venda não possui itens "
                        "disponíveis para troca."
                    )

                else:

                    for _, row in (
                        itens_venda.iterrows()
                    ):

                        item_id = int(
                            row[
                                "item_venda_id"
                            ]
                        )

                        quantidade_vendida = int(
                            row[
                                "quantidade_vendida"
                            ]
                            or 0
                        )

                        quantidade_ja_trocada = int(
                            row[
                                "quantidade_ja_trocada"
                            ]
                            or 0
                        )

                        quantidade_disponivel = int(
                            row[
                                "quantidade_disponivel"
                            ]
                            or 0
                        )

                        credito_unitario = (
                            calcular_credito_unitario(
                                row
                            )
                        )

                        with st.container(
                            border=True
                        ):

                            col_item1, col_item2 = (
                                st.columns(
                                    [
                                        3,
                                        1
                                    ]
                                )
                            )

                            with col_item1:

                                st.markdown(
                                    f"**{row['produto']}**"
                                )

                                st.caption(
                                    f"Vendido: "
                                    f"{quantidade_vendida} | "
                                    f"Já trocado: "
                                    f"{quantidade_ja_trocada} | "
                                    f"Disponível: "
                                    f"{quantidade_disponivel}"
                                )

                                st.caption(
                                    "Crédito unitário: "
                                    f"{formatar_moeda(credito_unitario)}"
                                )

                            with col_item2:

                                selecionar = (
                                    st.checkbox(
                                        "Devolver",
                                        key=(
                                            "troca_devolver_"
                                            f"{form_seq}_"
                                            f"{item_id}"
                                        ),
                                        disabled=(
                                            quantidade_disponivel
                                            <= 0
                                        )
                                    )
                                )

                            if (
                                selecionar
                                and
                                quantidade_disponivel
                                > 0
                            ):

                                quantidade_devolver = (
                                    st.number_input(
                                        "Quantidade a devolver",
                                        min_value=1,
                                        max_value=(
                                            quantidade_disponivel
                                        ),
                                        value=1,
                                        step=1,
                                        key=(
                                            "troca_qtd_devolver_"
                                            f"{form_seq}_"
                                            f"{item_id}"
                                        )
                                    )
                                )

                                credito_item = round(
                                    credito_unitario
                                    *
                                    int(
                                        quantidade_devolver
                                    ),
                                    2
                                )

                                st.success(
                                    "Crédito deste item: "
                                    f"{formatar_moeda(credito_item)}"
                                )

                                itens_devolvidos.append(
                                    {
                                        "item_venda_id": (
                                            item_id
                                        ),
                                        "quantidade": int(
                                            quantidade_devolver
                                        )
                                    }
                                )

                                valor_credito += (
                                    credito_item
                                )

                # =============================================
                # NOVOS PRODUTOS
                # =============================================

                st.divider()

                st.subheader(
                    "3️⃣ Novo(s) Produto(s)"
                )

                produtos = (
                    listar_produtos_para_troca()
                )

                if produtos.empty:

                    st.warning(
                        "Nenhum produto disponível."
                    )

                else:

                    produtos = produtos.copy()

                    produtos[
                        "descricao"
                    ] = produtos.apply(
                        lambda row: (
                            f'{row["id"]} - '
                            f'{row["nome"]} | '
                            f'{formatar_moeda(row["preco"])} | '
                            f'Estoque: {int(row["estoque"] or 0)}'
                        ),
                        axis=1
                    )

                    produto_escolhido = (
                        st.selectbox(
                            "Produto que o cliente levará",
                            options=(
                                produtos[
                                    "descricao"
                                ].tolist()
                            ),
                            index=None,
                            placeholder=(
                                "Selecione o novo produto"
                            ),
                            key=(
                                "troca_novo_produto_"
                                f"{produto_seq}"
                            )
                        )
                    )

                    produto_linha = None

                    if produto_escolhido:

                        produto_id_novo = int(
                            produto_escolhido.split(
                                " - "
                            )[0]
                        )

                        encontrado = produtos[
                            produtos["id"]
                            ==
                            produto_id_novo
                        ]

                        if not encontrado.empty:

                            produto_linha = (
                                encontrado.iloc[0]
                            )

                    if produto_linha is not None:

                        estoque_disponivel = int(
                            produto_linha[
                                "estoque"
                            ]
                            or 0
                        )

                        quantidade_nova = (
                            st.number_input(
                                "Quantidade do novo produto",
                                min_value=1,
                                max_value=max(
                                    estoque_disponivel,
                                    1
                                ),
                                value=1,
                                step=1,
                                key=(
                                    "troca_qtd_novo_"
                                    f"{produto_seq}"
                                )
                            )
                        )

                        preco_novo = float(
                            produto_linha[
                                "preco"
                            ]
                            or 0
                        )

                        valor_novo_item = round(
                            preco_novo
                            *
                            int(
                                quantidade_nova
                            ),
                            2
                        )

                        colpn1, colpn2 = (
                            st.columns(2)
                        )

                        with colpn1:

                            st.metric(
                                "Preço Unitário",
                                formatar_moeda(
                                    preco_novo
                                )
                            )

                        with colpn2:

                            st.metric(
                                "Valor",
                                formatar_moeda(
                                    valor_novo_item
                                )
                            )

                        if estoque_disponivel <= 0:

                            st.error(
                                "Este produto está "
                                "sem estoque."
                            )

                        elif st.button(
                            "➕ Adicionar Produto à Troca",
                            use_container_width=True,
                            key=(
                                "btn_add_novo_troca_"
                                f"{produto_seq}"
                            )
                        ):

                            produto_id_novo = int(
                                produto_linha["id"]
                            )

                            quantidade_nova = int(
                                quantidade_nova
                            )

                            existente = None

                            for item in st.session_state[
                                "troca_novos"
                            ]:

                                if (
                                    int(
                                        item[
                                            "produto_id"
                                        ]
                                    )
                                    ==
                                    produto_id_novo
                                ):

                                    existente = item
                                    break

                            if existente:

                                nova_quantidade = (
                                    int(
                                        existente[
                                            "quantidade"
                                        ]
                                    )
                                    +
                                    quantidade_nova
                                )

                                if (
                                    nova_quantidade
                                    >
                                    estoque_disponivel
                                ):

                                    st.error(
                                        "A quantidade total "
                                        "é maior que o estoque "
                                        "disponível."
                                    )

                                else:

                                    existente[
                                        "quantidade"
                                    ] = nova_quantidade

                                    existente[
                                        "valor_total"
                                    ] = round(
                                        preco_novo
                                        *
                                        nova_quantidade,
                                        2
                                    )

                                    st.session_state[
                                        "troca_produto_seq"
                                    ] += 1

                                    st.rerun()

                            else:

                                st.session_state[
                                    "troca_novos"
                                ].append(
                                    {
                                        "produto_id": (
                                            produto_id_novo
                                        ),
                                        "produto": (
                                            produto_linha[
                                                "nome"
                                            ]
                                        ),
                                        "quantidade": (
                                            quantidade_nova
                                        ),
                                        "preco": (
                                            preco_novo
                                        ),
                                        "valor_total": (
                                            valor_novo_item
                                        )
                                    }
                                )

                                st.session_state[
                                    "troca_produto_seq"
                                ] += 1

                                st.rerun()

                # =============================================
                # CARRINHO DOS NOVOS PRODUTOS
                # =============================================

                novos = st.session_state[
                    "troca_novos"
                ]

                valor_novos = 0.0

                if novos:

                    st.markdown(
                        "### 🛍️ Produtos da nova saída"
                    )

                    df_novos = pd.DataFrame(
                        novos
                    )

                    valor_novos = float(
                        df_novos[
                            "valor_total"
                        ].sum()
                    )

                    df_exibicao = (
                        formatar_dataframe_brasil(
                            df_novos.copy(),
                            com_hora=False,
                            moedas=True
                        )
                    )

                    st.dataframe(
                        df_exibicao,
                        use_container_width=True,
                        hide_index=True
                    )

                    if st.button(
                        "🧹 Limpar Novos Produtos",
                        use_container_width=True,
                        key=(
                            "troca_limpar_novos_"
                            f"{form_seq}"
                        )
                    ):

                        st.session_state[
                            "troca_novos"
                        ] = []

                        st.session_state[
                            "troca_produto_seq"
                        ] += 1

                        st.rerun()

                else:

                    st.info(
                        "Nenhum novo produto "
                        "adicionado."
                    )

                # =============================================
                # RESUMO FINANCEIRO
                # =============================================

                st.divider()

                st.subheader(
                    "4️⃣ Resumo da Troca"
                )

                valor_credito = round(
                    float(
                        valor_credito
                    ),
                    2
                )

                valor_novos = round(
                    float(
                        valor_novos
                    ),
                    2
                )

                diferenca = round(
                    valor_novos
                    -
                    valor_credito,
                    2
                )

                colr1, colr2, colr3 = (
                    st.columns(3)
                )

                with colr1:

                    st.metric(
                        "Crédito da Devolução",
                        formatar_moeda(
                            valor_credito
                        )
                    )

                with colr2:

                    st.metric(
                        "Novos Produtos",
                        formatar_moeda(
                            valor_novos
                        )
                    )

                with colr3:

                    if diferenca > 0:

                        st.metric(
                            "Cliente Paga",
                            formatar_moeda(
                                diferenca
                            )
                        )

                    elif diferenca == 0:

                        st.metric(
                            "Diferença",
                            formatar_moeda(
                                0
                            )
                        )

                    else:

                        st.metric(
                            "Saldo do Cliente",
                            formatar_moeda(
                                abs(
                                    diferenca
                                )
                            )
                        )

                # =============================================
                # DIFERENÇA POSITIVA
                # =============================================

                forma_pagamento = None
                conta_bancaria_id = None

                if diferenca > 0:

                    st.markdown(
                        "### 💰 Pagamento da Diferença"
                    )

                    forma_pagamento = (
                        st.selectbox(
                            "Forma de Pagamento",
                            [
                                "Dinheiro",
                                "PIX",
                                "Cartão Débito",
                                "Transferência",
                                "Boleto"
                            ],
                            key=(
                                "troca_forma_pagamento_"
                                f"{form_seq}"
                            )
                        )
                    )

                    forma_normalizada = (
                        normalizar_forma(
                            forma_pagamento
                        )
                    )

                    if (
                        forma_normalizada
                        ==
                        "DINHEIRO"
                    ):

                        caixa_aberto = (
                            verificar_caixa_aberto()
                        )

                        if caixa_aberto:

                            st.success(
                                "✅ Caixa aberto. "
                                "A diferença será "
                                "registrada no caixa atual."
                            )

                        else:

                            st.error(
                                "⚠️ Não há caixa aberto. "
                                "Não será possível concluir "
                                "a troca em dinheiro."
                            )

                    else:

                        bancos = listar_bancos()

                        if bancos.empty:

                            st.error(
                                "Nenhuma conta bancária "
                                "cadastrada."
                            )

                        else:

                            bancos = bancos.copy()

                            bancos[
                                "opcao"
                            ] = bancos.apply(
                                lambda row: (
                                    f'{row["id"]} - '
                                    f'{row["banco"]} | '
                                    f'Ag: {row["agencia"]} | '
                                    f'Conta: {row["conta"]}'
                                ),
                                axis=1
                            )

                            banco_opcao = (
                                st.selectbox(
                                    "Conta Bancária",
                                    options=(
                                        bancos[
                                            "opcao"
                                        ].tolist()
                                    ),
                                    index=None,
                                    placeholder=(
                                        "Selecione "
                                        "a conta bancária"
                                    ),
                                    key=(
                                        "troca_conta_"
                                        f"{form_seq}"
                                    )
                                )
                            )

                            if banco_opcao:

                                conta_bancaria_id = int(
                                    banco_opcao.split(
                                        " - "
                                    )[0]
                                )

                elif diferenca == 0:

                    st.success(
                        "✅ Troca de mesmo valor. "
                        "Nenhuma movimentação "
                        "financeira será gerada."
                    )

                else:

                    st.warning(
                        "⚠️ O novo produto possui valor "
                        "menor que o crédito da devolução."
                    )

                    st.info(
                        "Nesta primeira versão, esse tipo "
                        "de troca ainda não será concluído. "
                        "Na próxima etapa criaremos o "
                        "Vale-Troca / Crédito do Cliente."
                    )

                # =============================================
                # MOTIVO / OBSERVAÇÃO
                # =============================================

                st.divider()

                st.subheader(
                    "5️⃣ Informações da Troca"
                )

                motivo = st.selectbox(
                    "Motivo",
                    [
                        "Troca por preferência",
                        "Tamanho / modelo",
                        "Produto repetido",
                        "Presente",
                        "Defeito",
                        "Outro"
                    ],
                    key=(
                        "troca_motivo_"
                        f"{form_seq}"
                    )
                )

                observacoes = st.text_area(
                    "Observações",
                    key=(
                        "troca_observacoes_"
                        f"{form_seq}"
                    )
                )

                confirmar = st.checkbox(
                    "Confirmo os produtos e valores "
                    "desta troca",
                    key=(
                        "troca_confirmar_"
                        f"{form_seq}"
                    )
                )

                # =============================================
                # CONCLUIR TROCA
                # =============================================

                if st.button(
                    "✅ Concluir Troca",
                    type="primary",
                    use_container_width=True,
                    key=(
                        "btn_concluir_troca_"
                        f"{form_seq}"
                    )
                ):

                    if not itens_devolvidos:

                        st.warning(
                            "Selecione pelo menos "
                            "um produto devolvido."
                        )

                    elif not novos:

                        st.warning(
                            "Adicione pelo menos "
                            "um novo produto."
                        )

                    elif diferenca < 0:

                        st.warning(
                            "Esta troca gera crédito "
                            "para o cliente. "
                            "Aguarde a implementação "
                            "do Vale-Troca."
                        )

                    elif not confirmar:

                        st.warning(
                            "Marque a confirmação "
                            "antes de concluir."
                        )

                    elif (
                        diferenca > 0
                        and
                        forma_pagamento is None
                    ):

                        st.warning(
                            "Informe a forma de pagamento."
                        )

                    elif (
                        diferenca > 0
                        and
                        normalizar_forma(
                            forma_pagamento
                        )
                        ==
                        "DINHEIRO"
                        and
                        not verificar_caixa_aberto()
                    ):

                        st.error(
                            "Abra o caixa antes "
                            "de receber a diferença "
                            "em dinheiro."
                        )

                    elif (
                        diferenca > 0
                        and
                        normalizar_forma(
                            forma_pagamento
                        )
                        !=
                        "DINHEIRO"
                        and
                        conta_bancaria_id is None
                    ):

                        st.error(
                            "Selecione a conta bancária."
                        )

                    else:

                        usuario = (
                            st.session_state.get(
                                "nome"
                            )
                            or
                            st.session_state.get(
                                "usuario"
                            )
                            or
                            "Usuário"
                        )

                        resultado = registrar_troca(
                            venda_original_id=(
                                venda_id
                            ),
                            itens_devolvidos=(
                                itens_devolvidos
                            ),
                            itens_novos=[
                                {
                                    "produto_id": (
                                        item[
                                            "produto_id"
                                        ]
                                    ),
                                    "quantidade": (
                                        item[
                                            "quantidade"
                                        ]
                                    )
                                }
                                for item in novos
                            ],
                            motivo=motivo,
                            usuario=usuario,
                            observacoes=(
                                observacoes
                            ),
                            forma_pagamento_diferenca=(
                                forma_pagamento
                                if diferenca > 0
                                else None
                            ),
                            conta_bancaria_id=(
                                conta_bancaria_id
                                if diferenca > 0
                                else None
                            )
                        )

                        if resultado.get(
                            "sucesso"
                        ):

                            troca_id = resultado[
                                "troca_id"
                            ]

                            st.session_state[
                                "mensagem_troca"
                            ] = (
                                f"✅ Troca #{troca_id} "
                                "realizada com sucesso!"
                            )

                            limpar_troca()

                            st.rerun()

                        else:

                            st.error(
                                "Não foi possível "
                                "concluir a troca."
                            )

                            st.error(
                                resultado.get(
                                    "erro",
                                    "Erro desconhecido."
                                )
                            )

    # ========================================================
    # HISTÓRICO
    # ========================================================

    with abas[1]:

        st.subheader(
            "📋 Histórico de Trocas"
        )

        df_historico = historico_trocas()

        if df_historico.empty:

            st.info(
                "Nenhuma troca registrada."
            )

        else:

            pesquisa = st.text_input(
                "🔎 Buscar por troca, venda ou cliente",
                key="buscar_historico_trocas"
            )

            df_filtrado = (
                df_historico.copy()
            )

            if pesquisa:

                texto = (
                    pesquisa
                    .strip()
                    .lower()
                )

                mascara = pd.Series(
                    False,
                    index=df_filtrado.index
                )

                for coluna in [
                    "troca",
                    "venda_original",
                    "cliente"
                ]:

                    if coluna in df_filtrado.columns:

                        mascara = (
                            mascara
                            |
                            df_filtrado[
                                coluna
                            ]
                            .astype(str)
                            .str.lower()
                            .str.contains(
                                texto,
                                na=False
                            )
                        )

                df_filtrado = (
                    df_filtrado[
                        mascara
                    ]
                )

            df_exibicao = (
                formatar_dataframe_brasil(
                    df_filtrado.copy(),
                    com_hora=True,
                    moedas=True
                )
            )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            ids_trocas = (
                df_historico[
                    "troca"
                ]
                .astype(int)
                .tolist()
            )

            troca_detalhe = st.selectbox(
                "Visualizar itens da troca",
                options=ids_trocas,
                index=None,
                placeholder=(
                    "Selecione uma troca"
                ),
                format_func=lambda valor: (
                    f"Troca #{valor}"
                ),
                key="detalhe_troca_id"
            )

            if troca_detalhe is not None:

                itens = listar_itens_troca(
                    int(
                        troca_detalhe
                    )
                )

                if itens.empty:

                    st.info(
                        "Nenhum item encontrado."
                    )

                else:

                    st.markdown(
                        f"### Itens da Troca "
                        f"#{troca_detalhe}"
                    )

                    itens_exibicao = (
                        formatar_dataframe_brasil(
                            itens.copy(),
                            com_hora=False,
                            moedas=True
                        )
                    )

                    st.dataframe(
                        itens_exibicao,
                        use_container_width=True,
                        hide_index=True
                    )