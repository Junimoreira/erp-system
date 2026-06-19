import xml.etree.ElementTree as ET


def _texto(elemento, caminho, ns):
    achado = elemento.find(caminho, ns)
    return achado.text.strip() if achado is not None and achado.text else ""


def _float(valor):
    try:
        return float(str(valor).replace(",", "."))
    except Exception:
        return 0.0


def ler_xml_nfe(arquivo):

    tree = ET.parse(arquivo)
    root = tree.getroot()

    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    inf_nfe = root.find(".//nfe:infNFe", ns)

    if inf_nfe is None:
        raise Exception("XML inválido ou não é uma NF-e.")

    emit = inf_nfe.find("nfe:emit", ns)
    total = inf_nfe.find("nfe:total/nfe:ICMSTot", ns)

    fornecedor = {
        "razao_social": _texto(emit, "nfe:xNome", ns),
        "nome_fantasia": _texto(emit, "nfe:xFant", ns),
        "cnpj": _texto(emit, "nfe:CNPJ", ns),
        "inscricao_estadual": _texto(emit, "nfe:IE", ns),
        "telefone": _texto(emit, "nfe:enderEmit/nfe:fone", ns),
        "email": "",
        "endereco": _texto(emit, "nfe:enderEmit/nfe:xLgr", ns),
        "numero": _texto(emit, "nfe:enderEmit/nfe:nro", ns),
        "bairro": _texto(emit, "nfe:enderEmit/nfe:xBairro", ns),
        "cidade": _texto(emit, "nfe:enderEmit/nfe:xMun", ns),
        "estado": _texto(emit, "nfe:enderEmit/nfe:UF", ns),
        "cep": _texto(emit, "nfe:enderEmit/nfe:CEP", ns),
        "contato_responsavel": "",
        "observacoes": "Fornecedor importado via XML NF-e"
    }

    produtos = []

    for det in inf_nfe.findall("nfe:det", ns):

        prod = det.find("nfe:prod", ns)

        codigo_barras = _texto(prod, "nfe:cEAN", ns)

        if codigo_barras.upper() == "SEM GTIN":
            codigo_barras = ""

        quantidade = _float(_texto(prod, "nfe:qCom", ns))
        valor_unitario = _float(_texto(prod, "nfe:vUnCom", ns))
        valor_total = _float(_texto(prod, "nfe:vProd", ns))

        produtos.append({
            "nome": _texto(prod, "nfe:xProd", ns),
            "codigo_barras": codigo_barras,
            "sku": _texto(prod, "nfe:cProd", ns),
            "referencia": _texto(prod, "nfe:cProd", ns),
            "marca": "",
            "categoria": "IMPORTADO XML",
            "ncm": _texto(prod, "nfe:NCM", ns),
            "cest": _texto(prod, "nfe:CEST", ns),
            "cfop_padrao": _texto(prod, "nfe:CFOP", ns),
            "unidade": _texto(prod, "nfe:uCom", ns),
            "custo": valor_unitario,
            "preco": valor_unitario,
            "quantidade": quantidade,
            "subtotal": valor_total,
            "margem_lucro": 0,
            "estoque_minimo": 0,
            "localizacao": "",
            "ativo": True,
            "observacoes": "Produto importado via XML NF-e"
        })

    return {
        "fornecedor": fornecedor,
        "produtos": produtos,
        "valor_total": _float(_texto(total, "nfe:vNF", ns)) if total is not None else 0
    }