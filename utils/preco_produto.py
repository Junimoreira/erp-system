from database.configuracoes_db import buscar_configuracoes_financeiras


def calcular_preco_venda(custo: float) -> float:
    """
    Calcula preço de venda automaticamente com base nas configurações financeiras.
    """

    config = buscar_configuracoes_financeiras()

    if config is None:
        # fallback padrão
        imposto = 0
        frete = 0
        taxa_cartao = 0
        margem = 30
    else:
        imposto = float(config["imposto_padrao"])
        frete = float(config["frete_padrao"])
        taxa_cartao = float(config["taxa_cartao_padrao"])
        margem = float(config["margem_lucro_padrao"])

    total_percentual = imposto + frete + taxa_cartao + margem

    preco_venda = custo * (1 + total_percentual / 100)

    return round(preco_venda, 2)