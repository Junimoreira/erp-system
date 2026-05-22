from database.configuracoes_db import buscar_configuracoes_financeiras


# ==================================================
# CALCULAR PREÇO DE VENDA (ERP PROFISSIONAL)
# ==================================================
def calcular_preco_venda(custo, imposto=None, frete=None, cartao=None, margem=None):

    if custo is None or custo <= 0:
        return 0.0

    config = buscar_configuracoes_financeiras()

    if not config:
        return round(float(custo), 2)

    # ================================
    # PEGA CONFIG OU PARAMETROS
    # ================================
    imposto = float(imposto if imposto is not None else config.get("imposto_padrao", 0)) / 100
    frete = float(frete if frete is not None else config.get("frete_padrao", 0)) / 100
    cartao = float(cartao if cartao is not None else config.get("taxa_cartao_padrao", 0)) / 100
    margem = float(margem if margem is not None else config.get("margem_lucro_padrao", 0)) / 100

    total_percentual = imposto + frete + cartao + margem

    # proteção contra erro matemático
    if total_percentual >= 1:
        return round(float(custo) * 2, 2)

    preco = float(custo) / (1 - total_percentual)

    return round(preco, 2)


# ==================================================
# MARGEM PADRÃO
# ==================================================
def buscar_margem_padrao():

    config = buscar_configuracoes_financeiras()

    if not config:
        return 0.0

    try:
        return float(config.get("margem_lucro_padrao", 0))
    except:
        return 0.0