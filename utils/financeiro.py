# utils/financeiro.py


# ==================================================
# LUCRO REAL POR PRODUTO
# ==================================================
def calcular_lucro_real(preco_venda, custo):

    try:
        preco_venda = float(preco_venda or 0)
        custo = float(custo or 0)

        return preco_venda - custo

    except:
        return 0.0


# ==================================================
# MARGEM REAL (%)
# ==================================================
def calcular_margem_real(preco_venda, custo):

    try:
        preco_venda = float(preco_venda or 0)
        custo = float(custo or 0)

        if preco_venda <= 0:
            return 0.0

        return ((preco_venda - custo) / preco_venda) * 100

    except:
        return 0.0


# ==================================================
# VALOR TOTAL DE ESTOQUE (CUSTO)
# ==================================================
def calcular_valor_estoque(df):

    try:
        total = 0.0

        for _, row in df.iterrows():
            custo = float(row.get("custo", 0) or 0)
            estoque = float(row.get("estoque", 0) or 0)

            total += custo * estoque

        return total

    except:
        return 0.0


# ==================================================
# VALOR TOTAL DE VENDA (ESTOQUE A PREÇO VENDA)
# ==================================================
def calcular_valor_venda_estoque(df):

    try:
        total = 0.0

        for _, row in df.iterrows():
            preco = float(row.get("preco", 0) or 0)
            estoque = float(row.get("estoque", 0) or 0)

            total += preco * estoque

        return total

    except:
        return 0.0


# ==================================================
# LUCRO POTENCIAL DO ESTOQUE
# ==================================================
def calcular_lucro_estoque(df):

    try:
        total = 0.0

        for _, row in df.iterrows():
            preco = float(row.get("preco", 0) or 0)
            custo = float(row.get("custo", 0) or 0)
            estoque = float(row.get("estoque", 0) or 0)

            lucro_unitario = preco - custo

            total += lucro_unitario * estoque

        return total

    except:
        return 0.0


# ==================================================
# CLASSIFICAÇÃO SIMPLES DE MARGEM
# ==================================================
def classificar_margem(margem):

    try:
        margem = float(margem or 0)

        if margem >= 30:
            return "🔥 Alta"
        elif margem >= 15:
            return "⚠️ Média"
        else:
            return "❌ Baixa"

    except:
        return "❌ Indefinida"