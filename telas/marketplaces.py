# telas/marketplaces.py

from datetime import datetime
import secrets

import streamlit as st

from services.marketplaces.magalu import MagaluMarketplace

from database.marketplaces_db import (
    listar_canais_marketplace,
    listar_clientes_marketplace,
    listar_produtos_marketplace,
    listar_pedidos_marketplace,
    registrar_pedido_marketplace,
    registrar_oauth_state,
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def formatar_brl(valor):

    valor = float(valor or 0)

    texto = f"{valor:,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


def converter_data_hora(texto):

    texto = str(
        texto or ""
    ).strip()

    if not texto:
        return None

    formatos = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]

    for formato in formatos:

        try:

            return datetime.strptime(
                texto,
                formato
            )

        except ValueError:
            pass

    raise ValueError(
        "Data inválida. Use DD/MM/AAAA HH:MM "
        "ou DD/MM/AAAA."
    )


# ============================================================
# CADASTRO MANUAL MAGALU
# ============================================================

def cadastro_manual_magalu(
    canal_id
):

    st.subheader(
        "➕ Registrar Pedido Magalu"
    )

    st.caption(
        "Cadastro manual para contingência. "
        "Futuramente estes dados serão obtidos "
        "automaticamente pela API."
    )

    clientes = (
        listar_clientes_marketplace()
    )

    produtos = (
        listar_produtos_marketplace()
    )

    if clientes.empty:

        st.warning(
            "Nenhum cliente disponível."
        )

        return

    if produtos.empty:

        st.warning(
            "Nenhum produto disponível."
        )

        return

    # --------------------------------------------------------
    # MAPAS PARA SELECTBOX
    # --------------------------------------------------------

    mapa_clientes = {}

    for _, cliente in clientes.iterrows():

        cliente_id = int(
            cliente["id"]
        )

        documento = (
            cliente.get("cnpj")
            or
            cliente.get("cpf")
            or
            ""
        )

        cidade = (
            cliente.get("cidade")
            or
            ""
        )

        uf = (
            cliente.get("uf")
            or
            ""
        )

        texto = (
            f"{cliente_id} - "
            f"{cliente['nome']}"
        )

        if documento:
            texto += f" | {documento}"

        if cidade:
            texto += f" | {cidade}"

        if uf:
            texto += f"/{uf}"

        mapa_clientes[
            cliente_id
        ] = texto

    mapa_produtos = {}

    for _, produto in produtos.iterrows():

        produto_id = int(
            produto["id"]
        )

        nome = str(
            produto["nome"]
        )

        estoque = float(
            produto.get(
                "estoque",
                0
            )
            or 0
        )

        custo = float(
            produto.get(
                "custo",
                0
            )
            or 0
        )

        mapa_produtos[
            produto_id
        ] = (
            f"{produto_id} - {nome} "
            f"| Estoque: {estoque:g} "
            f"| Custo: {formatar_brl(custo)}"
        )

    # --------------------------------------------------------
    # PEDIDO
    # --------------------------------------------------------

    st.markdown(
        "#### 🧾 Dados do pedido"
    )

    c1, c2 = st.columns(2)

    with c1:

        pedido_externo = st.text_input(
            "Número do pedido Magalu",
            placeholder="Ex.: LU-1531770107905712",
            key="magalu_pedido_externo"
        )

        data_pedido_texto = st.text_input(
            "Data/hora da compra",
            placeholder="DD/MM/AAAA HH:MM",
            key="magalu_data_pedido"
        )

    with c2:

        forma_pagamento = st.text_input(
            "Forma de pagamento no marketplace",
            placeholder="Ex.: Pix",
            key="magalu_forma_pagamento"
        )

        data_aprovacao_texto = st.text_input(
            "Data/hora da aprovação",
            placeholder="DD/MM/AAAA HH:MM",
            key="magalu_data_aprovacao"
        )

    cliente_id = st.selectbox(
        "Cliente",
        options=list(
            mapa_clientes.keys()
        ),
        index=None,
        placeholder="Selecione o cliente",
        format_func=lambda x: (
            mapa_clientes[x]
        ),
        key="magalu_cliente"
    )

    # --------------------------------------------------------
    # PRODUTO
    # --------------------------------------------------------

    st.markdown(
        "#### 📦 Produto"
    )

    produto_id = st.selectbox(
        "Produto do ERP",
        options=list(
            mapa_produtos.keys()
        ),
        index=None,
        placeholder="Selecione o produto",
        format_func=lambda x: (
            mapa_produtos[x]
        ),
        key="magalu_produto"
    )

    p1, p2, p3 = st.columns(3)

    with p1:

        quantidade = st.number_input(
            "Quantidade",
            min_value=1.0,
            value=1.0,
            step=1.0,
            key="magalu_quantidade"
        )

    with p2:

        valor_unitario = st.number_input(
            "Preço unitário vendido",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_valor_unitario"
        )

    with p3:

        sku_marketplace = st.text_input(
            "SKU no Magalu",
            key="magalu_sku"
        )

    codigo_anuncio = st.text_input(
        "Código do anúncio no Magalu",
        key="magalu_codigo_anuncio"
    )

    # --------------------------------------------------------
    # FINANCEIRO
    # --------------------------------------------------------

    st.markdown(
        "#### 💰 Valores do marketplace"
    )

    f1, f2, f3 = st.columns(3)

    with f1:

        valor_frete_cliente = st.number_input(
            "Frete pago pelo cliente",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_frete_cliente"
        )

    with f2:

        valor_desconto = st.number_input(
            "Desconto ao cliente",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_desconto"
        )

    with f3:

        valor_repasse_previsto = st.number_input(
            "Repasse previsto",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_repasse_previsto"
        )

    t1, t2, t3 = st.columns(3)

    with t1:

        percentual_comissao = st.number_input(
            "Comissão (%)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_comissao_percentual"
        )

        valor_comissao = st.number_input(
            "Comissão (R$)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_comissao_valor"
        )

    with t2:

        valor_tarifa_fixa = st.number_input(
            "Tarifa fixa",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_tarifa_fixa"
        )

        valor_taxas_outros = st.number_input(
            "Outras taxas",
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.2f",
            key="magalu_taxas_outros"
        )

    with t3:

        frete_apurado = st.checkbox(
            "Coparticipação de frete já apurada",
            key="magalu_frete_apurado"
        )

        valor_coparticipacao_frete = None

        if frete_apurado:

            valor_coparticipacao_frete = (
                st.number_input(
                    "Coparticipação do frete",
                    min_value=0.0,
                    value=0.0,
                    step=0.01,
                    format="%.2f",
                    key="magalu_coparticipacao"
                )
            )

    observacoes = st.text_area(
        "Observações",
        placeholder=(
            "Informações adicionais sobre "
            "o pedido, NF-e, despacho etc."
        ),
        key="magalu_observacoes"
    )

    # --------------------------------------------------------
    # PRÉVIA ECONÔMICA
    # --------------------------------------------------------

    valor_produtos = round(
        float(quantidade)
        *
        float(valor_unitario),
        2
    )

    valor_total_cliente = round(
        valor_produtos
        +
        float(valor_frete_cliente)
        -
        float(valor_desconto),
        2
    )

    custo_total = 0.0

    if produto_id is not None:

        linha_produto = produtos[
            produtos["id"]
            ==
            produto_id
        ]

        if not linha_produto.empty:

            custo_unitario = float(
                linha_produto.iloc[0][
                    "custo"
                ]
                or 0
            )

            custo_total = round(
                custo_unitario
                *
                float(quantidade),
                2
            )

    resultado_estimado = round(
        float(
            valor_repasse_previsto
        )
        -
        custo_total,
        2
    )

    st.markdown(
        "#### 📊 Prévia econômica"
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric(
        "Produtos",
        formatar_brl(
            valor_produtos
        )
    )

    m2.metric(
        "Total cliente",
        formatar_brl(
            valor_total_cliente
        )
    )

    m3.metric(
        "Custo",
        formatar_brl(
            custo_total
        )
    )

    m4.metric(
        "Resultado estimado",
        formatar_brl(
            resultado_estimado
        )
    )

    if (
        valor_repasse_previsto > 0
        and
        resultado_estimado < 0
    ):

        st.error(
            "⚠️ Este pedido apresenta "
            f"prejuízo estimado de "
            f"{formatar_brl(abs(resultado_estimado))}."
        )

    elif (
        valor_repasse_previsto > 0
        and
        resultado_estimado >= 0
    ):

        st.success(
            "Resultado estimado positivo: "
            f"{formatar_brl(resultado_estimado)}."
        )

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    salvar = st.button(
        "💾 Salvar pedido Magalu",
        type="primary",
        key="salvar_pedido_magalu"
    )

    if salvar:

        try:

            if cliente_id is None:

                raise ValueError(
                    "Selecione o cliente."
                )

            if produto_id is None:

                raise ValueError(
                    "Selecione o produto."
                )

            if not str(
                pedido_externo or ""
            ).strip():

                raise ValueError(
                    "Informe o número do pedido."
                )

            data_pedido = (
                converter_data_hora(
                    data_pedido_texto
                )
            )

            data_aprovacao = (
                converter_data_hora(
                    data_aprovacao_texto
                )
            )

            taxas = []

            if valor_comissao > 0:

                taxas.append(
                    {
                        "tipo": "COMISSAO",
                        "descricao": (
                            "Comissão do marketplace"
                        ),
                        "percentual": (
                            percentual_comissao
                        ),
                        "valor": (
                            valor_comissao
                        ),
                        "responsabilidade": (
                            "VENDEDOR"
                        )
                    }
                )

            if valor_tarifa_fixa > 0:

                taxas.append(
                    {
                        "tipo": "TARIFA_FIXA",
                        "descricao": (
                            "Tarifa fixa do marketplace"
                        ),
                        "percentual": None,
                        "valor": (
                            valor_tarifa_fixa
                        ),
                        "responsabilidade": (
                            "VENDEDOR"
                        )
                    }
                )

            if valor_taxas_outros > 0:

                taxas.append(
                    {
                        "tipo": "OUTRAS",
                        "descricao": (
                            "Outras taxas do marketplace"
                        ),
                        "percentual": None,
                        "valor": (
                            valor_taxas_outros
                        ),
                        "responsabilidade": (
                            "VENDEDOR"
                        )
                    }
                )

            resultado = (
                registrar_pedido_marketplace(
                    canal_id=canal_id,

                    pedido_externo=(
                        pedido_externo
                    ),

                    cliente_id=(
                        cliente_id
                    ),

                    itens=[
                        {
                            "produto_id": (
                                produto_id
                            ),

                            "quantidade": (
                                quantidade
                            ),

                            "valor_unitario": (
                                valor_unitario
                            ),

                            "sku_marketplace": (
                                sku_marketplace
                            ),

                            "codigo_anuncio": (
                                codigo_anuncio
                            ),
                        }
                    ],

                    data_pedido=(
                        data_pedido
                    ),

                    data_aprovacao=(
                        data_aprovacao
                    ),

                    forma_pagamento=(
                        forma_pagamento
                    ),

                    valor_frete_cliente=(
                        valor_frete_cliente
                    ),

                    valor_desconto=(
                        valor_desconto
                    ),

                    valor_comissao=(
                        valor_comissao
                    ),

                    valor_tarifa_fixa=(
                        valor_tarifa_fixa
                    ),

                    valor_taxas_outros=(
                        valor_taxas_outros
                    ),

                    valor_coparticipacao_frete=(
                        valor_coparticipacao_frete
                    ),

                    valor_repasse_previsto=(
                        valor_repasse_previsto
                    ),

                    taxas=taxas,

                    observacoes=(
                        observacoes
                    )
                )
            )

            if resultado.get(
                "sucesso"
            ):

                st.session_state[
                    "marketplace_flash"
                ] = (
                    "Pedido cadastrado com sucesso. "
                    f"ID ERP: {resultado['pedido_id']} | "
                    "Resultado estimado: "
                    f"{formatar_brl(resultado['resultado_estimado'])}"
                )

                st.rerun()

            else:

                st.error(
                    resultado.get(
                        "erro",
                        "Erro ao cadastrar pedido."
                    )
                )

        except Exception as erro:

            st.error(
                str(erro)
            )


# ============================================================
# TELA PRINCIPAL
# ============================================================

def tela_marketplaces():

    st.title(
        "🛍️ Marketplaces"
    )

    st.caption(
        "Gestão integrada de vendas realizadas "
        "em marketplaces."
    )

    mensagem = st.session_state.pop(
        "marketplace_flash",
        None
    )

    if mensagem:

        st.success(
            mensagem
        )

    (
        aba_visao_geral,
        aba_pedidos,
        aba_magalu,
        aba_ml,
        aba_shopee,
    ) = st.tabs(
        [
            "📊 Visão Geral",
            "📦 Pedidos",
            "🟠 Magalu",
            "🟡 Mercado Livre",
            "🟣 Shopee",
        ]
    )

    # ========================================================
    # VISÃO GERAL
    # ========================================================

    with aba_visao_geral:

        st.subheader(
            "Visão Geral dos Marketplaces"
        )

        canais = (
            listar_canais_marketplace()
        )

        if canais.empty:

            st.warning(
                "Nenhum marketplace cadastrado."
            )

        else:

            col1, col2, col3 = (
                st.columns(3)
            )

            total_canais = len(
                canais
            )

            integrados = int(
                canais[
                    "integracao_api"
                ].sum()
            )

            pendentes = (
                total_canais
                -
                integrados
            )

            col1.metric(
                "Marketplaces ativos",
                total_canais
            )

            col2.metric(
                "Integrações ativas",
                integrados
            )

            col3.metric(
                "Integrações pendentes",
                pendentes
            )

        pedidos = (
            listar_pedidos_marketplace()
        )

        st.divider()

        if pedidos.empty:

            st.info(
                "Ainda não existem pedidos "
                "de marketplace cadastrados."
            )

        else:

            total_pedidos = len(
                pedidos
            )

            total_cliente = float(
                pedidos[
                    "valor_total_cliente"
                ].fillna(0).sum()
            )

            total_repasse = float(
                pedidos[
                    "valor_repasse_previsto"
                ].fillna(0).sum()
            )

            resultado_estimado = float(
                pedidos[
                    "resultado_estimado"
                ].fillna(0).sum()
            )

            c1, c2, c3, c4 = (
                st.columns(4)
            )

            c1.metric(
                "Pedidos",
                total_pedidos
            )

            c2.metric(
                "Valor vendido",
                formatar_brl(
                    total_cliente
                )
            )

            c3.metric(
                "Repasse previsto",
                formatar_brl(
                    total_repasse
                )
            )

            c4.metric(
                "Resultado estimado",
                formatar_brl(
                    resultado_estimado
                )
            )

            if resultado_estimado < 0:

                st.error(
                    "⚠️ Existem pedidos com "
                    "resultado econômico negativo."
                )

    # ========================================================
    # PEDIDOS
    # ========================================================

    with aba_pedidos:

        st.subheader(
            "Pedidos dos Marketplaces"
        )

        pedidos = (
            listar_pedidos_marketplace()
        )

        if pedidos.empty:

            st.info(
                "Nenhum pedido cadastrado."
            )

        else:

            st.dataframe(
                pedidos,
                use_container_width=True,
                hide_index=True
            )

    # ========================================================
    # MAGALU
    # ========================================================

    with aba_magalu:

        st.subheader(
            "Magazine Luiza"
        )

        st.caption(
            "Pedidos, taxas, repasses, "
            "NF-e e despacho."
        )

        canais = (
            listar_canais_marketplace()
        )

        canal_magalu = canais[
            canais["codigo"]
            ==
            "MAGALU"
        ]

        if canal_magalu.empty:

            st.warning(
                "Canal Magalu não encontrado."
            )

        else:

            canal_id = int(
                canal_magalu.iloc[0][
                    "id"
                ]
            )

            # --------------------------------------------
            # INTEGRACAO API MAGALU
            # --------------------------------------------

            st.markdown(
                "### ?? Integra??o com o Magalu"
            )

            try:
                conector_magalu = MagaluMarketplace()

                if not conector_magalu.oauth_configurado():
                    st.warning(
                        "Configura??o OAuth do Magalu "
                        "ainda n?o est? dispon?vel "
                        "neste ambiente."
                    )

                else:
                    st.success(
                        "Aplica??o OAuth do Magalu "
                        "configurada neste ambiente."
                    )

                    if st.button(
                        "Preparar conex?o com o Magalu",
                        key="preparar_oauth_magalu",
                    ):
                        state = secrets.token_urlsafe(32)

                        # Persiste o state no banco para que
                        # sobreviva ao redirecionamento externo
                        # Magalu -> ERP.
                        registrar_oauth_state(
                            canal_id=canal_id,
                            state=state,
                            validade_minutos=10,
                        )

                        # Mantemos tambem na sessao apenas como
                        # apoio visual/local, mas a validacao
                        # real sera feita pelo banco.
                        st.session_state[
                            "magalu_oauth_state"
                        ] = state

                        url_autorizacao = (
                            conector_magalu
                            .gerar_url_autorizacao(
                                state
                            )
                        )

                        st.session_state[
                            "magalu_oauth_url"
                        ] = url_autorizacao

                        st.success(
                            "Conex?o preparada com seguran?a."
                        )

                    url_autorizacao = (
                        st.session_state.get(
                            "magalu_oauth_url"
                        )
                    )

                    if url_autorizacao:
                        st.info(
                            "A autoriza??o foi preparada. "
                            "Ainda n?o prossiga com a "
                            "conex?o real."
                        )

                        st.link_button(
                            "Abrir autoriza??o do Magalu",
                            url_autorizacao,
                        )

            except Exception:
                st.error(
                    "N?o foi poss?vel preparar a "
                    "integra??o com o Magalu."
                )

            st.divider()

            pedidos_magalu = (
                listar_pedidos_marketplace(
                    canal_id
                )
            )

            st.markdown(
                "### 📦 Pedidos cadastrados"
            )

            if pedidos_magalu.empty:

                st.info(
                    "Ainda não existem pedidos "
                    "do Magalu cadastrados."
                )

            else:

                st.dataframe(
                    pedidos_magalu,
                    use_container_width=True,
                    hide_index=True
                )

            st.divider()

            cadastro_manual_magalu(
                canal_id
            )

    # ========================================================
    # MERCADO LIVRE
    # ========================================================

    with aba_ml:

        st.subheader(
            "Mercado Livre"
        )

        st.info(
            "Estrutura preparada. "
            "Integração será implementada "
            "em etapa posterior."
        )

    # ========================================================
    # SHOPEE
    # ========================================================

    with aba_shopee:

        st.subheader(
            "Shopee"
        )

        st.info(
            "Estrutura preparada. "
            "Integração será implementada "
            "em etapa posterior."
        )
