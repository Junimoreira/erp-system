from decimal import Decimal, InvalidOperation

from services.fiscal.perfil_fiscal_saida import (
    montar_perfil_fiscal_saida
)


# ============================================================
# VALIDADOR FISCAL DE VENDA
#
# RESPONSABILIDADE:
# - Validar cada produto da venda
# - Montar o perfil fiscal de cada item
# - Consolidar erros e avisos
# - Validar modelo NF-e / NFC-e
# - Preservar valores comerciais do item
# - Transportar PIS / COFINS do perfil fiscal
# - Informar se a venda está pronta para emissão
#
# IMPORTANTE:
# Esta versão NÃO:
# - altera a venda
# - altera estoque
# - altera produtos
# - gera XML
# - transmite documento à SEFAZ
# ============================================================


# ============================================================
# NORMALIZAR ID DO PRODUTO
# ============================================================
def _normalizar_produto_id(
    valor
):

    if valor is None:
        return None

    try:

        return int(
            valor
        )

    except (
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# NORMALIZAR MODELO
# ============================================================
def _normalizar_modelo(
    modelo
):

    if modelo is None:
        return None

    try:

        modelo = int(
            modelo
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    if modelo not in (
        55,
        65
    ):

        return None

    return modelo


# ============================================================
# EXTRAIR PRODUTO ID DO ITEM
# ============================================================
def _extrair_produto_id(
    item
):

    produto_id = (
        item.get(
            "produto_id"
        )
    )

    if produto_id is None:

        produto_id = (
            item.get(
                "id_produto"
            )
        )

    if produto_id is None:

        produto = item.get(
            "produto"
        )

        if isinstance(
            produto,
            dict
        ):

            produto_id = (
                produto.get(
                    "id"
                )
            )

    return _normalizar_produto_id(
        produto_id
    )


# ============================================================
# EXTRAIR QUANTIDADE
# ============================================================
def _extrair_quantidade(
    item
):

    quantidade = item.get(
        "quantidade",
        1
    )

    try:

        return float(
            quantidade
        )

    except (
        TypeError,
        ValueError
    ):

        return 0


# ============================================================
# NORMALIZAR VALOR MONETÁRIO
# ============================================================
def _extrair_valor_monetario(
    valor
):

    if valor is None:
        return None

    try:

        return Decimal(
            str(
                valor
            )
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError
    ):

        return None


# ============================================================
# VALIDAR ITEM DA VENDA
# ============================================================
def validar_item_venda_fiscal(
    item,
    uf_destino,
    modelo=None
):

    produto_id = (
        _extrair_produto_id(
            item
        )
    )

    quantidade = (
        _extrair_quantidade(
            item
        )
    )

    preco_unitario = (
        _extrair_valor_monetario(
            item.get(
                "preco_unitario"
            )
        )
    )

    subtotal = (
        _extrair_valor_monetario(
            item.get(
                "subtotal"
            )
        )
    )

    modelo_normalizado = _normalizar_modelo(
        modelo
    )

    erros = []
    avisos = []

    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------
    if (
        modelo is not None
        and
        modelo_normalizado is None
    ):

        erros.append(
            "Modelo fiscal inválido. Use 55 ou 65."
        )

    # --------------------------------------------------------
    # PRODUTO
    # --------------------------------------------------------
    if produto_id is None:

        return {
            "produto_id": None,
            "produto_nome": None,
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "subtotal": subtotal,
            "modelo": modelo_normalizado,
            "pode_emitir": False,
            "perfil_fiscal": None,
            "erros": [
                (
                    "Item da venda sem produto_id "
                    "válido."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # QUANTIDADE
    # --------------------------------------------------------
    if quantidade <= 0:

        erros.append(
            (
                "Quantidade do item deve ser "
                "maior que zero."
            )
        )

    # --------------------------------------------------------
    # PREÇO UNITÁRIO
    # --------------------------------------------------------
    if preco_unitario is None:

        avisos.append(
            (
                "Preço unitário do item não foi "
                "informado ao validador fiscal."
            )
        )

    elif preco_unitario < 0:

        erros.append(
            (
                "Preço unitário do item não pode "
                "ser negativo."
            )
        )

    # --------------------------------------------------------
    # SUBTOTAL
    # --------------------------------------------------------
    if subtotal is None:

        avisos.append(
            (
                "Subtotal do item não foi informado "
                "ao validador fiscal."
            )
        )

    elif subtotal < 0:

        erros.append(
            (
                "Subtotal do item não pode "
                "ser negativo."
            )
        )

    # --------------------------------------------------------
    # PERFIL FISCAL
    # --------------------------------------------------------
    perfil = (
        montar_perfil_fiscal_saida(
            produto_id=produto_id,
            uf_destino=uf_destino,
            modelo=modelo_normalizado
        )
    )

    if not perfil:

        erros.append(
            (
                "Não foi possível montar o "
                "perfil fiscal do produto."
            )
        )

        return {
            "produto_id": produto_id,
            "produto_nome": None,
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "subtotal": subtotal,
            "modelo": modelo_normalizado,
            "pode_emitir": False,
            "perfil_fiscal": None,
            "erros": erros,
            "avisos": avisos
        }

    # --------------------------------------------------------
    # ERROS DO PERFIL
    # --------------------------------------------------------
    for erro in perfil.get(
        "erros",
        []
    ):

        erros.append(
            erro
        )

    # --------------------------------------------------------
    # AVISOS DO PERFIL
    # --------------------------------------------------------
    for aviso in perfil.get(
        "avisos",
        []
    ):

        avisos.append(
            aviso
        )

    # --------------------------------------------------------
    # PERFIL NÃO APTO
    # --------------------------------------------------------
    if not perfil.get(
        "pode_emitir",
        False
    ):

        if not erros:

            erros.append(
                (
                    "Produto não está apto "
                    "para emissão fiscal."
                )
            )

    pode_emitir = (
        len(
            erros
        ) == 0
    )

    return {
        "produto_id":
            produto_id,

        "produto_nome":
            perfil.get(
                "produto_nome"
            ),

        "codigo_barras":
            perfil.get(
                "codigo_barras"
            ),

        # ----------------------------------------------------
        # DADOS COMERCIAIS
        # ----------------------------------------------------
        "quantidade":
            quantidade,

        "preco_unitario":
            preco_unitario,

        "subtotal":
            subtotal,

        # ----------------------------------------------------
        # MODELO / OPERAÇÃO
        # ----------------------------------------------------
        "modelo":
            modelo_normalizado,

        "operacao":
            perfil.get(
                "operacao"
            ),

        # ----------------------------------------------------
        # CLASSIFICAÇÃO FISCAL
        # ----------------------------------------------------
        "ncm":
            perfil.get(
                "ncm"
            ),

        "cest":
            perfil.get(
                "cest"
            ),

        "origem_mercadoria":
            perfil.get(
                "origem_mercadoria"
            ),

        # ----------------------------------------------------
        # ICMS
        # ----------------------------------------------------
        "perfil_icms":
            perfil.get(
                "perfil_icms"
            ),

        "cfop":
            perfil.get(
                "cfop"
            ),

        "csosn":
            perfil.get(
                "csosn"
            ),

        # ----------------------------------------------------
        # PIS / COFINS
        # ----------------------------------------------------
        "cst_pis":
            perfil.get(
                "cst_pis"
            ),

        "aliquota_pis":
            perfil.get(
                "aliquota_pis"
            ),

        "cst_cofins":
            perfil.get(
                "cst_cofins"
            ),

        "aliquota_cofins":
            perfil.get(
                "aliquota_cofins"
            ),

        # ----------------------------------------------------
        # IBS / CBS
        # ----------------------------------------------------
        "cst_ibs_cbs":
            perfil.get(
                "cst_ibs_cbs"
            ),

        "classificacao_tributaria":
            perfil.get(
                "classificacao_tributaria"
            ),

        "ibs_cbs_validado":
            perfil.get(
                "ibs_cbs_validado"
            ),

        "ibs_cbs_vigente":
            perfil.get(
                "ibs_cbs_vigente"
            ),

        "ibs_cbs_permitido_modelo":
            perfil.get(
                "ibs_cbs_permitido_modelo"
            ),

        "ibs_cbs_ind_nfe":
            perfil.get(
                "ibs_cbs_ind_nfe"
            ),

        "ibs_cbs_ind_nfce":
            perfil.get(
                "ibs_cbs_ind_nfce"
            ),

        "ibs_cbs_descricao":
            perfil.get(
                "ibs_cbs_descricao"
            ),

        # ----------------------------------------------------
        # CONTROLE
        # ----------------------------------------------------
        "fiscal_revisado":
            perfil.get(
                "fiscal_revisado"
            ),

        "fiscal_confianca":
            perfil.get(
                "fiscal_confianca"
            ),

        "pode_emitir":
            pode_emitir,

        "perfil_fiscal":
            perfil,

        "erros":
            erros,

        "avisos":
            avisos
    }


# ============================================================
# VALIDAR LISTA DE ITENS
# ============================================================
def validar_itens_venda_fiscal(
    itens,
    uf_destino,
    modelo=None
):

    if itens is None:

        itens = []

    modelo_normalizado = _normalizar_modelo(
        modelo
    )

    resultados = []

    for numero_item, item in enumerate(
        itens,
        start=1
    ):

        resultado = (
            validar_item_venda_fiscal(
                item=item,
                uf_destino=uf_destino,
                modelo=modelo_normalizado
            )
        )

        resultado[
            "numero_item"
        ] = numero_item

        resultados.append(
            resultado
        )

    # --------------------------------------------------------
    # TOTAIS
    # --------------------------------------------------------
    total_itens = len(
        resultados
    )

    itens_liberados = sum(
        1
        for item in resultados
        if item.get(
            "pode_emitir"
        )
    )

    itens_bloqueados = (
        total_itens
        -
        itens_liberados
    )

    total_erros = sum(
        len(
            item.get(
                "erros",
                []
            )
        )
        for item in resultados
    )

    total_avisos = sum(
        len(
            item.get(
                "avisos",
                []
            )
        )
        for item in resultados
    )

    erros_venda = []

    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------
    if (
        modelo is not None
        and
        modelo_normalizado is None
    ):

        erros_venda.append(
            "Modelo fiscal inválido. Use 55 ou 65."
        )

    # --------------------------------------------------------
    # VENDA SEM ITENS
    # --------------------------------------------------------
    if total_itens == 0:

        erros_venda.append(
            "Venda sem itens."
        )

    pode_emitir = (
        total_itens > 0
        and
        itens_bloqueados == 0
        and
        len(
            erros_venda
        ) == 0
    )

    return {
        "pode_emitir":
            pode_emitir,

        "modelo":
            modelo_normalizado,

        "uf_destino":
            uf_destino,

        "quantidade_itens":
            total_itens,

        "itens_liberados":
            itens_liberados,

        "itens_bloqueados":
            itens_bloqueados,

        "total_erros":
            total_erros
            +
            len(
                erros_venda
            ),

        "total_avisos":
            total_avisos,

        "erros_venda":
            erros_venda,

        "itens":
            resultados
    }


# ============================================================
# VALIDAR VENDA
#
# modelo:
# - None -> compatibilidade com chamadas antigas
# - 55   -> NF-e
# - 65   -> NFC-e
# ============================================================
def validar_venda_fiscal(
    venda,
    uf_destino,
    modelo=None
):

    if not isinstance(
        venda,
        dict
    ):

        return {
            "sucesso": False,
            "pode_emitir": False,
            "mensagem":
                "Venda inválida.",
            "modelo":
                _normalizar_modelo(
                    modelo
                ),
            "itens": []
        }

    venda_id = venda.get(
        "id"
    )

    itens = venda.get(
        "itens",
        []
    )

    resultado = (
        validar_itens_venda_fiscal(
            itens=itens,
            uf_destino=uf_destino,
            modelo=modelo
        )
    )

    resultado[
        "sucesso"
    ] = True

    resultado[
        "venda_id"
    ] = venda_id

    return resultado