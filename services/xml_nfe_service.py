import xml.etree.ElementTree as ET


def limpar_numero(valor):
    if valor is None:
        return ""
    return "".join(filter(str.isdigit, str(valor)))


def texto_no(elemento, caminho, ns):
    achado = elemento.find(caminho, ns)
    return achado.text.strip() if achado is not None and achado.text else ""


def numero_float(valor):
    try:
        if valor is None or valor == "":
            return 0.0
        return float(str(valor).replace(",", "."))
    except Exception:
        return 0.0


def ler_xml_nfe(arquivo_xml):

    conteudo = arquivo_xml.read()

    root = ET.fromstring(conteudo)

    ns = {
        "nfe": "http://www.portalfiscal.inf.br/nfe"
    }

    inf_nfe = root.find(".//nfe:infNFe", ns)

    if inf_nfe is None:
        raise Exception("XML inválido: infNFe não encontrado.")

    chave_nfe = inf_nfe.attrib.get("Id", "").replace("NFe", "")

    ide = inf_nfe.find("nfe:ide", ns)
    emit = inf_nfe.find("nfe:emit", ns)
    total = inf_nfe.find(".//nfe:ICMSTot", ns)

    numero_nfe = texto_no(ide, "nfe:nNF", ns) if ide is not None else ""
    serie_nfe = texto_no(ide, "nfe:serie", ns) if ide is not None else ""
    data_emissao = texto_no(ide, "nfe:dhEmi", ns) if ide is not None else ""

    fornecedor = {
        "razao_social": texto_no(emit, "nfe:xNome", ns),
        "nome_fantasia": texto_no(emit, "nfe:xFant", ns),
        "cnpj": limpar_numero(texto_no(emit, "nfe:CNPJ", ns)),
        "inscricao_estadual": texto_no(emit, "nfe:IE", ns),
        "cidade": texto_no(emit, "nfe:enderEmit/nfe:xMun", ns),
        "estado": texto_no(emit, "nfe:enderEmit/nfe:UF", ns),
        "telefone": texto_no(emit, "nfe:enderEmit/nfe:fone", ns),
    }

    produtos = []

    for det in inf_nfe.findall("nfe:det", ns):

        prod = det.find("nfe:prod", ns)

        if prod is None:
            continue

        quantidade = numero_float(texto_no(prod, "nfe:qCom", ns))
        custo_unitario = numero_float(texto_no(prod, "nfe:vUnCom", ns))
        subtotal = numero_float(texto_no(prod, "nfe:vProd", ns))

        produtos.append({
            "codigo": texto_no(prod, "nfe:cProd", ns),
            "ean": texto_no(prod, "nfe:cEAN", ns),
            "nome": texto_no(prod, "nfe:xProd", ns),
            "ncm": texto_no(prod, "nfe:NCM", ns),
            "cfop": texto_no(prod, "nfe:CFOP", ns),
            "unidade": texto_no(prod, "nfe:uCom", ns),
            "quantidade": quantidade,
            "custo": custo_unitario,
            "subtotal": subtotal
        })

    valor_total = numero_float(
        texto_no(total, "nfe:vNF", ns) if total is not None else 0
    )

    return {
        "chave_nfe": chave_nfe,
        "numero_nfe": numero_nfe,
        "serie_nfe": serie_nfe,
        "data_emissao": data_emissao,
        "fornecedor": fornecedor,
        "produtos": produtos,
        "valor_total": valor_total
    }