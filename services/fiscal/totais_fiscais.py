from decimal import Decimal, InvalidOperation


# ============================================================
# TOTAIS FISCAIS
#
# RESPONSABILIDADE:
# - Conferir soma dos subtotais
# - Conferir valor total da venda
# - Conferir desconto
# - Conferir valor final
# - Conferir valor do pagamento
#
# IMPORTANTE:
# Esta etapa valida os totais comerciais do ERP.
# Ainda NÃO calcula o vNF definitivo do XML.
# ============================================================


CENTAVOS = Decimal("0.01")


# ============================================================
# NORMALIZAR DECIMAL
# ============================================================
def _decimal(
    valor
):

    if valor is None:
        return None

    try:

        return Decimal(
            str(
                valor
            )
        ).quantize(
            CENTAVOS
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# MONTAR / VALIDAR TOTAIS
# ============================================================
def montar_totais_fiscais(
    venda,
    resultado_pagamento
):

    erros = []
    avisos = []

    if not isinstance(
        venda,
        dict
    ):

        return {
            "sucesso": False,
            "totais": None,
            "erros": [
                "Venda inválida para cálculo dos totais."
            ],
            "avisos": []
        }

    itens = venda.get(
        "itens",
        []
    )

    if not itens:

        return {
            "sucesso": False,
            "totais": None,
            "erros": [
                "Venda sem itens para cálculo dos totais."
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # SOMAR SUBTOTAIS
    # --------------------------------------------------------
    soma_itens = Decimal("0.00")

    for numero_item, item in enumerate(
        itens,
        start=1
    ):

        subtotal = _decimal(
            item.get(
                "subtotal"
            )
        )

        if subtotal is None:

            erros.append(
                (
                    f"Item {numero_item} sem subtotal "
                    "válido."
                )
            )

            continue

        if subtotal < 0:

            erros.append(
                (
                    f"Item {numero_item} possui subtotal "
                    "negativo."
                )
            )

            continue

        soma_itens += subtotal

    soma_itens = soma_itens.quantize(
        CENTAVOS
    )

    # --------------------------------------------------------
    # VALORES DA VENDA
    # --------------------------------------------------------
    valor_total = _decimal(
        venda.get(
            "valor_total"
        )
    )

    desconto = _decimal(
        venda.get(
            "desconto"
        )
    )

    valor_final = _decimal(
        venda.get(
            "valor_final"
        )
    )

    if valor_total is None:

        erros.append(
            "Valor total da venda inválido."
        )

    if desconto is None:

        desconto = Decimal("0.00")

    if desconto < 0:

        erros.append(
            "Desconto não pode ser negativo."
        )

    if valor_final is None:

        erros.append(
            "Valor final da venda inválido."
        )

    # --------------------------------------------------------
    # CONFERIR SOMA DOS ITENS
    # --------------------------------------------------------
    if (
        valor_total is not None
        and
        soma_itens != valor_total
    ):

        erros.append(
            (
                "Soma dos subtotais dos itens difere "
                "do valor total da venda. "
                f"Itens: {soma_itens} | "
                f"Venda: {valor_total}"
            )
        )

    # --------------------------------------------------------
    # CONFERIR TOTAL - DESCONTO
    # --------------------------------------------------------
    valor_calculado = None

    if valor_total is not None:

        valor_calculado = (
            valor_total
            -
            desconto
        ).quantize(
            CENTAVOS
        )

        if (
            valor_final is not None
            and
            valor_calculado != valor_final
        ):

            erros.append(
                (
                    "Valor final da venda não confere "
                    "com total menos desconto. "
                    f"Calculado: {valor_calculado} | "
                    f"Venda: {valor_final}"
                )
            )

    # --------------------------------------------------------
    # PAGAMENTO
    # --------------------------------------------------------
    pagamento = (
        resultado_pagamento.get(
            "pagamento"
        )
        if isinstance(
            resultado_pagamento,
            dict
        )
        else None
    )

    valor_pagamento = None

    if pagamento:

        valor_pagamento = _decimal(
            pagamento.get(
                "valor"
            )
        )

    if valor_pagamento is None:

        erros.append(
            "Valor do pagamento não informado."
        )

    elif (
        valor_final is not None
        and
        valor_pagamento != valor_final
    ):

        erros.append(
            (
                "Valor do pagamento difere do valor "
                "final da venda. "
                f"Pagamento: {valor_pagamento} | "
                f"Venda: {valor_final}"
            )
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    return {
        "sucesso":
            len(
                erros
            ) == 0,

        "totais": {
            "soma_itens":
                soma_itens,

            "valor_total":
                valor_total,

            "desconto":
                desconto,

            "valor_calculado":
                valor_calculado,

            "valor_final":
                valor_final,

            "valor_pagamento":
                valor_pagamento,

            "diferenca_pagamento":
                (
                    (
                        valor_pagamento
                        -
                        valor_final
                    ).quantize(
                        CENTAVOS
                    )
                    if (
                        valor_pagamento is not None
                        and
                        valor_final is not None
                    )
                    else None
                )
        },

        "erros":
            erros,

        "avisos":
            avisos
    }