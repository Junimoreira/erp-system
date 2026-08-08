import re


# ==========================================================
# CONVERSÃO PADRÃO
# ==========================================================

def conversao_padrao(observacao="Nenhuma conversão detectada."):

    return {
        "detectado": False,
        "tipo_compra": "UNIDADE",
        "unidade_compra": "UNIDADE",
        "unidade_estoque": "UNIDADE",
        "fator_conversao": 1.0,
        "observacao": observacao
    }


# ==========================================================
# DETECTAR CONVERSÃO PELA DESCRIÇÃO
# ==========================================================

def detectar_conversao_por_descricao(descricao):

    if not descricao:
        return conversao_padrao()

    texto = str(descricao).upper().strip()

    # ======================================================
    # IMPORTANTE
    #
    # Somente detectamos conversão quando existir uma
    # indicação CLARA de embalagem comercial.
    #
    # Exemplos aceitos:
    #
    # CX C/12
    # CAIXA C/12
    # PCT C/10
    # PCT.C/10
    # PACOTE C/10
    # FARDO C/6
    # DISPLAY C/24
    # KIT C/4
    # EMB C/20
    #
    # NÃO interpretar como conversão:
    #
    # 52PCS
    # 1000PCS
    # ABC 52PCS
    # 40 PEÇAS
    # 500 FOLHAS
    # 120 PALAVRAS
    # 24X12CM
    # ======================================================

    padroes = [

        # KIT C/10
        (
            r"\bKIT\.?\s*C\s*/\s*(\d+)\b",
            "KIT"
        ),

        # KIT COM 10
        (
            r"\bKIT\.?\s+COM\s+(\d+)\b",
            "KIT"
        ),

        # CX C/12
        (
            r"\bCX\.?\s*C\s*/\s*(\d+)\b",
            "CAIXA"
        ),

        # CX COM 12
        (
            r"\bCX\.?\s+COM\s+(\d+)\b",
            "CAIXA"
        ),

        # CAIXA C/12
        (
            r"\bCAIXA\s*C\s*/\s*(\d+)\b",
            "CAIXA"
        ),

        # CAIXA COM 12
        (
            r"\bCAIXA\s+COM\s+(\d+)\b",
            "CAIXA"
        ),

        # PCT C/10 ou PCT.C/10
        (
            r"\bPCT\.?\s*C\s*/\s*(\d+)\b",
            "PACOTE"
        ),

        # PCT COM 10
        (
            r"\bPCT\.?\s+COM\s+(\d+)\b",
            "PACOTE"
        ),

        # PACOTE C/10
        (
            r"\bPACOTE\s*C\s*/\s*(\d+)\b",
            "PACOTE"
        ),

        # PACOTE COM 10
        (
            r"\bPACOTE\s+COM\s+(\d+)\b",
            "PACOTE"
        ),

        # FARDO C/6
        (
            r"\bFARDO\s*C\s*/\s*(\d+)\b",
            "FARDO"
        ),

        # FARDO COM 6
        (
            r"\bFARDO\s+COM\s+(\d+)\b",
            "FARDO"
        ),

        # DISPLAY C/24
        (
            r"\bDISPLAY\s*C\s*/\s*(\d+)\b",
            "DISPLAY"
        ),

        # DISPLAY COM 24
        (
            r"\bDISPLAY\s+COM\s+(\d+)\b",
            "DISPLAY"
        ),

        # EMB C/20
        (
            r"\bEMB\.?\s*C\s*/\s*(\d+)\b",
            "EMBALAGEM"
        ),

        # EMB COM 20
        (
            r"\bEMB\.?\s+COM\s+(\d+)\b",
            "EMBALAGEM"
        ),

        # EMBALAGEM C/20
        (
            r"\bEMBALAGEM\s*C\s*/\s*(\d+)\b",
            "EMBALAGEM"
        ),

        # EMBALAGEM COM 20
        (
            r"\bEMBALAGEM\s+COM\s+(\d+)\b",
            "EMBALAGEM"
        ),
    ]

    for padrao, tipo in padroes:

        encontrado = re.search(padrao, texto)

        if not encontrado:
            continue

        try:
            fator = float(encontrado.group(1))

        except (TypeError, ValueError):
            continue

        if fator <= 1:
            continue

        return {
            "detectado": True,
            "tipo_compra": tipo,
            "unidade_compra": tipo,
            "unidade_estoque": "UNIDADE",
            "fator_conversao": fator,
            "observacao": (
                f"Conversão detectada automaticamente na descrição: "
                f"{tipo} com {int(fator)} unidades."
            )
        }

    return conversao_padrao()


# ==========================================================
# APLICAR CONVERSÃO
# ==========================================================

def aplicar_conversao_produto(
    quantidade_xml,
    custo_xml,
    subtotal_xml,
    conversao
):

    conversao = conversao or {}

    try:
        fator = float(
            conversao.get("fator_conversao", 1) or 1
        )
    except (TypeError, ValueError):
        fator = 1.0

    if fator <= 0:
        fator = 1.0

    try:
        quantidade_xml = float(quantidade_xml or 0)
    except (TypeError, ValueError):
        quantidade_xml = 0.0

    try:
        custo_xml = float(custo_xml or 0)
    except (TypeError, ValueError):
        custo_xml = 0.0

    try:
        subtotal_xml = float(subtotal_xml or 0)
    except (TypeError, ValueError):
        subtotal_xml = quantidade_xml * custo_xml

    quantidade_estoque = quantidade_xml * fator

    custo_unitario_estoque = (
        custo_xml / fator
        if fator > 0
        else custo_xml
    )

    return {
        "fator_conversao": fator,
        "quantidade_xml": quantidade_xml,
        "custo_xml": custo_xml,
        "subtotal_xml": subtotal_xml,
        "quantidade_estoque": quantidade_estoque,
        "custo_unitario_estoque": custo_unitario_estoque,
        "subtotal_convertido": subtotal_xml,
        "tipo_compra": conversao.get(
            "tipo_compra",
            "UNIDADE"
        ),
        "unidade_compra": conversao.get(
            "unidade_compra",
            "UNIDADE"
        ),
        "unidade_estoque": conversao.get(
            "unidade_estoque",
            "UNIDADE"
        )
    }


# ==========================================================
# SALVAR CONVERSÃO AUTOMÁTICA
# ==========================================================

def salvar_conversao_automatica(
    cursor,
    produto_id,
    codigo_barras,
    codigo_fornecedor,
    conversao_detectada
):

    if not conversao_detectada:
        return False

    if not conversao_detectada.get("detectado"):
        return False

    try:
        fator = float(
            conversao_detectada.get(
                "fator_conversao",
                1
            ) or 1
        )
    except (TypeError, ValueError):
        fator = 1.0

    if fator <= 1:
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
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            true,
            %s,
            CURRENT_TIMESTAMP
        )
    """, (
        produto_id,
        codigo_barras,
        codigo_fornecedor,
        conversao_detectada["tipo_compra"],
        conversao_detectada["unidade_compra"],
        conversao_detectada["unidade_estoque"],
        fator,
        conversao_detectada["observacao"]
    ))

    return True