from decimal import Decimal
import xml.etree.ElementTree as ET


NAMESPACE_NFE = {
    "nfe": "http://www.portalfiscal.inf.br/nfe"
}


def _texto(elemento, caminho):

    if elemento is None:
        return None

    encontrado = elemento.find(
        caminho,
        NAMESPACE_NFE
    )

    if (
        encontrado is None
        or encontrado.text is None
    ):
        return None

    return encontrado.text.strip()


def _decimal(valor):

    if valor in (None, ""):
        return Decimal("0")

    try:
        return Decimal(str(valor))
    except Exception:
        return Decimal("0")


def _ler_grupo_icms(imposto):

    resultado = {
        "grupo": None,
        "origem": None,
        "cst": None,
        "csosn": None,
        "base_icms": Decimal("0"),
        "aliquota_icms": Decimal("0"),
        "valor_icms": Decimal("0"),
        "base_icms_st": Decimal("0"),
        "aliquota_icms_st": Decimal("0"),
        "valor_icms_st": Decimal("0"),
    }

    if imposto is None:
        return resultado

    icms = imposto.find(
        "nfe:ICMS",
        NAMESPACE_NFE
    )

    if icms is None:
        return resultado

    grupos = list(icms)

    if not grupos:
        return resultado

    grupo = grupos[0]

    resultado["grupo"] = (
        grupo.tag.split("}")[-1]
    )

    resultado["origem"] = _texto(
        grupo,
        "nfe:orig"
    )

    resultado["cst"] = _texto(
        grupo,
        "nfe:CST"
    )

    resultado["csosn"] = _texto(
        grupo,
        "nfe:CSOSN"
    )

    resultado["base_icms"] = _decimal(
        _texto(
            grupo,
            "nfe:vBC"
        )
    )

    resultado["aliquota_icms"] = _decimal(
        _texto(
            grupo,
            "nfe:pICMS"
        )
    )

    resultado["valor_icms"] = _decimal(
        _texto(
            grupo,
            "nfe:vICMS"
        )
    )

    resultado["base_icms_st"] = _decimal(
        _texto(
            grupo,
            "nfe:vBCST"
        )
    )

    resultado["aliquota_icms_st"] = _decimal(
        _texto(
            grupo,
            "nfe:pICMSST"
        )
    )

    resultado["valor_icms_st"] = _decimal(
        _texto(
            grupo,
            "nfe:vICMSST"
        )
    )

    return resultado


def _ler_ipi(imposto):

    resultado = {
        "cst_ipi": None,
        "base_ipi": Decimal("0"),
        "aliquota_ipi": Decimal("0"),
        "valor_ipi": Decimal("0"),
    }

    if imposto is None:
        return resultado

    ipi = imposto.find(
        "nfe:IPI",
        NAMESPACE_NFE
    )

    if ipi is None:
        return resultado

    for nome_grupo in (
        "IPITrib",
        "IPINT"
    ):

        grupo = ipi.find(
            f"nfe:{nome_grupo}",
            NAMESPACE_NFE
        )

        if grupo is None:
            continue

        resultado["cst_ipi"] = _texto(
            grupo,
            "nfe:CST"
        )

        resultado["base_ipi"] = _decimal(
            _texto(
                grupo,
                "nfe:vBC"
            )
        )

        resultado["aliquota_ipi"] = _decimal(
            _texto(
                grupo,
                "nfe:pIPI"
            )
        )

        resultado["valor_ipi"] = _decimal(
            _texto(
                grupo,
                "nfe:vIPI"
            )
        )

        break

    return resultado


def extrair_itens_tributarios_sintegra(
    origem_xml
):

    if isinstance(origem_xml, bytes):
        raiz = ET.fromstring(origem_xml)

    elif isinstance(origem_xml, str):
        raiz = ET.fromstring(
            origem_xml.encode("utf-8")
        )

    else:
        raise TypeError(
            "XML deve ser informado como bytes ou texto."
        )

    itens = []

    for det in raiz.findall(
        ".//nfe:det",
        NAMESPACE_NFE
    ):

        prod = det.find(
            "nfe:prod",
            NAMESPACE_NFE
        )

        imposto = det.find(
            "nfe:imposto",
            NAMESPACE_NFE
        )

        icms = _ler_grupo_icms(
            imposto
        )

        ipi = _ler_ipi(
            imposto
        )

        numero_item = det.attrib.get(
            "nItem"
        )

        itens.append({
            "numero_item": (
                int(numero_item)
                if numero_item
                else None
            ),
            "codigo_produto": _texto(
                prod,
                "nfe:cProd"
            ),
            "descricao": _texto(
                prod,
                "nfe:xProd"
            ),
            "ncm": _texto(
                prod,
                "nfe:NCM"
            ),
            "cfop": _texto(
                prod,
                "nfe:CFOP"
            ),
            "unidade": _texto(
                prod,
                "nfe:uCom"
            ),
            "quantidade": _decimal(
                _texto(
                    prod,
                    "nfe:qCom"
                )
            ),
            "valor_produto": _decimal(
                _texto(
                    prod,
                    "nfe:vProd"
                )
            ),
            "valor_desconto": _decimal(
                _texto(
                    prod,
                    "nfe:vDesc"
                )
            ),
            **icms,
            **ipi,
        })

    return itens



def ler_xml_sintegra(origem_xml):

    if isinstance(origem_xml, bytes):
        raiz = ET.fromstring(origem_xml)

    elif isinstance(origem_xml, str):
        raiz = ET.fromstring(
            origem_xml.encode("utf-8")
        )

    else:
        raise TypeError(
            "XML deve ser informado como bytes ou texto."
        )

    inf_nfe = raiz.find(
        ".//nfe:infNFe",
        NAMESPACE_NFE
    )

    ide = raiz.find(
        ".//nfe:ide",
        NAMESPACE_NFE
    )

    emitente = raiz.find(
        ".//nfe:emit",
        NAMESPACE_NFE
    )

    destinatario = raiz.find(
        ".//nfe:dest",
        NAMESPACE_NFE
    )

    totais = raiz.find(
        ".//nfe:ICMSTot",
        NAMESPACE_NFE
    )

    chave = None

    if inf_nfe is not None:
        chave = (
            inf_nfe.attrib
            .get("Id", "")
            .replace("NFe", "")
        ) or None

    documento_destinatario = (
        _texto(
            destinatario,
            "nfe:CNPJ"
        )
        or
        _texto(
            destinatario,
            "nfe:CPF"
        )
    )

    return {
        "chave_acesso": chave,

        "modelo": _texto(
            ide,
            "nfe:mod"
        ),

        "serie": _texto(
            ide,
            "nfe:serie"
        ),

        "numero": _texto(
            ide,
            "nfe:nNF"
        ),

        "data_emissao": _texto(
            ide,
            "nfe:dhEmi"
        ),

        "data_saida_entrada": _texto(
            ide,
            "nfe:dhSaiEnt"
        ),

        "emitente": {
            "cnpj": _texto(
                emitente,
                "nfe:CNPJ"
            ),
            "nome": _texto(
                emitente,
                "nfe:xNome"
            ),
            "inscricao_estadual": _texto(
                emitente,
                "nfe:IE"
            ),
            "uf": _texto(
                emitente,
                "nfe:enderEmit/nfe:UF"
            ),
        },

        "destinatario": {
            "documento":
                documento_destinatario,
            "nome": _texto(
                destinatario,
                "nfe:xNome"
            ),
            "inscricao_estadual": _texto(
                destinatario,
                "nfe:IE"
            ),
            "uf": _texto(
                destinatario,
                "nfe:enderDest/nfe:UF"
            ),
        },

        "totais": {
            "valor_produtos": _decimal(
                _texto(
                    totais,
                    "nfe:vProd"
                )
            ),
            "base_icms": _decimal(
                _texto(
                    totais,
                    "nfe:vBC"
                )
            ),
            "valor_icms": _decimal(
                _texto(
                    totais,
                    "nfe:vICMS"
                )
            ),
            "base_icms_st": _decimal(
                _texto(
                    totais,
                    "nfe:vBCST"
                )
            ),
            "valor_icms_st": _decimal(
                _texto(
                    totais,
                    "nfe:vST"
                )
            ),
            "valor_ipi": _decimal(
                _texto(
                    totais,
                    "nfe:vIPI"
                )
            ),
            "valor_frete": _decimal(
                _texto(
                    totais,
                    "nfe:vFrete"
                )
            ),
            "valor_desconto": _decimal(
                _texto(
                    totais,
                    "nfe:vDesc"
                )
            ),
            "valor_nota": _decimal(
                _texto(
                    totais,
                    "nfe:vNF"
                )
            ),
        },

        "itens":
            extrair_itens_tributarios_sintegra(
                origem_xml
            ),
    }
