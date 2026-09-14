from datetime import datetime, timezone, timedelta
from pathlib import Path

from lxml import etree
import xmlsec

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
)

from services.fiscal.assinador_xml_nfe import (
    carregar_certificado_a1,
)


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

NAMESPACE_DS = (
    "http://www.w3.org/2000/09/xmldsig#"
)

TIPO_EVENTO_CANCELAMENTO = "110111"


def _somente_digitos(valor):

    return "".join(
        caractere
        for caractere in str(valor or "")
        if caractere.isdigit()
    )


def _normalizar_chave(chave):

    chave = _somente_digitos(
        chave
    )

    if len(chave) != 44:

        raise ValueError(
            "Chave da NF-e deve possuir 44 digitos."
        )

    return chave


def _normalizar_protocolo(protocolo):

    protocolo = _somente_digitos(
        protocolo
    )

    if not protocolo:

        raise ValueError(
            "Protocolo de autorizacao nao informado."
        )

    return protocolo


def _normalizar_ambiente(ambiente):

    ambiente = str(
        ambiente
    ).strip()

    if ambiente not in {
        "1",
        "2",
    }:

        raise ValueError(
            "Ambiente deve ser 1 ou 2."
        )

    return ambiente


def _normalizar_justificativa(
    justificativa
):

    justificativa = " ".join(
        str(
            justificativa or ""
        ).split()
    )

    if len(justificativa) < 15:

        raise ValueError(
            "Justificativa deve possuir "
            "pelo menos 15 caracteres."
        )

    if len(justificativa) > 255:

        raise ValueError(
            "Justificativa deve possuir "
            "no maximo 255 caracteres."
        )

    return justificativa


def _dh_evento_agora():

    fuso = timezone(
        timedelta(
            hours=-3
        )
    )

    return datetime.now(
        fuso
    ).replace(
        microsecond=0
    ).isoformat()


def gerar_evento_cancelamento(
    chave,
    protocolo,
    cnpj,
    justificativa,
    ambiente=1,
    sequencia=1,
    dh_evento=None,
):

    chave = _normalizar_chave(
        chave
    )

    protocolo = _normalizar_protocolo(
        protocolo
    )

    ambiente = _normalizar_ambiente(
        ambiente
    )

    cnpj = _somente_digitos(
        cnpj
    )

    if len(cnpj) != 14:

        raise ValueError(
            "CNPJ do autor deve possuir 14 digitos."
        )

    justificativa = (
        _normalizar_justificativa(
            justificativa
        )
    )

    sequencia = int(
        sequencia
    )

    if sequencia <= 0:

        raise ValueError(
            "Sequencia do evento invalida."
        )

    dh_evento = (
        str(
            dh_evento
        ).strip()
        if dh_evento
        else _dh_evento_agora()
    )

    id_evento = (
        "ID"
        + TIPO_EVENTO_CANCELAMENTO
        + chave
        + str(
            sequencia
        ).zfill(2)
    )

    env_evento = etree.Element(
        etree.QName(
            NAMESPACE_NFE,
            "envEvento"
        ),
        nsmap={
            None:
                NAMESPACE_NFE
        },
        versao="1.00"
    )

    id_lote = etree.SubElement(
        env_evento,
        etree.QName(
            NAMESPACE_NFE,
            "idLote"
        )
    )

    id_lote.text = "1"

    evento = etree.SubElement(
        env_evento,
        etree.QName(
            NAMESPACE_NFE,
            "evento"
        ),
        versao="1.00"
    )

    inf_evento = etree.SubElement(
        evento,
        etree.QName(
            NAMESPACE_NFE,
            "infEvento"
        ),
        Id=id_evento
    )

    campos = [
        (
            "cOrgao",
            chave[:2]
        ),
        (
            "tpAmb",
            ambiente
        ),
        (
            "CNPJ",
            cnpj
        ),
        (
            "chNFe",
            chave
        ),
        (
            "dhEvento",
            dh_evento
        ),
        (
            "tpEvento",
            TIPO_EVENTO_CANCELAMENTO
        ),
        (
            "nSeqEvento",
            str(
                sequencia
            )
        ),
        (
            "verEvento",
            "1.00"
        ),
    ]

    for nome, valor in campos:

        elemento = etree.SubElement(
            inf_evento,
            etree.QName(
                NAMESPACE_NFE,
                nome
            )
        )

        elemento.text = valor

    det_evento = etree.SubElement(
        inf_evento,
        etree.QName(
            NAMESPACE_NFE,
            "detEvento"
        ),
        versao="1.00"
    )

    desc_evento = etree.SubElement(
        det_evento,
        etree.QName(
            NAMESPACE_NFE,
            "descEvento"
        )
    )

    desc_evento.text = (
        "Cancelamento"
    )

    n_prot = etree.SubElement(
        det_evento,
        etree.QName(
            NAMESPACE_NFE,
            "nProt"
        )
    )

    n_prot.text = protocolo

    x_just = etree.SubElement(
        det_evento,
        etree.QName(
            NAMESPACE_NFE,
            "xJust"
        )
    )

    x_just.text = justificativa

    return etree.tostring(
        env_evento,
        encoding="utf-8",
        xml_declaration=False,
        pretty_print=False
    )


def _preparar_chave_xmlsec(
    chave_privada,
    certificado
):

    chave_pem = (
        chave_privada.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        )
    )

    certificado_pem = (
        certificado.public_bytes(
            Encoding.PEM
        )
    )

    chave_xmlsec = (
        xmlsec.Key.from_memory(
            chave_pem,
            xmlsec.constants.KeyDataFormatPem,
            None
        )
    )

    chave_xmlsec.load_cert_from_memory(
        certificado_pem,
        xmlsec.constants.KeyDataFormatCertPem
    )

    return chave_xmlsec


def assinar_evento_cancelamento(
    xml_evento,
    caminho_certificado,
    senha
):

    resultado_certificado = (
        carregar_certificado_a1(
            caminho_certificado=
                caminho_certificado,
            senha=senha
        )
    )

    if not resultado_certificado.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "xml_assinado": None,
            "id_evento": None,
            "erros":
                resultado_certificado.get(
                    "erros",
                    []
                )
        }

    chave_privada = (
        resultado_certificado.get(
            "chave_privada"
        )
    )

    certificado = (
        resultado_certificado.get(
            "certificado"
        )
    )

    try:

        if isinstance(
            xml_evento,
            bytes
        ):
            xml_bytes = xml_evento

        else:
            xml_bytes = str(
                xml_evento
            ).encode(
                "utf-8"
            )

        parser = etree.XMLParser(
            remove_blank_text=True,
            resolve_entities=False,
            no_network=True
        )

        raiz = etree.fromstring(
            xml_bytes,
            parser
        )

        inf_evento = raiz.xpath(
            "//*[local-name()='infEvento']"
        )

        if len(inf_evento) != 1:

            raise ValueError(
                "infEvento nao encontrado "
                "de forma unica."
            )

        inf_evento = inf_evento[0]

        id_evento = str(
            inf_evento.get(
                "Id"
            )
            or ""
        ).strip()

        if not id_evento:

            raise ValueError(
                "Id do infEvento ausente."
            )

        evento = inf_evento.getparent()

        assinaturas = evento.xpath(
            "./ds:Signature",
            namespaces={
                "ds":
                    NAMESPACE_DS
            }
        )

        if assinaturas:

            raise ValueError(
                "Evento ja possui assinatura."
            )

        signature = (
            xmlsec.template.create(
                evento,
                xmlsec.constants.TransformInclC14N,
                xmlsec.constants.TransformRsaSha1,
                ns=None
            )
        )

        evento.append(
            signature
        )

        referencia = (
            xmlsec.template.add_reference(
                signature,
                xmlsec.constants.TransformSha1,
                uri=(
                    "#"
                    + id_evento
                )
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

        key_info = (
            xmlsec.template.ensure_key_info(
                signature
            )
        )

        xmlsec.template.add_x509_data(
            key_info
        )

        # Estabilizar namespaces antes da assinatura.
        xml_template = etree.tostring(
            raiz,
            encoding="utf-8",
            xml_declaration=False,
            pretty_print=False
        )

        raiz = etree.fromstring(
            xml_template,
            parser
        )

        inf_evento = raiz.xpath(
            "//*[local-name()='infEvento']"
        )[0]

        evento = inf_evento.getparent()

        signature = xmlsec.tree.find_node(
            evento,
            xmlsec.constants.NodeSignature
        )

        if signature is None:

            raise ValueError(
                "Signature nao encontrada "
                "apos estabilizacao."
            )

        xmlsec.tree.add_ids(
            raiz,
            [
                "Id"
            ]
        )

        chave_xmlsec = (
            _preparar_chave_xmlsec(
                chave_privada,
                certificado
            )
        )

        contexto = (
            xmlsec.SignatureContext()
        )

        contexto.key = chave_xmlsec

        contexto.sign(
            signature
        )

        # ----------------------------------------------------
        # NORMALIZAR XMLDSIG PARA SEFAZ
        #
        # Evita rejeicao cStat 588 por CR/LF/TAB ou espacos
        # de formatacao inseridos pelo xmlsec.
        # ----------------------------------------------------
        namespace_ds = {
            "ds": NAMESPACE_DS
        }

        signature_value = signature.find(
            "./ds:SignatureValue",
            namespaces=namespace_ds
        )

        if (
            signature_value is not None
            and
            signature_value.text
        ):
            signature_value.text = "".join(
                signature_value.text.split()
            )

        x509_nodes = signature.findall(
            ".//ds:X509Certificate",
            namespaces=namespace_ds
        )

        for x509_node in x509_nodes:
            if x509_node.text:
                x509_node.text = "".join(
                    x509_node.text.split()
                )

        key_info_nodes = signature.findall(
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
            signature.tail
            and
            signature.tail.isspace()
        ):
            signature.tail = None

        xml_assinado = etree.tostring(
            raiz,
            encoding="utf-8",
            xml_declaration=False,
            pretty_print=False
        )

        if (
            b"\r" in xml_assinado
            or
            b"\n" in xml_assinado
            or
            b"\t" in xml_assinado
        ):
            raise ValueError(
                "XML final do evento contem caracteres "
                "de edicao incompat?veis com a SEFAZ."
            )

        # Validacao local depois da serializacao.
        raiz_validacao = etree.fromstring(
            xml_assinado,
            parser
        )

        xmlsec.tree.add_ids(
            raiz_validacao,
            [
                "Id"
            ]
        )

        signature_validacao = (
            xmlsec.tree.find_node(
                raiz_validacao,
                xmlsec.constants.NodeSignature
            )
        )

        if signature_validacao is None:

            raise ValueError(
                "Signature ausente apos serializacao."
            )

        certificado_pem = (
            certificado.public_bytes(
                Encoding.PEM
            )
        )

        chave_publica = (
            xmlsec.Key.from_memory(
                certificado_pem,
                xmlsec.constants.KeyDataFormatCertPem,
                None
            )
        )

        contexto_validacao = (
            xmlsec.SignatureContext()
        )

        contexto_validacao.key = (
            chave_publica
        )

        contexto_validacao.verify(
            signature_validacao
        )

        return {
            "sucesso": True,
            "xml_assinado":
                xml_assinado,
            "id_evento":
                id_evento,
            "erros": [],
            "avisos": [
                (
                    "Evento de cancelamento "
                    "assinado e validado localmente. "
                    "Ainda nao transmitido."
                )
            ]
        }

    except Exception as erro:

        return {
            "sucesso": False,
            "xml_assinado": None,
            "id_evento": None,
            "erros": [
                (
                    f"{type(erro).__name__}: "
                    f"{erro}"
                )
            ],
            "avisos": []
        }

# ============================================================
# TRANSMISSAO EVENTO NF-e - SEFAZ MG
#
# IMPORTANTE:
# - transmite somente o XML de evento ja assinado;
# - nao altera banco;
# - nao altera status local da NF-e;
# - nao transmite uma nova NF-e.
# ============================================================

from requests import Session
from requests_pkcs12 import Pkcs12Adapter


NAMESPACE_SOAP12 = (
    "http://www.w3.org/2003/05/soap-envelope"
)

NAMESPACE_WSDL_EVENTO = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/"
    "NFeRecepcaoEvento4"
)

URL_EVENTO_PRODUCAO_MG = (
    "https://nfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeRecepcaoEvento4"
)

URL_EVENTO_HOMOLOGACAO_MG = (
    "https://hnfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeRecepcaoEvento4"
)


def _url_evento_por_ambiente(
    ambiente
):

    ambiente = _normalizar_ambiente(
        ambiente
    )

    if ambiente == "1":
        return URL_EVENTO_PRODUCAO_MG

    return URL_EVENTO_HOMOLOGACAO_MG


def gerar_soap_evento(
    xml_evento_assinado
):

    if isinstance(
        xml_evento_assinado,
        bytes
    ):
        xml_bytes = (
            xml_evento_assinado
        )

    elif isinstance(
        xml_evento_assinado,
        Path
    ):
        xml_bytes = (
            xml_evento_assinado.read_bytes()
        )

    elif isinstance(
        xml_evento_assinado,
        str
    ):

        texto = (
            xml_evento_assinado.strip()
        )

        if texto.startswith("<"):
            xml_bytes = texto.encode(
                "utf-8"
            )
        else:
            xml_bytes = Path(
                texto
            ).read_bytes()

    else:
        raise ValueError(
            "XML de evento em formato nao suportado."
        )

    evento = etree.fromstring(
        xml_bytes
    )

    envelope = etree.Element(
        etree.QName(
            NAMESPACE_SOAP12,
            "Envelope"
        ),
        nsmap={
            None:
                NAMESPACE_SOAP12
        }
    )

    body = etree.SubElement(
        envelope,
        etree.QName(
            NAMESPACE_SOAP12,
            "Body"
        )
    )

    dados_msg = etree.SubElement(
        body,
        etree.QName(
            NAMESPACE_WSDL_EVENTO,
            "nfeDadosMsg"
        ),
        nsmap={
            None:
                NAMESPACE_WSDL_EVENTO
        }
    )

    dados_msg.append(
        evento
    )

    return etree.tostring(
        envelope,
        encoding="utf-8",
        xml_declaration=False,
        pretty_print=False
    )


def interpretar_retorno_evento(
    xml_resposta
):

    resultado = {
        "cstat_lote": None,
        "xmotivo_lote": None,
        "tp_amb": None,
        "versao_aplicacao": None,
        "evento": None,
        "erros": [],
    }

    if not xml_resposta:
        resultado["erros"].append(
            "Resposta vazia da SEFAZ."
        )
        return resultado

    try:

        if isinstance(
            xml_resposta,
            bytes
        ):
            xml_bytes = xml_resposta
        else:
            xml_bytes = str(
                xml_resposta
            ).encode(
                "utf-8"
            )

        raiz = etree.fromstring(
            xml_bytes
        )

    except Exception as erro:

        resultado["erros"].append(
            (
                "Falha ao interpretar retorno: "
                f"{type(erro).__name__}: {erro}"
            )
        )

        return resultado

    def primeiro_texto(
        elemento,
        nome
    ):

        encontrados = elemento.xpath(
            ".//*[local-name()=$nome]/text()",
            nome=nome
        )

        if not encontrados:
            return None

        return str(
            encontrados[0]
        ).strip()

    resultado["cstat_lote"] = (
        primeiro_texto(
            raiz,
            "cStat"
        )
    )

    resultado["xmotivo_lote"] = (
        primeiro_texto(
            raiz,
            "xMotivo"
        )
    )

    resultado["tp_amb"] = (
        primeiro_texto(
            raiz,
            "tpAmb"
        )
    )

    resultado["versao_aplicacao"] = (
        primeiro_texto(
            raiz,
            "verAplic"
        )
    )

    retornos_evento = raiz.xpath(
        "//*[local-name()='retEvento']"
    )

    if retornos_evento:

        ret = retornos_evento[0]

        inf_ret = ret.xpath(
            ".//*[local-name()='infEvento']"
        )

        if inf_ret:
            inf_ret = inf_ret[0]
        else:
            inf_ret = ret

        resultado["evento"] = {
            "id":
                inf_ret.get("Id"),

            "cstat":
                primeiro_texto(
                    inf_ret,
                    "cStat"
                ),

            "xmotivo":
                primeiro_texto(
                    inf_ret,
                    "xMotivo"
                ),

            "chave":
                primeiro_texto(
                    inf_ret,
                    "chNFe"
                ),

            "tp_evento":
                primeiro_texto(
                    inf_ret,
                    "tpEvento"
                ),

            "sequencia":
                primeiro_texto(
                    inf_ret,
                    "nSeqEvento"
                ),

            "data_registro":
                primeiro_texto(
                    inf_ret,
                    "dhRegEvento"
                ),

            "protocolo_evento":
                primeiro_texto(
                    inf_ret,
                    "nProt"
                ),
        }

    return resultado


def transmitir_evento_cancelamento_mg(
    xml_evento_assinado,
    caminho_certificado,
    senha,
    ambiente=1,
    timeout=60,
):

    ambiente = _normalizar_ambiente(
        ambiente
    )

    url = _url_evento_por_ambiente(
        ambiente
    )

    soap = gerar_soap_evento(
        xml_evento_assinado
    )

    sessao = Session()

    sessao.mount(
        "https://",
        Pkcs12Adapter(
            pkcs12_filename=str(
                caminho_certificado
            ),
            pkcs12_password=senha
        )
    )

    headers = {
        "Content-Type": (
            "application/soap+xml; "
            "charset=utf-8"
        )
    }

    try:

        resposta = sessao.post(
            url,
            data=soap,
            headers=headers,
            timeout=timeout
        )

    except Exception as erro:

        return {
            "sucesso_comunicacao": False,
            "http_status": None,
            "ambiente": ambiente,
            "url": url,
            "retorno": None,
            "resposta_bruta": None,
            "erros": [
                (
                    f"{type(erro).__name__}: "
                    f"{erro}"
                )
            ]
        }

    retorno = interpretar_retorno_evento(
        resposta.content
    )

    return {
        "sucesso_comunicacao":
            resposta.ok,

        "http_status":
            resposta.status_code,

        "ambiente":
            ambiente,

        "url":
            url,

        "retorno":
            retorno,

        "resposta_bruta":
            resposta.text,

        "erros":
            retorno.get(
                "erros",
                []
            )
    }
