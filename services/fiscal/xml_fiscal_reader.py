from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET


NAMESPACE_NFE = {
    "nfe": "http://www.portalfiscal.inf.br/nfe"
}


# ============================================================
# CONVERSÕES SEGURAS
# ============================================================
def _texto(elemento, caminho, default=None):

    if elemento is None:
        return default

    item = elemento.find(
        caminho,
        NAMESPACE_NFE
    )

    if item is None:
        return default

    if item.text is None:
        return default

    return item.text.strip()


def _decimal(valor):

    if valor in (
        None,
        ""
    ):
        return Decimal("0")

    try:
        return Decimal(
            str(valor)
        )
    except Exception:
        return Decimal("0")


# ============================================================
# IDENTIFICAR BLOCO DE ICMS
# ============================================================
def _ler_icms(imposto):

    resultado = {
        "origem": None,
        "cst": None,
        "csosn": None
    }

    if imposto is None:
        return resultado

    icms = imposto.find(
        "nfe:ICMS",
        NAMESPACE_NFE
    )

    if icms is None:
        return resultado

    # O ICMS possui vários grupos possíveis:
    #
    # ICMS00
    # ICMS10
    # ICMS20
    # ICMS40
    # ICMS60
    # ICMSSN102
    # ICMSSN500
    # etc.
    #
    # Portanto percorremos o primeiro filho.

    for grupo in list(icms):

        origem = grupo.find(
            "nfe:orig",
            NAMESPACE_NFE
        )

        cst = grupo.find(
            "nfe:CST",
            NAMESPACE_NFE
        )

        csosn = grupo.find(
            "nfe:CSOSN",
            NAMESPACE_NFE
        )

        if origem is not None:
            resultado["origem"] = origem.text

        if cst is not None:
            resultado["cst"] = cst.text

        if csosn is not None:
            resultado["csosn"] = csosn.text

        break

    return resultado


# ============================================================
# LER PIS / COFINS
# ============================================================
def _ler_cst_imposto(
    imposto,
    nome_grupo
):

    if imposto is None:
        return None

    grupo_principal = imposto.find(
        f"nfe:{nome_grupo}",
        NAMESPACE_NFE
    )

    if grupo_principal is None:
        return None

    for grupo in list(
        grupo_principal
    ):

        cst = grupo.find(
            "nfe:CST",
            NAMESPACE_NFE
        )

        if cst is not None:
            return cst.text

    return None


# ============================================================
# IBS / CBS
# ============================================================
def _ler_ibs_cbs(imposto):

    resultado = {

        "cst": None,

        "classificacao_tributaria": None,

        "valor_ibs": Decimal("0"),

        "valor_cbs": Decimal("0")
    }

    if imposto is None:
        return resultado

    grupo = imposto.find(
        "nfe:IBSCBS",
        NAMESPACE_NFE
    )

    if grupo is None:
        return resultado

    resultado["cst"] = _texto(
        grupo,
        "nfe:CST"
    )

    resultado[
        "classificacao_tributaria"
    ] = _texto(
        grupo,
        "nfe:cClassTrib"
    )

    g_ibs_cbs = grupo.find(
        "nfe:gIBSCBS",
        NAMESPACE_NFE
    )

    if g_ibs_cbs is None:
        return resultado

    resultado["valor_ibs"] = (
        _decimal(
            _texto(
                g_ibs_cbs,
                "nfe:vIBS"
            )
        )
    )

    g_cbs = g_ibs_cbs.find(
        "nfe:gCBS",
        NAMESPACE_NFE
    )

    if g_cbs is not None:

        resultado["valor_cbs"] = (
            _decimal(
                _texto(
                    g_cbs,
                    "nfe:vCBS"
                )
            )
        )

    return resultado


# ============================================================
# LER ITEM
# ============================================================
def _ler_item(det):

    numero_item = det.attrib.get(
        "nItem"
    )

    prod = det.find(
        "nfe:prod",
        NAMESPACE_NFE
    )

    imposto = det.find(
        "nfe:imposto",
        NAMESPACE_NFE
    )

    icms = _ler_icms(
        imposto
    )

    ibs_cbs = _ler_ibs_cbs(
        imposto
    )

    return {

        "numero_item": int(
            numero_item
        ) if numero_item else None,

        "codigo_produto": _texto(
            prod,
            "nfe:cProd"
        ),

        "codigo_barras": _texto(
            prod,
            "nfe:cEAN"
        ),

        "descricao": _texto(
            prod,
            "nfe:xProd"
        ),

        "ncm": _texto(
            prod,
            "nfe:NCM"
        ),

        "cest": _texto(
            prod,
            "nfe:CEST"
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

        "valor_unitario": _decimal(
            _texto(
                prod,
                "nfe:vUnCom"
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

        "origem_icms": icms[
            "origem"
        ],

        "cst_icms": icms[
            "cst"
        ],

        "csosn": icms[
            "csosn"
        ],

        "cst_pis": _ler_cst_imposto(
            imposto,
            "PIS"
        ),

        "cst_cofins": (
            _ler_cst_imposto(
                imposto,
                "COFINS"
            )
        ),

        "cst_ibs_cbs": ibs_cbs[
            "cst"
        ],

        "classificacao_tributaria":
            ibs_cbs[
                "classificacao_tributaria"
            ],

        "valor_ibs": ibs_cbs[
            "valor_ibs"
        ],

        "valor_cbs": ibs_cbs[
            "valor_cbs"
        ]
    }


# ============================================================
# LER XML NF-e / NFC-e
# ============================================================
def ler_xml_fiscal(
    origem
):

    """
    Lê XML de:

    NF-e modelo 55
    NFC-e modelo 65

    Pode receber:

    - caminho de arquivo
    - bytes
    - string XML
    """

    xml_original = None

    # ----------------------------------------
    # ARQUIVO
    # ----------------------------------------
    if isinstance(
        origem,
        Path
    ):

        xml_original = (
            origem.read_text(
                encoding="utf-8"
            )
        )

    elif isinstance(
        origem,
        bytes
    ):

        xml_original = (
            origem.decode(
                "utf-8"
            )
        )

    elif isinstance(
        origem,
        str
    ):

        caminho = Path(
            origem
        )

        if (
            not origem.lstrip().startswith(
                "<"
            )
            and caminho.exists()
        ):

            xml_original = (
                caminho.read_text(
                    encoding="utf-8"
                )
            )

        else:
            xml_original = origem

    else:

        raise TypeError(
            "Formato de XML não suportado."
        )

    # ----------------------------------------
    # PARSE
    # ----------------------------------------
    root = ET.fromstring(
        xml_original
    )

    # Pode vir:
    #
    # <nfeProc>
    #     <NFe>
    #
    # ou diretamente:
    #
    # <NFe>

    if root.tag.endswith(
        "nfeProc"
    ):

        nfe = root.find(
            "nfe:NFe",
            NAMESPACE_NFE
        )

    elif root.tag.endswith(
        "NFe"
    ):

        nfe = root

    else:

        nfe = root.find(
            ".//nfe:NFe",
            NAMESPACE_NFE
        )

    if nfe is None:

        raise ValueError(
            "XML não contém uma NF-e/NFC-e válida."
        )

    inf_nfe = nfe.find(
        "nfe:infNFe",
        NAMESPACE_NFE
    )

    if inf_nfe is None:

        raise ValueError(
            "Tag infNFe não encontrada."
        )

    ide = inf_nfe.find(
        "nfe:ide",
        NAMESPACE_NFE
    )

    emit = inf_nfe.find(
        "nfe:emit",
        NAMESPACE_NFE
    )

    dest = inf_nfe.find(
        "nfe:dest",
        NAMESPACE_NFE
    )

    total = inf_nfe.find(
        "nfe:total/nfe:ICMSTot",
        NAMESPACE_NFE
    )

    # ----------------------------------------
    # CHAVE DE ACESSO
    # ----------------------------------------
    chave = inf_nfe.attrib.get(
        "Id",
        ""
    )

    if chave.startswith(
        "NFe"
    ):
        chave = chave[3:]

    # ----------------------------------------
    # PROTOCOLO
    # ----------------------------------------
    protocolo = None

    inf_prot = root.find(
        ".//nfe:protNFe/nfe:infProt",
        NAMESPACE_NFE
    )

    if inf_prot is not None:

        protocolo = _texto(
            inf_prot,
            "nfe:nProt"
        )

    # ----------------------------------------
    # EMITENTE
    # ----------------------------------------
    emitente = {

        "cnpj": _texto(
            emit,
            "nfe:CNPJ"
        ),

        "cpf": _texto(
            emit,
            "nfe:CPF"
        ),

        "razao_social": _texto(
            emit,
            "nfe:xNome"
        ),

        "nome_fantasia": _texto(
            emit,
            "nfe:xFant"
        ),

        "ie": _texto(
            emit,
            "nfe:IE"
        ),

        "crt": _texto(
            emit,
            "nfe:CRT"
        ),

        "uf": _texto(
            emit,
            "nfe:enderEmit/nfe:UF"
        ),

        "municipio": _texto(
            emit,
            "nfe:enderEmit/nfe:xMun"
        ),

        "codigo_municipio": _texto(
            emit,
            "nfe:enderEmit/nfe:cMun"
        )
    }

    # ----------------------------------------
    # DESTINATÁRIO
    # ----------------------------------------
    destinatario = {

        "cnpj": _texto(
            dest,
            "nfe:CNPJ"
        ),

        "cpf": _texto(
            dest,
            "nfe:CPF"
        ),

        "nome": _texto(
            dest,
            "nfe:xNome"
        ),

        "ie": _texto(
            dest,
            "nfe:IE"
        ),

        "indicador_ie": _texto(
            dest,
            "nfe:indIEDest"
        ),

        "uf": _texto(
            dest,
            "nfe:enderDest/nfe:UF"
        ),

        "municipio": _texto(
            dest,
            "nfe:enderDest/nfe:xMun"
        ),

        "codigo_municipio": _texto(
            dest,
            "nfe:enderDest/nfe:cMun"
        )
    }

    # ----------------------------------------
    # ITENS
    # ----------------------------------------
    itens = []

    for det in inf_nfe.findall(
        "nfe:det",
        NAMESPACE_NFE
    ):

        itens.append(
            _ler_item(
                det
            )
        )

    # ----------------------------------------
    # RESULTADO
    # ----------------------------------------
    resultado = {

        "chave_acesso": chave,

        "modelo": int(
            _texto(
                ide,
                "nfe:mod",
                0
            )
        ),

        "serie": int(
            _texto(
                ide,
                "nfe:serie",
                0
            )
        ),

        "numero": int(
            _texto(
                ide,
                "nfe:nNF",
                0
            )
        ),

        "natureza_operacao": _texto(
            ide,
            "nfe:natOp"
        ),

        "tipo_nf": _texto(
            ide,
            "nfe:tpNF"
        ),

        "destino_operacao": _texto(
            ide,
            "nfe:idDest"
        ),

        "ambiente": _texto(
            ide,
            "nfe:tpAmb"
        ),

        "finalidade": _texto(
            ide,
            "nfe:finNFe"
        ),

        "consumidor_final": _texto(
            ide,
            "nfe:indFinal"
        ),

        "presenca_comprador": _texto(
            ide,
            "nfe:indPres"
        ),

        "data_emissao": _texto(
            ide,
            "nfe:dhEmi"
        ),

        "emitente": emitente,

        "destinatario":
            destinatario,

        "valor_produtos": _decimal(
            _texto(
                total,
                "nfe:vProd"
            )
        ),

        "valor_frete": _decimal(
            _texto(
                total,
                "nfe:vFrete"
            )
        ),

        "valor_desconto": _decimal(
            _texto(
                total,
                "nfe:vDesc"
            )
        ),

        "valor_total": _decimal(
            _texto(
                total,
                "nfe:vNF"
            )
        ),

        "protocolo": protocolo,

        "itens": itens,

        "xml_original":
            xml_original
    }

    return resultado