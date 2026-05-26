def calcular_preco_venda(custo, imposto, frete, taxa_cartao, margem):

    custo = float(custo)

    total_percentual = (
        float(imposto)
        + float(frete)
        + float(taxa_cartao)
        + float(margem)
    )

    if total_percentual >= 1:
        raise ValueError("Percentual total não pode ser 100% ou mais.")

    preco = custo / (1 - total_percentual)

    return round(preco, 2)