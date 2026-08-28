import xml.etree.ElementTree as ET

from services.fiscal.origem_mercadoria import (
    validar_origem_mercadoria
)


NAMESPACE_NFE = {
    "nfe": "http://www.portalfiscal.inf.br/nfe"
}


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar(
    valor
):

    if valor is None:
        return ""

    return str(
        valor
    ).strip()


# ============================================================
# LER ORIGEM DO ITEM NO XML
# ============================================================
def extrair_origem_item_xml(
    caminho_xml,
    numero_item=None,
    codigo_barras=None
):

    try:

        arvore = ET.parse(
            caminho_xml
        )

        raiz = arvore.getroot()

    except Exception as erro:

        return {
            "sucesso": False,
            "mensagem":
                f"Erro ao ler XML: {erro}",
            "item": None
        }

    codigo_barras = _normalizar(
        codigo_barras
    )

    # --------------------------------------------------------
    # PERCORRER ITENS
    # --------------------------------------------------------
    for det in raiz.findall(
        ".//nfe:det",
        NAMESPACE_NFE
    ):

        numero_xml = _normalizar(
            det.get(
                "nItem"
            )
        )

        prod = det.find(
            "nfe:prod",
            NAMESPACE_NFE
        )

        if prod is None:
            continue

        descricao = prod.findtext(
            "nfe:xProd",
            default="",
            namespaces=NAMESPACE_NFE
        )

        ean = prod.findtext(
            "nfe:cEAN",
            default="",
            namespaces=NAMESPACE_NFE
        )

        ncm = prod.findtext(
            "nfe:NCM",
            default="",
            namespaces=NAMESPACE_NFE
        )

        cest = prod.findtext(
            "nfe:CEST",
            default="",
            namespaces=NAMESPACE_NFE
        )

        cfop = prod.findtext(
            "nfe:CFOP",
            default="",
            namespaces=NAMESPACE_NFE
        )

        # ----------------------------------------------------
        # FILTRAR PELO NÚMERO DO ITEM
        # ----------------------------------------------------
        if numero_item is not None:

            if numero_xml != str(
                numero_item
            ):

                continue

        # ----------------------------------------------------
        # FILTRAR PELO CÓDIGO DE BARRAS
        # ----------------------------------------------------
        if codigo_barras:

            if _normalizar(
                ean
            ) != codigo_barras:

                continue

        # ----------------------------------------------------
        # LOCALIZAR GRUPO ICMS
        # ----------------------------------------------------
        icms = det.find(
            ".//nfe:ICMS",
            NAMESPACE_NFE
        )

        if icms is None:

            return {
                "sucesso": False,
                "mensagem":
                    "Grupo ICMS não encontrado no item.",
                "item": {
                    "numero_item":
                        numero_xml,
                    "descricao":
                        descricao,
                    "codigo_barras":
                        ean
                }
            }

        # ----------------------------------------------------
        # PROCURAR TAG orig EM QUALQUER SUBGRUPO DO ICMS
        # ----------------------------------------------------
        origem = None
        csosn = None
        cst = None

        for grupo_icms in list(
            icms
        ):

            origem = grupo_icms.findtext(
                "nfe:orig",
                default=None,
                namespaces=NAMESPACE_NFE
            )

            csosn = grupo_icms.findtext(
                "nfe:CSOSN",
                default=None,
                namespaces=NAMESPACE_NFE
            )

            cst = grupo_icms.findtext(
                "nfe:CST",
                default=None,
                namespaces=NAMESPACE_NFE
            )

            if origem is not None:
                break

        validacao_origem = (
            validar_origem_mercadoria(
                origem
            )
        )

        return {
            "sucesso":
                validacao_origem.get(
                    "sucesso"
                ),

            "mensagem":
                (
                    "Origem encontrada no histórico fiscal."
                    if validacao_origem.get(
                        "sucesso"
                    )
                    else
                    "Origem encontrada, porém inválida."
                ),

            "item": {
                "numero_item":
                    numero_xml,

                "descricao":
                    descricao,

                "codigo_barras":
                    ean,

                "ncm":
                    ncm or None,

                "cest":
                    cest or None,

                "cfop":
                    cfop or None,

                "origem":
                    origem,

                "origem_descricao":
                    validacao_origem.get(
                        "descricao"
                    ),

                "csosn":
                    csosn,

                "cst":
                    cst
            },

            "validacao_origem":
                validacao_origem
        }

    # --------------------------------------------------------
    # ITEM NÃO ENCONTRADO
    # --------------------------------------------------------
    return {
        "sucesso": False,
        "mensagem":
            "Item não encontrado no XML.",
        "item": None
    }