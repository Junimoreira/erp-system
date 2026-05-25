from database.configuracoes_db import buscar_configuracoes_financeiras


# ==================================================
# MOTOR CENTRAL DE PRECIFICAÇÃO ERP
# ==================================================
def calcular_preco_venda(
    custo,
    imposto=None,
    frete=None,
    cartao=None,
    margem=None,
    margem_minima=None,
    preco_minimo=None
):

    if custo is None or custo <= 0:
        return 0.0

    config = buscar_configuracoes_financeiras()

    if not config:
        return round(float(custo) * 2, 2)

    # =========================
    # CONFIGURAÇÕES GLOBAIS
    # =========================
    imposto = float(imposto if imposto is not None else config.get("imposto_padrao", 0)) / 100
    frete = float(frete if frete is not None else config.get("frete_padrao", 0)) / 100
    cartao = float(cartao if cartao is not None else config.get("taxa_cartao_padrao", 0)) / 100
    margem = float(margem if margem is not None else config.get("margem_lucro_padrao", 0)) / 100

    total_custos = imposto + frete + cartao + margem

    # proteção matemática
    if total_custos >= 1:
        return round(float(custo) * 2, 2)

    preco = float(custo) / (1 - total_custos)

    # =========================
    # REGRAS DE SEGURANÇA
    # =========================

    if margem_minima:
        preco_minimo_margem = custo * (1 + margem_minima / 100)
        if preco < preco_minimo_margem:
            preco = preco_minimo_margem

    if preco_minimo:
        if preco < preco_minimo:
            preco = preco_minimo

    return round(preco, 2)