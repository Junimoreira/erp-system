import re


def detectar_conversao_por_descricao(descricao):

    if not descricao:
        return {
            "detectado": False,
            "tipo_compra": "UNIDADE",
            "unidade_compra": "UNIDADE",
            "unidade_estoque": "UNIDADE",
            "fator_conversao": 1.0,
            "observacao": "Nenhuma conversão detectada."
        }

    texto = str(descricao).upper().strip()

    padroes = [
        (r"KIT\.?\s*C/?\s*(\d+)", "KIT"),
        (r"CX\.?\s*C/?\s*(\d+)", "CAIXA"),
        (r"CAIXA\s*C/?\s*(\d+)", "CAIXA"),
        (r"PACOTE\s*C/?\s*(\d+)", "PACOTE"),
        (r"PCT\.?\s*C/?\s*(\d+)", "PACOTE"),
        (r"FARDO\s*C/?\s*(\d+)", "FARDO"),
        (r"DISPLAY\s*C/?\s*(\d+)", "DISPLAY"),
        (r"EMB\.?\s*C/?\s*(\d+)", "EMBALAGEM"),
        (r"C/?\s*(\d+)\s*UN", "UNIDADE"),
        (r"COM\s*(\d+)\s*UN", "UNIDADE"),
        (r"C/?\s*(\d+)", "UNIDADE"),
    ]

    for padrao, tipo in padroes:
        encontrado = re.search(padrao, texto)

        if encontrado:
            fator = float(encontrado.group(1))

            if fator > 1:
                return {
                    "detectado": True,
                    "tipo_compra": tipo,
                    "unidade_compra": tipo,
                    "unidade_estoque": "UNIDADE",
                    "fator_conversao": fator,
                    "observacao": f"Conversão detectada automaticamente na descrição: {tipo} com {int(fator)} unidades."
                }

    return {
        "detectado": False,
        "tipo_compra": "UNIDADE",
        "unidade_compra": "UNIDADE",
        "unidade_estoque": "UNIDADE",
        "fator_conversao": 1.0,
        "observacao": "Nenhuma conversão detectada."
    }


def aplicar_conversao_produto(
    quantidade_xml,
    custo_xml,
    subtotal_xml,
    conversao
):

    fator = float(conversao.get("fator_conversao", 1) or 1)

    if fator <= 0:
        fator = 1

    quantidade_estoque = float(quantidade_xml) * fator
    custo_unitario_estoque = float(custo_xml) / fator
    subtotal_convertido = float(subtotal_xml)

    return {
        "fator_conversao": fator,
        "quantidade_xml": float(quantidade_xml),
        "custo_xml": float(custo_xml),
        "subtotal_xml": float(subtotal_xml),
        "quantidade_estoque": quantidade_estoque,
        "custo_unitario_estoque": custo_unitario_estoque,
        "subtotal_convertido": subtotal_convertido,
        "tipo_compra": conversao.get("tipo_compra", "UNIDADE"),
        "unidade_compra": conversao.get("unidade_compra", "UNIDADE"),
        "unidade_estoque": conversao.get("unidade_estoque", "UNIDADE")
    }


def salvar_conversao_automatica(
    cursor,
    produto_id,
    codigo_barras,
    codigo_fornecedor,
    conversao_detectada
):

    if not conversao_detectada.get("detectado"):
        return False

    cursor.execute("""
        INSERT INTO conversao_produtos_xml (
            produto_id,
            codigo_barras,
            codigo_fornecedor,
            tipo_compra,
            unidade_compra,
            unidade_estoque,
            fator_conversao,
            ativo,
            observacoes,
            atualizado_em
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, true, %s, CURRENT_TIMESTAMP)
    """, (
        produto_id,
        codigo_barras,
        codigo_fornecedor,
        conversao_detectada["tipo_compra"],
        conversao_detectada["unidade_compra"],
        conversao_detectada["unidade_estoque"],
        conversao_detectada["fator_conversao"],
        conversao_detectada["observacao"]
    ))

    return True