from database.configuracoes_db import (
    buscar_configuracoes_financeiras
)


# ==================================================
# MOTOR CENTRAL DE PRECIFICAÇÃO ERP
# ==================================================
def calcular_preco_venda(
    custo,
    imposto=None,
    frete=None,
    cartao=None,
    margem=None,
    desconto_maximo=None
):

    try:

        custo = float(custo)

    except:
        return 0.0

    # ==================================================
    # VALIDAÇÃO
    # ==================================================
    if custo <= 0:
        return 0.0

    # ==================================================
    # CONFIGURAÇÕES ERP
    # ==================================================
    config = buscar_configuracoes_financeiras()

    if not config:
        config = {}

    # ==================================================
    # PERCENTUAIS
    # ==================================================
    imposto = float(
        imposto
        if imposto is not None
        else config.get("imposto_padrao", 0)
    )

    frete = float(
        frete
        if frete is not None
        else config.get("frete_padrao", 0)
    )

    cartao = float(
        cartao
        if cartao is not None
        else config.get("taxa_cartao_padrao", 0)
    )

    margem = float(
        margem
        if margem is not None
        else config.get("margem_lucro_padrao", 30)
    )

    desconto_maximo = float(
        desconto_maximo
        if desconto_maximo is not None
        else config.get("desconto_maximo", 0)
    )

    # ==================================================
    # CONVERTE %
    # ==================================================
    imposto = imposto / 100
    frete = frete / 100
    cartao = cartao / 100
    margem = margem / 100
    desconto_maximo = desconto_maximo / 100

    # ==================================================
    # SOMA TOTAL DOS PERCENTUAIS
    # ==================================================
    total_percentual = (
        imposto +
        frete +
        cartao +
        margem
    )

    # ==================================================
    # PROTEÇÃO MATEMÁTICA
    # ==================================================
    if total_percentual >= 1:

        return round(custo * 2, 2)

    # ==================================================
    # MARKUP DIVISOR
    # FÓRMULA PROFISSIONAL ERP
    # ==================================================
    divisor = 1 - total_percentual

    preco_base = custo / divisor

    # ==================================================
    # DESCONTO MÁXIMO
    # ==================================================
    if desconto_maximo > 0:

        preco_final = preco_base * (
            1 - desconto_maximo
        )

    else:

        preco_final = preco_base

    # ==================================================
    # RETORNO FINAL
    # ==================================================
    return round(preco_final, 2)


# ==================================================
# MARGEM PADRÃO
# ==================================================
def buscar_margem_padrao():

    config = buscar_configuracoes_financeiras()

    if not config:
        return 30.0

    try:

        return float(
            config.get(
                "margem_lucro_padrao",
                30
            )
        )

    except:

        return 30.0