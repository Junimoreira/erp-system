import base64
import hashlib
from pathlib import Path

from lxml import etree
import xmlsec

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
    pkcs12,
)


# ============================================================
# ASSINADOR XML NF-e - XMLSEC
#
# RESPONSABILIDADE:
# - Carregar certificado A1 PKCS#12
# - Localizar NFe / infNFe pelo atributo Id
# - Criar a estrutura XMLDSig com xmlsec
# - Registrar o atributo Id da infNFe
# - Calcular DigestValue pelo mecanismo XMLDSig
# - Assinar com RSA/SHA-1
# - Incluir certificado X509 no XML
#
# IMPORTANTE:
# - NÃO transmite para SEFAZ
# - NÃO altera banco
# - NÃO consome numeração
# - NÃO grava senha
# - NÃO grava chave privada
#
# A assinatura é delegada ao xmlsec para evitar divergências
# de canonicalização, namespaces e transforms.
# ============================================================


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

NAMESPACE_DS = (
    "http://www.w3.org/2000/09/xmldsig#"
)

ALGORITMO_C14N = (
    "http://www.w3.org/TR/2001/"
    "REC-xml-c14n-20010315"
)

ALGORITMO_ENVELOPED = (
    "http://www.w3.org/2000/09/"
    "xmldsig#enveloped-signature"
)

ALGORITMO_RSA_SHA1 = (
    "http://www.w3.org/2000/09/"
    "xmldsig#rsa-sha1"
)

ALGORITMO_SHA1 = (
    "http://www.w3.org/2000/09/"
    "xmldsig#sha1"
)


# ============================================================
# CARREGAR CERTIFICADO A1
# ============================================================
def carregar_certificado_a1(
    caminho_certificado,
    senha
):

    caminho = Path(
        caminho_certificado
    )

    if not caminho.exists():

        return {
            "sucesso": False,
            "chave_privada": None,
            "certificado": None,
            "cadeia": [],
            "erros": [
                "Certificado não encontrado."
            ]
        }

    if not caminho.is_file():

        return {
            "sucesso": False,
            "chave_privada": None,
            "certificado": None,
            "cadeia": [],
            "erros": [
                "O caminho informado não é um arquivo."
            ]
        }

    try:

        conteudo = caminho.read_bytes()

        senha_bytes = (
            None
            if senha is None
            else str(
                senha
            ).encode(
                "utf-8"
            )
        )

        chave_privada, certificado, cadeia = (
            pkcs12.load_key_and_certificates(
                conteudo,
                senha_bytes
            )
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "chave_privada": None,
            "certificado": None,
            "cadeia": [],
            "erros": [
                (
                    "Falha ao carregar certificado A1: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

    if chave_privada is None:

        return {
            "sucesso": False,
            "chave_privada": None,
            "certificado": certificado,
            "cadeia":
                list(
                    cadeia or []
                ),
            "erros": [
                "Certificado sem chave privada."
            ]
        }

    if certificado is None:

        return {
            "sucesso": False,
            "chave_privada": chave_privada,
            "certificado": None,
            "cadeia":
                list(
                    cadeia or []
                ),
            "erros": [
                "Certificado principal não encontrado."
            ]
        }

    return {
        "sucesso": True,
        "chave_privada":
            chave_privada,
        "certificado":
            certificado,
        "cadeia":
            list(
                cadeia or []
            ),
        "erros": []
    }


# ============================================================
# CARREGAR XML
# ============================================================
def _carregar_xml(
    xml
):

    if isinstance(
        xml,
        bytes
    ):

        xml_bytes = xml

    elif isinstance(
        xml,
        str
    ):

        texto = xml.strip()

        if texto.startswith(
            "<"
        ):

            xml_bytes = texto.encode(
                "utf-8"
            )

        else:

            caminho = Path(
                texto
            )

            if not caminho.exists():

                raise ValueError(
                    "Arquivo XML não encontrado."
                )

            xml_bytes = caminho.read_bytes()

    elif isinstance(
        xml,
        Path
    ):

        if not xml.exists():

            raise ValueError(
                "Arquivo XML não encontrado."
            )

        xml_bytes = xml.read_bytes()

    else:

        raise ValueError(
            "Tipo de entrada XML não suportado."
        )

    parser = etree.XMLParser(
        remove_blank_text=True,
        resolve_entities=False,
        no_network=True
    )

    return etree.fromstring(
        xml_bytes,
        parser
    )


# ============================================================
# CANONICALIZAR
#
# Mantido para diagnóstico e compatibilidade com testes.
# O fluxo principal de assinatura usa xmlsec.
# ============================================================
def _canonicalizar(
    elemento
):

    return etree.tostring(
        elemento,
        method="c14n",
        exclusive=False,
        with_comments=False
    )


# ============================================================
# LOCALIZAR NFe
# ============================================================
def _localizar_nfe(
    raiz
):

    qname = etree.QName(
        raiz
    )

    if (
        qname.localname == "NFe"
        and
        qname.namespace == NAMESPACE_NFE
    ):

        return raiz

    namespace = {
        "nfe":
            NAMESPACE_NFE
    }

    elementos = raiz.xpath(
        ".//nfe:NFe",
        namespaces=namespace
    )

    if not elementos:

        raise ValueError(
            "Elemento NFe não encontrado."
        )

    if len(
        elementos
    ) != 1:

        raise ValueError(
            (
                "O XML deve possuir exatamente "
                "uma NFe para assinatura."
            )
        )

    return elementos[0]


# ============================================================
# LOCALIZAR infNFe
# ============================================================
def _localizar_infnfe(
    raiz
):

    nfe = _localizar_nfe(
        raiz
    )

    namespace = {
        "nfe":
            NAMESPACE_NFE
    }

    elementos = nfe.xpath(
        "./nfe:infNFe",
        namespaces=namespace
    )

    if not elementos:

        raise ValueError(
            "Elemento infNFe não encontrado."
        )

    if len(
        elementos
    ) != 1:

        raise ValueError(
            (
                "A NFe deve possuir exatamente "
                "uma infNFe."
            )
        )

    inf_nfe = elementos[0]

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
            "Id da infNFe inválido."
        )

    return inf_nfe, id_infnfe


# ============================================================
# CALCULAR DIGEST MANUAL PARA DIAGNÓSTICO
#
# Esta função NÃO é usada para gerar a assinatura oficial.
# O xmlsec calcula o DigestValue aplicando os transforms da
# própria Reference.
# ============================================================
def _calcular_digest_infnfe(
    inf_nfe
):

    canonicalizado = _canonicalizar(
        inf_nfe
    )

    digest = hashlib.sha1(
        canonicalizado
    ).digest()

    return base64.b64encode(
        digest
    ).decode(
        "ascii"
    )


# ============================================================
# VERIFICAR ASSINATURA EXISTENTE
# ============================================================
def _possui_assinatura(
    nfe
):

    namespace_ds = {
        "ds":
            NAMESPACE_DS
    }

    assinaturas = nfe.xpath(
        "./ds:Signature",
        namespaces=namespace_ds
    )

    return bool(
        assinaturas
    )


# ============================================================
# PREPARAR CHAVE XMLSEC
# ============================================================
def _preparar_chave_xmlsec(
    chave_privada,
    certificado
):

    chave_pem = chave_privada.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )

    certificado_pem = certificado.public_bytes(
        Encoding.PEM
    )

    chave_xmlsec = xmlsec.Key.from_memory(
        chave_pem,
        xmlsec.constants.KeyDataFormatPem,
        None
    )

    chave_xmlsec.load_cert_from_memory(
        certificado_pem,
        xmlsec.constants.KeyDataFormatCertPem
    )

    return chave_xmlsec


# ============================================================
# MONTAR TEMPLATE XMLDSIG
# ============================================================
def _montar_template_assinatura(
    nfe,
    id_infnfe
):

    signature = xmlsec.template.create(
        nfe,
        xmlsec.constants.TransformInclC14N,
        xmlsec.constants.TransformRsaSha1,
        ns=None
    )

    # A assinatura da NF-e é filha direta de NFe,
    # logo após infNFe.
    nfe.append(
        signature
    )

    referencia = xmlsec.template.add_reference(
        signature,
        xmlsec.constants.TransformSha1,
        uri=(
            "#"
            +
            id_infnfe
        )
    )

    xmlsec.template.add_transform(
        referencia,
        xmlsec.constants.TransformEnveloped
    )

    xmlsec.template.add_transform(
        referencia,
        xmlsec.constants.TransformInclC14N
    )

    key_info = xmlsec.template.ensure_key_info(
        signature
    )

    xmlsec.template.add_x509_data(
        key_info
    )

    return signature


# ============================================================
# EXTRAIR DIGEST DO XML ASSINADO
# ============================================================
def _extrair_digest_value(
    signature
):

    namespace_ds = {
        "ds":
            NAMESPACE_DS
    }

    digest = signature.find(
        ".//ds:DigestValue",
        namespaces=namespace_ds
    )

    if (
        digest is None
        or
        not digest.text
    ):

        return None

    return str(
        digest.text
    ).strip()


# ============================================================
# VALIDAR ASSINATURA LOCAL COM XMLSEC
# ============================================================
def _validar_assinatura_xmlsec(
    raiz,
    signature,
    certificado
):

    xmlsec.tree.add_ids(
        raiz,
        [
            "Id"
        ]
    )

    certificado_pem = certificado.public_bytes(
        Encoding.PEM
    )

    chave_publica = xmlsec.Key.from_memory(
        certificado_pem,
        xmlsec.constants.KeyDataFormatCertPem,
        None
    )

    contexto = xmlsec.SignatureContext()
    contexto.key = chave_publica

    contexto.verify(
        signature
    )

    return True


# ============================================================
# ASSINAR XML NF-e
# ============================================================
def assinar_xml_nfe(
    xml,
    caminho_certificado,
    senha
):

    # --------------------------------------------------------
    # CERTIFICADO
    # --------------------------------------------------------
    resultado_certificado = carregar_certificado_a1(
        caminho_certificado=caminho_certificado,
        senha=senha
    )

    if not resultado_certificado.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros":
                resultado_certificado.get(
                    "erros",
                    []
                ),
            "avisos": []
        }

    chave_privada = resultado_certificado.get(
        "chave_privada"
    )

    certificado = resultado_certificado.get(
        "certificado"
    )

    # --------------------------------------------------------
    # XML ORIGINAL
    # --------------------------------------------------------
    try:

        raiz = _carregar_xml(
            xml
        )

        nfe = _localizar_nfe(
            raiz
        )

        inf_nfe, id_infnfe = _localizar_infnfe(
            raiz
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                str(
                    erro
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # EVITAR DUPLICIDADE DE ASSINATURA
    # --------------------------------------------------------
    if _possui_assinatura(
        nfe
    ):

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                "O XML já possui uma assinatura digital."
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # MONTAR TEMPLATE
    # --------------------------------------------------------
    try:

        signature = _montar_template_assinatura(
            nfe=nfe,
            id_infnfe=id_infnfe
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                (
                    "Falha ao montar template XMLDSig: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # ESTABILIZAR NAMESPACES ANTES DE ASSINAR
    #
    # O template é serializado e relido ANTES da assinatura.
    # Assim, a canonicalização usada para gerar SignatureValue
    # ocorre já sobre a mesma estrutura de namespaces que será
    # efetivamente gravada/transmitida.
    # --------------------------------------------------------
    try:

        xml_template_bytes = etree.tostring(
            raiz,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=False
        )

        parser = etree.XMLParser(
            remove_blank_text=True,
            resolve_entities=False,
            no_network=True
        )

        raiz_final = etree.fromstring(
            xml_template_bytes,
            parser
        )

        nfe_final = _localizar_nfe(
            raiz_final
        )

        inf_nfe_final, id_infnfe_final = _localizar_infnfe(
            raiz_final
        )

        if id_infnfe_final != id_infnfe:

            raise ValueError(
                "Id da infNFe mudou durante estabilização do XML."
            )

        signature_final = xmlsec.tree.find_node(
            nfe_final,
            xmlsec.constants.NodeSignature
        )

        if signature_final is None:

            raise ValueError(
                "Template Signature não encontrado após estabilização."
            )

        xmlsec.tree.add_ids(
            raiz_final,
            [
                "Id"
            ]
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                (
                    "Falha ao estabilizar XML antes da assinatura: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # CHAVE XMLSEC
    # --------------------------------------------------------
    try:

        chave_xmlsec = _preparar_chave_xmlsec(
            chave_privada=chave_privada,
            certificado=certificado
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                (
                    "Falha ao preparar chave/certificado para xmlsec: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # ASSINAR A ÁRVORE ESTABILIZADA
    # --------------------------------------------------------
    try:

        contexto = xmlsec.SignatureContext()
        contexto.key = chave_xmlsec

        contexto.sign(
            signature_final
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                (
                    "Falha ao assinar XML com xmlsec: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    digest_value = _extrair_digest_value(
        signature_final
    )

    # --------------------------------------------------------
    # NORMALIZAR BASE64 DO XMLDSIG
    #
    # A biblioteca xmlsec pode inserir quebras de linha em
    # SignatureValue e X509Certificate. A SEFAZ rejeita esses
    # caracteres de edição (cStat 588). A remoção de espaços,
    # CR/LF e TAB nesses dois conteúdos Base64 não altera o
    # SignedInfo nem o DigestValue da NF-e.
    # --------------------------------------------------------
    namespace_ds = {
        "ds": NAMESPACE_DS
    }

    signature_value_node = signature_final.find(
        "./ds:SignatureValue",
        namespaces=namespace_ds
    )

    if (
        signature_value_node is not None
        and
        signature_value_node.text
    ):
        signature_value_node.text = "".join(
            signature_value_node.text.split()
        )

    x509_nodes = signature_final.findall(
        ".//ds:X509Certificate",
        namespaces=namespace_ds
    )

    for x509_node in x509_nodes:

        if x509_node.text:
            x509_node.text = "".join(
                x509_node.text.split()
            )

    # --------------------------------------------------------
    # REMOVER WHITESPACE DE FORMATAÇÃO FORA DO SignedInfo
    #
    # xmlsec pode deixar CR/LF como text/tail no KeyInfo e
    # após Signature. Esses nós não pertencem ao SignedInfo
    # assinado. A remoção já foi validada em teste independente
    # sem invalidar a assinatura.
    # --------------------------------------------------------
    key_info_nodes = signature_final.findall(
        "./ds:KeyInfo",
        namespaces=namespace_ds
    )

    for key_info_node in key_info_nodes:

        for elemento in key_info_node.iter():

            if (
                elemento.text
                and
                elemento.text.isspace()
            ):
                elemento.text = None

            if (
                elemento.tail
                and
                elemento.tail.isspace()
            ):
                elemento.tail = None

    if (
        signature_final.tail
        and
        signature_final.tail.isspace()
    ):
        signature_final.tail = None

    # --------------------------------------------------------
    # SERIALIZAÇÃO FINAL
    # --------------------------------------------------------
    try:

        xml_bytes = etree.tostring(
            raiz_final,
            encoding="utf-8",
            xml_declaration=False,
            pretty_print=False
        )

        xml_texto = xml_bytes.decode(
            "utf-8"
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "erros": [
                (
                    "Falha ao serializar XML assinado: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # VERIFICAÇÃO PÓS-SERIALIZAÇÃO
    #
    # Esta é a validação que importa para transmissão:
    # reabre exatamente os bytes que serão devolvidos ao emissor
    # e verifica a assinatura novamente.
    # --------------------------------------------------------
    try:

        parser_verificacao = etree.XMLParser(
            remove_blank_text=True,
            resolve_entities=False,
            no_network=True
        )

        raiz_verificacao = etree.fromstring(
            xml_bytes,
            parser_verificacao
        )

        xmlsec.tree.add_ids(
            raiz_verificacao,
            [
                "Id"
            ]
        )

        signature_verificacao = xmlsec.tree.find_node(
            raiz_verificacao,
            xmlsec.constants.NodeSignature
        )

        if signature_verificacao is None:

            raise ValueError(
                "Signature não encontrada após serialização final."
            )

        certificado_pem = certificado.public_bytes(
            Encoding.PEM
        )

        chave_publica = xmlsec.Key.from_memory(
            certificado_pem,
            xmlsec.constants.KeyDataFormatCertPem,
            None
        )

        contexto_verificacao = xmlsec.SignatureContext()
        contexto_verificacao.key = chave_publica

        contexto_verificacao.verify(
            signature_verificacao
        )

        # Garantir que o XML final não contenha caracteres de
        # edição incompatíveis com a recepção da SEFAZ.
        if (
            b"\r" in xml_bytes
            or
            b"\n" in xml_bytes
            or
            b"\t" in xml_bytes
        ):
            raise ValueError(
                "XML final ainda contém CR/LF/TAB."
            )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "id_infnfe": id_infnfe,
            "digest_value": digest_value,
            "erros": [
                (
                    "A assinatura não permaneceu válida após "
                    "a serialização final do XML: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    return {
        "sucesso": True,

        "xml_assinado":
            xml_texto,

        "id_infnfe":
            id_infnfe,

        "digest_value":
            digest_value,

        "erros": [],

        "avisos": [
            (
                "XML assinado com xmlsec e validado novamente "
                "após a serialização final. "
                "Ainda não transmitido à SEFAZ."
            )
        ]
    }