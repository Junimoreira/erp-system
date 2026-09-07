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
    buscar_vinculo_produto_marketplace,
    salvar_vinculo_produto_marketplace,
    listar_vinculos_produtos_marketplace,
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
                "### 🔗 Integração com o Magalu"
            )

            try:
                conector_magalu = MagaluMarketplace()

                if not conector_magalu.oauth_configurado():
                    st.warning(
                        "Configuração OAuth do Magalu "
                        "ainda não está disponível "
                        "neste ambiente."
                    )

                else:
                    st.success(
                        "Aplicação OAuth do Magalu "
                        "configurada neste ambiente."
                    )

                    if st.button(
                        "Preparar conexão com o Magalu",
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

                        # Mantemos também na sessão apenas como
                        # apoio visual/local, mas a validação
                        # real será feita pelo banco.
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
                            "Conexão preparada com segurança."
                        )

                    url_autorizacao = (
                        st.session_state.get(
                            "magalu_oauth_url"
                        )
                    )

                    if url_autorizacao:
                        st.info(
                            "A autorização foi preparada. "
                            "Clique abaixo para continuar "
                            "no ID Magalu."
                        )

                        st.link_button(
                            "Abrir autorização do Magalu",
                            url_autorizacao,
                        )

                    st.divider()

                    st.markdown(
                        "### 🧪 Teste da API Magalu"
                    )

                    st.caption(
                        "Consulta a API usando as credenciais "
                        "salvas pelo OAuth, sem exibir tokens."
                    )

                    if st.button(
                        "Testar leitura de pedidos Magalu",
                        key="testar_leitura_pedidos_magalu",
                    ):
                        try:
                            conector_teste = MagaluMarketplace()

                            credenciais_ok = (
                                conector_teste
                                .carregar_credenciais_banco()
                            )

                            if not credenciais_ok:
                                st.warning(
                                    "Nenhuma credencial válida do Magalu "
                                    "foi encontrada no banco."
                                )

                            else:
                                with st.spinner(
                                    "Consultando pedidos no Magalu..."
                                ):
                                    resposta_pedidos = (
                                        conector_teste
                                        .listar_pedidos()
                                    )

                                st.success(
                                    "Consulta realizada com sucesso."
                                )

                                st.write(
                                    "Resposta recebida da API:"
                                )

                                st.json(
                                    resposta_pedidos
                                )

                        except Exception as erro:
                            st.error(
                                "Não foi possível consultar os "
                                "pedidos do Magalu."
                            )

                            st.exception(
                                erro
                            )

                    # --------------------------------------------
                    # DIAGNOSTICO DO CHANNEL ID
                    # --------------------------------------------

                    if st.button(
                        "Diagnosticar Channel ID do Magalu",
                        key="diagnosticar_channel_id_magalu",
                    ):
                        try:
                            conector_diagnostico = (
                                MagaluMarketplace()
                            )

                            credenciais_ok = (
                                conector_diagnostico
                                .carregar_credenciais_banco()
                            )

                            if not credenciais_ok:
                                st.warning(
                                    "Nenhuma credencial válida "
                                    "do Magalu foi encontrada."
                                )

                            else:
                                with st.spinner(
                                    "Procurando identificadores "
                                    "de canal na API..."
                                ):
                                    resposta_diagnostico = (
                                        conector_diagnostico
                                        .listar_pedidos()
                                    )

                                campos_channel = []

                                def procurar_channel(
                                    valor,
                                    caminho="raiz",
                                ):
                                    if isinstance(
                                        valor,
                                        dict,
                                    ):
                                        for chave, conteudo in (
                                            valor.items()
                                        ):
                                            novo_caminho = (
                                                f"{caminho}.{chave}"
                                            )

                                            if (
                                                "channel"
                                                in str(
                                                    chave
                                                ).lower()
                                            ):
                                                campos_channel.append(
                                                    {
                                                        "campo": (
                                                            novo_caminho
                                                        ),
                                                        "valor": (
                                                            conteudo
                                                        ),
                                                    }
                                                )

                                            procurar_channel(
                                                conteudo,
                                                novo_caminho,
                                            )

                                    elif isinstance(
                                        valor,
                                        list,
                                    ):
                                        for indice, item in enumerate(
                                            valor
                                        ):
                                            procurar_channel(
                                                item,
                                                (
                                                    f"{caminho}"
                                                    f"[{indice}]"
                                                ),
                                            )

                                procurar_channel(
                                    resposta_diagnostico
                                )

                                if campos_channel:
                                    st.success(
                                        "Identificadores relacionados "
                                        "a channel encontrados."
                                    )

                                    st.json(
                                        campos_channel
                                    )

                                else:
                                    st.warning(
                                        "Nenhum campo relacionado "
                                        "a channel foi encontrado "
                                        "na resposta dos pedidos."
                                    )

                                # ------------------------------------
                                # PROCURAR UUIDS NA RESPOSTA
                                # ------------------------------------

                                import re

                                uuids_encontrados = []

                                padrao_uuid = re.compile(
                                    r"^[0-9a-fA-F]{8}-"
                                    r"[0-9a-fA-F]{4}-"
                                    r"[0-9a-fA-F]{4}-"
                                    r"[0-9a-fA-F]{4}-"
                                    r"[0-9a-fA-F]{12}$"
                                )

                                def procurar_uuid(
                                    valor,
                                    caminho="raiz",
                                ):
                                    if isinstance(
                                        valor,
                                        dict,
                                    ):
                                        for chave, conteudo in (
                                            valor.items()
                                        ):
                                            procurar_uuid(
                                                conteudo,
                                                (
                                                    f"{caminho}."
                                                    f"{chave}"
                                                ),
                                            )

                                    elif isinstance(
                                        valor,
                                        list,
                                    ):
                                        for indice, item in enumerate(
                                            valor
                                        ):
                                            procurar_uuid(
                                                item,
                                                (
                                                    f"{caminho}"
                                                    f"[{indice}]"
                                                ),
                                            )

                                    elif isinstance(
                                        valor,
                                        str,
                                    ):
                                        texto_uuid = valor.strip()

                                        if padrao_uuid.fullmatch(
                                            texto_uuid
                                        ):
                                            registro_uuid = {
                                                "campo": caminho,
                                                "valor": texto_uuid,
                                            }

                                            if (
                                                registro_uuid
                                                not in uuids_encontrados
                                            ):
                                                uuids_encontrados.append(
                                                    registro_uuid
                                                )

                                procurar_uuid(
                                    resposta_diagnostico
                                )

                                if uuids_encontrados:
                                    st.success(
                                        "UUID(s) encontrado(s) "
                                        "na resposta dos pedidos."
                                    )

                                    st.json(
                                        uuids_encontrados
                                    )

                                else:
                                    st.info(
                                        "Nenhum UUID foi encontrado "
                                        "na resposta dos pedidos."
                                    )

                        except Exception as erro:
                            st.error(
                                "Não foi possível executar "
                                "o diagnóstico de Channel ID."
                            )

                            st.exception(
                                erro
                            )

                    st.divider()

                    # --------------------------------------------
                    # LOCALIZAR PEDIDO E ENTREGA MAGALU
                    # --------------------------------------------

                    st.markdown(
                        "### 🔎 Localizar pedido e entrega Magalu"
                    )

                    st.caption(
                        "Localiza o pedido na listagem retornada pela API "
                        "e extrai automaticamente o ID da entrega. "
                        "Não usa X-Channel-Id nesta etapa."
                    )

                    codigo_pedido_magalu = st.text_input(
                        "Código do pedido Magalu",
                        value="LU-1531770107905712",
                        key="codigo_pedido_magalu_consulta",
                    )

                    if st.button(
                        "Localizar pedido e entrega",
                        key="localizar_pedido_entrega_magalu",
                    ):
                        try:
                            codigo_consulta = str(
                                codigo_pedido_magalu or ""
                            ).strip()

                            if not codigo_consulta:
                                st.warning(
                                    "Informe o código do pedido Magalu."
                                )

                            else:
                                conector_pedido = MagaluMarketplace()

                                credenciais_ok = (
                                    conector_pedido
                                    .carregar_credenciais_banco()
                                )

                                if not credenciais_ok:
                                    st.warning(
                                        "Nenhuma credencial válida "
                                        "do Magalu foi encontrada."
                                    )

                                else:
                                    with st.spinner(
                                        "Localizando pedido no Magalu..."
                                    ):
                                        resposta_pedidos = (
                                            conector_pedido
                                            .listar_pedidos()
                                        )

                                    resultados = []

                                    if isinstance(
                                        resposta_pedidos,
                                        dict,
                                    ):
                                        resultados = (
                                            resposta_pedidos.get(
                                                "results",
                                                [],
                                            )
                                            or []
                                        )

                                    pedido_encontrado = None

                                    for pedido_api in resultados:
                                        if not isinstance(
                                            pedido_api,
                                            dict,
                                        ):
                                            continue

                                        codigo_api = str(
                                            pedido_api.get("code")
                                            or ""
                                        ).strip()

                                        if codigo_api == codigo_consulta:
                                            pedido_encontrado = pedido_api
                                            break

                                    if pedido_encontrado is None:
                                        st.session_state.pop(
                                            "pedido_magalu_consultado",
                                            None,
                                        )
                                        st.session_state.pop(
                                            "magalu_entrega_id",
                                            None,
                                        )

                                        codigos_disponiveis = [
                                            str(
                                                pedido_api.get("code")
                                                or ""
                                            ).strip()
                                            for pedido_api in resultados
                                            if isinstance(
                                                pedido_api,
                                                dict,
                                            )
                                            and str(
                                                pedido_api.get("code")
                                                or ""
                                            ).strip()
                                        ]

                                        st.warning(
                                            "O pedido informado não foi "
                                            "encontrado na página de pedidos "
                                            "retornada pela API."
                                        )

                                        if codigos_disponiveis:
                                            st.info(
                                                "Pedidos retornados nesta "
                                                "consulta: "
                                                + ", ".join(
                                                    codigos_disponiveis
                                                )
                                            )

                                    else:
                                        st.session_state[
                                            "pedido_magalu_consultado"
                                        ] = pedido_encontrado

                                        entregas = (
                                            pedido_encontrado.get(
                                                "deliveries",
                                                [],
                                            )
                                            or []
                                        )

                                        ids_entregas = []

                                        for entrega in entregas:
                                            if not isinstance(
                                                entrega,
                                                dict,
                                            ):
                                                continue

                                            entrega_id = str(
                                                entrega.get("id")
                                                or ""
                                            ).strip()

                                            if (
                                                entrega_id
                                                and entrega_id
                                                not in ids_entregas
                                            ):
                                                ids_entregas.append(
                                                    entrega_id
                                                )

                                        st.success(
                                            "Pedido localizado com sucesso."
                                        )

                                        st.write(
                                            "**Código do pedido:** "
                                            f"{codigo_consulta}"
                                        )

                                        pedido_id = str(
                                            pedido_encontrado.get("id")
                                            or ""
                                        ).strip()

                                        if pedido_id:
                                            st.write(
                                                "**ID interno do pedido "
                                                "Magalu:** "
                                                f"{pedido_id}"
                                            )

                                        if ids_entregas:
                                            st.session_state[
                                                "magalu_entrega_id"
                                            ] = ids_entregas[0]

                                            st.success(
                                                "ID da entrega localizado: "
                                                f"{ids_entregas[0]}"
                                            )

                                            if len(ids_entregas) > 1:
                                                st.info(
                                                    "Este pedido possui "
                                                    f"{len(ids_entregas)} "
                                                    "entregas. Os IDs são: "
                                                    + ", ".join(
                                                        ids_entregas
                                                    )
                                                )

                                        else:
                                            st.session_state.pop(
                                                "magalu_entrega_id",
                                                None,
                                            )

                                            st.warning(
                                                "O pedido foi localizado, "
                                                "mas a resposta não trouxe "
                                                "nenhuma entrega vinculada."
                                            )

                        except Exception as erro:
                            st.error(
                                "Não foi possível localizar o pedido "
                                "e a entrega no Magalu."
                            )

                            st.exception(
                                erro
                            )

                    pedido_magalu_consultado = (
                        st.session_state.get(
                            "pedido_magalu_consultado"
                        )
                    )

                    if pedido_magalu_consultado:
                        st.markdown(
                            "#### 📦 Dados do pedido localizado"
                        )

                        st.json(
                            pedido_magalu_consultado
                        )

                    st.divider()

                    # --------------------------------------------
                    # VINCULO DE PRODUTOS MAGALU -> ERP
                    # --------------------------------------------

                    st.markdown(
                        "### 🔗 Vincular produtos do Magalu"
                    )

                    st.caption(
                        "Relaciona o SKU recebido do Magalu "
                        "ao produto correspondente no ERP."
                    )

                    if st.button(
                        "Carregar produtos dos pedidos Magalu",
                        key="carregar_produtos_magalu_api",
                    ):
                        try:
                            conector_produtos = MagaluMarketplace()

                            credenciais_ok = (
                                conector_produtos
                                .carregar_credenciais_banco()
                            )

                            if not credenciais_ok:
                                st.warning(
                                    "Nenhuma credencial válida "
                                    "do Magalu foi encontrada."
                                )

                            else:
                                with st.spinner(
                                    "Buscando produtos no Magalu..."
                                ):
                                    resposta = (
                                        conector_produtos
                                        .listar_pedidos()
                                    )

                                produtos_api = {}

                                for pedido in (
                                    resposta.get(
                                        "results",
                                        []
                                    )
                                    or []
                                ):
                                    pedido_codigo = str(
                                        pedido.get(
                                            "code"
                                        )
                                        or ""
                                    ).strip()

                                    for entrega in (
                                        pedido.get(
                                            "deliveries",
                                            []
                                        )
                                        or []
                                    ):
                                        for item in (
                                            entrega.get(
                                                "items",
                                                []
                                            )
                                            or []
                                        ):
                                            info = (
                                                item.get(
                                                    "info"
                                                )
                                                or {}
                                            )

                                            sku = str(
                                                info.get(
                                                    "sku"
                                                )
                                                or ""
                                            ).strip()

                                            if not sku:
                                                continue

                                            nome = str(
                                                info.get(
                                                    "name"
                                                )
                                                or info.get(
                                                    "description"
                                                )
                                                or "Produto sem nome"
                                            ).strip()

                                            marca = str(
                                                info.get(
                                                    "brand"
                                                )
                                                or ""
                                            ).strip()

                                            quantidade = float(
                                                item.get(
                                                    "quantity",
                                                    0
                                                )
                                                or 0
                                            )

                                            preco_info = (
                                                item.get(
                                                    "unit_price"
                                                )
                                                or {}
                                            )

                                            normalizador = float(
                                                preco_info.get(
                                                    "normalizer",
                                                    100
                                                )
                                                or 100
                                            )

                                            valor_bruto = float(
                                                preco_info.get(
                                                    "value",
                                                    0
                                                )
                                                or 0
                                            )

                                            if normalizador == 0:
                                                normalizador = 100

                                            valor_unitario = (
                                                valor_bruto
                                                / normalizador
                                            )

                                            if sku not in produtos_api:
                                                produtos_api[sku] = {
                                                    "sku": sku,
                                                    "nome": nome,
                                                    "marca": marca,
                                                    "quantidade": 0,
                                                    "valor_unitario": (
                                                        valor_unitario
                                                    ),
                                                    "pedidos": [],
                                                }

                                            produtos_api[
                                                sku
                                            ][
                                                "quantidade"
                                            ] += quantidade

                                            if (
                                                pedido_codigo
                                                and pedido_codigo
                                                not in produtos_api[
                                                    sku
                                                ][
                                                    "pedidos"
                                                ]
                                            ):
                                                produtos_api[
                                                    sku
                                                ][
                                                    "pedidos"
                                                ].append(
                                                    pedido_codigo
                                                )

                                st.session_state[
                                    "magalu_produtos_api"
                                ] = produtos_api

                                st.success(
                                    f"{len(produtos_api)} SKU(s) "
                                    "encontrado(s) nos pedidos."
                                )

                        except Exception as erro:
                            st.error(
                                "Não foi possível carregar "
                                "os produtos do Magalu."
                            )
                            st.exception(
                                erro
                            )

                    produtos_api = (
                        st.session_state.get(
                            "magalu_produtos_api",
                            {}
                        )
                        or {}
                    )

                    if produtos_api:
                        opcoes_sku = list(
                            produtos_api.keys()
                        )

                        sku_selecionado = st.selectbox(
                            "Produto encontrado no Magalu",
                            options=opcoes_sku,
                            index=None,
                            placeholder=(
                                "Selecione um SKU do Magalu"
                            ),
                            format_func=lambda sku: (
                                f"{produtos_api[sku]['nome']} "
                                f"| SKU: {sku}"
                            ),
                            key="magalu_sku_vinculo",
                        )

                        if sku_selecionado:
                            dados_produto_api = (
                                produtos_api[
                                    sku_selecionado
                                ]
                            )

                            st.write(
                                "**Produto Magalu:** "
                                f"{dados_produto_api['nome']}"
                            )

                            if dados_produto_api["marca"]:
                                st.write(
                                    "**Marca:** "
                                    f"{dados_produto_api['marca']}"
                                )

                            st.write(
                                "**SKU Magalu:** "
                                f"{sku_selecionado}"
                            )

                            st.write(
                                "**Preço encontrado:** "
                                f"{formatar_brl(
                                    dados_produto_api[
                                        'valor_unitario'
                                    ]
                                )}"
                            )

                            st.write(
                                "**Pedidos encontrados:** "
                                + ", ".join(
                                    dados_produto_api[
                                        "pedidos"
                                    ]
                                )
                            )

                            vinculo_atual = (
                                buscar_vinculo_produto_marketplace(
                                    canal_id=canal_id,
                                    sku_marketplace=(
                                        sku_selecionado
                                    ),
                                )
                            )

                            if vinculo_atual:
                                st.success(
                                    "Este SKU já está vinculado a: "
                                    f"{vinculo_atual[
                                        'produto_nome'
                                    ]}"
                                )

                            produtos_erp = (
                                listar_produtos_marketplace()
                            )

                            if produtos_erp.empty:
                                st.warning(
                                    "Nenhum produto disponível "
                                    "no ERP."
                                )

                            else:
                                mapa_produtos_erp = {}

                                for _, produto in (
                                    produtos_erp.iterrows()
                                ):
                                    produto_id = int(
                                        produto["id"]
                                    )

                                    nome_produto = str(
                                        produto["nome"]
                                    )

                                    codigo_barras = str(
                                        produto.get(
                                            "codigo_barras"
                                        )
                                        or ""
                                    ).strip()

                                    texto = (
                                        f"{produto_id} - "
                                        f"{nome_produto}"
                                    )

                                    if codigo_barras:
                                        texto += (
                                            " | Código: "
                                            f"{codigo_barras}"
                                        )

                                    mapa_produtos_erp[
                                        produto_id
                                    ] = texto

                                produto_erp_id = st.selectbox(
                                    "Produto correspondente no ERP",
                                    options=list(
                                        mapa_produtos_erp.keys()
                                    ),
                                    index=None,
                                    placeholder=(
                                        "Selecione o produto correto"
                                    ),
                                    format_func=lambda produto_id: (
                                        mapa_produtos_erp[
                                            produto_id
                                        ]
                                    ),
                                    key=(
                                        "magalu_produto_erp_vinculo"
                                    ),
                                )

                                if st.button(
                                    "Salvar vínculo do produto",
                                    type="primary",
                                    key="salvar_vinculo_magalu",
                                ):
                                    if produto_erp_id is None:
                                        st.warning(
                                            "Selecione primeiro "
                                            "o produto do ERP."
                                        )

                                    else:
                                        try:
                                            resultado_vinculo = (
                                                salvar_vinculo_produto_marketplace(
                                                    canal_id=canal_id,
                                                    produto_id=(
                                                        produto_erp_id
                                                    ),
                                                    sku_marketplace=(
                                                        sku_selecionado
                                                    ),
                                                    codigo_anuncio=None,
                                                    ativo=True,
                                                )
                                            )

                                            if resultado_vinculo.get(
                                                "sucesso"
                                            ):
                                                st.success(
                                                    "Produto vinculado "
                                                    "com sucesso."
                                                )
                                                st.rerun()

                                        except Exception as erro:
                                            st.error(
                                                "Não foi possível salvar "
                                                "o vínculo do produto."
                                            )
                                            st.exception(
                                                erro
                                            )

                    vinculos_magalu = (
                        listar_vinculos_produtos_marketplace(
                            canal_id=canal_id
                        )
                    )

                    if not vinculos_magalu.empty:
                        st.markdown(
                            "#### ✅ Produtos já vinculados"
                        )

                        st.dataframe(
                            vinculos_magalu[
                                [
                                    "produto",
                                    "sku_marketplace",
                                    "codigo_barras",
                                    "ativo",
                                ]
                            ],
                            use_container_width=True,
                            hide_index=True,
                        )

            except Exception as erro:
                st.error(
                    "Não foi possível preparar a "
                    "integração com o Magalu."
                )

                st.exception(
                    erro
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