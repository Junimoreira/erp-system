from copy import deepcopy
from pathlib import Path

from lxml import etree


# ============================================================
# GERADOR DO ENVELOPE enviNFe
#
# RESPONSABILIDADE:
# - Receber uma NF-e já assinada
# - Montar o envelope <enviNFe versao="4.00">
# - Incluir idLote
# - Incluir indSinc
# - Incluir uma ou mais NFe
#
# IMPORTANTE:
# - NÃO transmite para SEFAZ
# - NÃO altera banco
# - NÃO consome numeração fiscal
# - NÃO altera a assinatura da NF-e
# - NÃO remove espaços/nós de texto do XML assinado
# ============================================================


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

NAMESPACE_DS = (
    "http://www.w3.org/2000/09/xmldsig#"
)

VERSAO_NFE = "4.00"


# ============================================================
# CARREGAR XML
#
# ATENÇÃO:
# Em XML já assinado NÃO devemos usar:
#
#     remove_blank_text=True
#
# Isso pode modificar nós de texto presentes na assinatura
# XMLDSig e invalidar o SignatureValue.
# ============================================================
def _carregar_xml(
    xml
):

    # --------------------------------------------------------
    # ELEMENTO LXML
    #
    # Fazemos cópia para não reparentar/modificar a árvore
    # que pertence ao chamador.
    # --------------------------------------------------------
    if isinstance(
        xml,
        etree._Element
    ):

        return deepcopy(
            xml
        )

    # --------------------------------------------------------
    # ELEMENT TREE
    # --------------------------------------------------------
    if isinstance(
        xml,
        etree._ElementTree
    ):

        return deepcopy(
            xml.getroot()
        )

    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------
    if isinstance(
        xml,
        Path
    ):

        caminho = xml

        if not caminho.is_file():

            raise ValueError(
                "Arquivo XML não encontrado."
            )

        conteudo = caminho.read_bytes()

    # --------------------------------------------------------
    # BYTES
    # --------------------------------------------------------
    elif isinstance(
        xml,
        bytes
    ):

        conteudo = xml

    # --------------------------------------------------------
    # STRING
    # --------------------------------------------------------
    elif isinstance(
        xml,
        str
    ):

        texto = xml.strip()

        if not texto:

            raise ValueError(
                "XML não informado."
            )

        # XML informado diretamente
        if texto.startswith(
            "<"
        ):

            conteudo = texto.encode(
                "utf-8"
            )

        # Caminho informado como string
        else:

            caminho = Path(
                texto
            )

            if not caminho.is_file():

                raise ValueError(
                    "Arquivo XML não encontrado."
                )

            conteudo = caminho.read_bytes()

    else:

        raise ValueError(
            "Tipo de XML não suportado."
        )

    # --------------------------------------------------------
    # PARSER
    #
    # MUITO IMPORTANTE:
    #
    # remove_blank_text=False
    #
    # O XML pode já conter uma assinatura XMLDSig.
    # Não podemos remover nós de texto em branco/quebras
    # existentes na árvore assinada.
    # --------------------------------------------------------
    parser = etree.XMLParser(
        remove_blank_text=False,
        resolve_entities=False,
        no_network=True
    )

    return etree.fromstring(
        conteudo,
        parser
    )


# ============================================================
# VALIDAR NF-e PARA O ENVELOPE
# ============================================================
def _validar_nfe(
    nfe
):

    qname = etree.QName(
        nfe
    )

    # --------------------------------------------------------
    # ELEMENTO RAIZ
    # --------------------------------------------------------
    if (
        qname.namespace
        !=
        NAMESPACE_NFE
        or
        qname.localname
        !=
        "NFe"
    ):

        raise ValueError(
            "O XML informado não possui elemento raiz NFe."
        )

    namespace = {
        "nfe":
            NAMESPACE_NFE,

        "ds":
            NAMESPACE_DS
    }

    # --------------------------------------------------------
    # infNFe
    # --------------------------------------------------------
    inf_nfe = nfe.find(
        "nfe:infNFe",
        namespace
    )

    if inf_nfe is None:

        raise ValueError(
            "A NF-e não possui infNFe."
        )

    # --------------------------------------------------------
    # Id DA infNFe
    # --------------------------------------------------------
    id_infnfe = inf_nfe.get(
        "Id"
    )

    if not id_infnfe:

        raise ValueError(
            "A infNFe não possui atributo Id."
        )

    if not id_infnfe.startswith(
        "NFe"
    ):

        raise ValueError(
            "O Id da infNFe é inválido."
        )

    # --------------------------------------------------------
    # SIGNATURE
    # --------------------------------------------------------
    assinatura = nfe.find(
        "ds:Signature",
        namespace
    )

    if assinatura is None:

        raise ValueError(
            (
                "A NF-e ainda não possui Signature. "
                "Assine o XML antes de montar enviNFe."
            )
        )

    # --------------------------------------------------------
    # SignedInfo
    # --------------------------------------------------------
    signed_info = assinatura.find(
        "ds:SignedInfo",
        namespace
    )

    if signed_info is None:

        raise ValueError(
            "A assinatura não possui SignedInfo."
        )

    # --------------------------------------------------------
    # SignatureValue
    # --------------------------------------------------------
    signature_value = assinatura.find(
        "ds:SignatureValue",
        namespace
    )

    if (
        signature_value is None
        or
        not signature_value.text
    ):

        raise ValueError(
            "A assinatura não possui SignatureValue."
        )

    # --------------------------------------------------------
    # X509Certificate
    # --------------------------------------------------------
    certificado = assinatura.find(
        ".//ds:X509Certificate",
        namespace
    )

    if (
        certificado is None
        or
        not certificado.text
    ):

        raise ValueError(
            "A assinatura não possui X509Certificate."
        )

    return True


# ============================================================
# NORMALIZAR idLote
# ============================================================
def _normalizar_id_lote(
    id_lote
):

    if id_lote is None:

        raise ValueError(
            "idLote não informado."
        )

    texto = str(
        id_lote
    ).strip()

    if not texto:

        raise ValueError(
            "idLote não informado."
        )

    if not texto.isdigit():

        raise ValueError(
            "idLote deve conter somente números."
        )

    return texto


# ============================================================
# NORMALIZAR indSinc
# ============================================================
def _normalizar_ind_sinc(
    ind_sinc
):

    texto = str(
        ind_sinc
    ).strip()

    if texto not in (
        "0",
        "1"
    ):

        raise ValueError(
            "indSinc deve ser 0 ou 1."
        )

    return texto


# ============================================================
# NORMALIZAR LISTA DE NF-e
# ============================================================
def _normalizar_nfes(
    nfes
):

    # --------------------------------------------------------
    # PERMITIR UMA ÚNICA NF-e SEM LISTA
    # --------------------------------------------------------
    if isinstance(
        nfes,
        (
            str,
            bytes,
            Path,
            etree._Element,
            etree._ElementTree
        )
    ):

        nfes = [
            nfes
        ]

    # --------------------------------------------------------
    # VALIDAR TIPO
    # --------------------------------------------------------
    if not isinstance(
        nfes,
        (
            list,
            tuple
        )
    ):

        raise ValueError(
            "NF-e deve ser informada como XML ou lista de XMLs."
        )

    # --------------------------------------------------------
    # LISTA VAZIA
    # --------------------------------------------------------
    if not nfes:

        raise ValueError(
            "Nenhuma NF-e informada."
        )

    # --------------------------------------------------------
    # LIMITE DO ENVELOPE
    # --------------------------------------------------------
    if len(
        nfes
    ) > 50:

        raise ValueError(
            "O envelope permite no máximo 50 NF-e."
        )

    resultado = []

    # --------------------------------------------------------
    # CARREGAR E VALIDAR CADA NF-e
    # --------------------------------------------------------
    for xml in nfes:

        nfe = _carregar_xml(
            xml
        )

        _validar_nfe(
            nfe
        )

        resultado.append(
            nfe
        )

    return resultado


# ============================================================
# GERAR enviNFe
# ============================================================
def gerar_envi_nfe(
    nfes,
    id_lote,
    ind_sinc=1
):

    # --------------------------------------------------------
    # NORMALIZAÇÃO / VALIDAÇÃO
    # --------------------------------------------------------
    try:

        id_lote = _normalizar_id_lote(
            id_lote
        )

        ind_sinc = _normalizar_ind_sinc(
            ind_sinc
        )

        nfes_normalizadas = _normalizar_nfes(
            nfes
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml": None,
            "id_lote": None,
            "ind_sinc": None,
            "quantidade_nfes": 0,
            "erros": [
                str(
                    erro
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # CRIAR enviNFe
    # --------------------------------------------------------
    envi_nfe = etree.Element(
        etree.QName(
            NAMESPACE_NFE,
            "enviNFe"
        ),
        nsmap={
            None:
                NAMESPACE_NFE
        },
        versao=VERSAO_NFE
    )

    # --------------------------------------------------------
    # idLote
    # --------------------------------------------------------
    elemento_id_lote = etree.SubElement(
        envi_nfe,
        etree.QName(
            NAMESPACE_NFE,
            "idLote"
        )
    )

    elemento_id_lote.text = (
        id_lote
    )

    # --------------------------------------------------------
    # indSinc
    # --------------------------------------------------------
    elemento_ind_sinc = etree.SubElement(
        envi_nfe,
        etree.QName(
            NAMESPACE_NFE,
            "indSinc"
        )
    )

    elemento_ind_sinc.text = (
        ind_sinc
    )

    # --------------------------------------------------------
    # NFe
    #
    # IMPORTANTE:
    #
    # Não fazemos um segundo deepcopy aqui.
    #
    # Cada NF-e já foi carregada em uma árvore própria por
    # _carregar_xml().
    #
    # Assim reduzimos transformações desnecessárias sobre o
    # XML que contém a assinatura digital.
    # --------------------------------------------------------
    for nfe in nfes_normalizadas:

        envi_nfe.append(
            nfe
        )

    # --------------------------------------------------------
    # SERIALIZAR
    #
    # NÃO usar pretty_print=True.
    #
    # Não queremos inserir novos espaços/quebras de linha no
    # conteúdo XML já assinado.
    # --------------------------------------------------------
    xml_bytes = etree.tostring(
        envi_nfe,
        encoding="utf-8",
        xml_declaration=False,
        pretty_print=False
    )

    xml_texto = xml_bytes.decode(
        "utf-8"
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    return {
        "sucesso": True,

        "xml":
            xml_texto,

        "id_lote":
            id_lote,

        "ind_sinc":
            ind_sinc,

        "quantidade_nfes":
            len(
                nfes_normalizadas
            ),

        "erros": [],

        "avisos": [
            (
                "Envelope enviNFe gerado localmente. "
                "Nenhuma transmissão foi realizada."
            ),
            (
                "A NF-e assinada foi preservada sem "
                "remoção de nós de texto."
            )
        ]
    }