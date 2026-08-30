from lxml import etree

from requests import Session
from requests_pkcs12 import Pkcs12Adapter


# ============================================================
# CONSULTA STATUS SERVIÇO NF-e - SEFAZ MG
#
# IMPORTANTE:
# - NÃO transmite NF-e
# - NÃO altera banco
# - NÃO consome numeração
# - apenas consulta o status do serviço
# ============================================================


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

NAMESPACE_SOAP12 = (
    "http://www.w3.org/2003/05/soap-envelope"
)

NAMESPACE_WSDL_STATUS = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4"
)

URL_PRODUCAO_MG = (
    "https://nfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeStatusServico4"
)

URL_HOMOLOGACAO_MG = (
    "https://hnfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeStatusServico4"
)


def _normalizar_ambiente(ambiente):
    ambiente = str(ambiente).strip()

    if ambiente not in {"1", "2"}:
        raise ValueError(
            "Ambiente fiscal inválido. "
            "Use 1 para produção ou 2 para homologação."
        )

    return ambiente


def _url_por_ambiente(ambiente):
    ambiente = _normalizar_ambiente(
        ambiente
    )

    if ambiente == "1":
        return URL_PRODUCAO_MG

    return URL_HOMOLOGACAO_MG


# ============================================================
# GERAR XML consStatServ
# ============================================================
def gerar_consulta_status(
    ambiente=2,
    codigo_uf="31"
):
    ambiente = _normalizar_ambiente(
        ambiente
    )

    raiz = etree.Element(
        etree.QName(
            NAMESPACE_NFE,
            "consStatServ"
        ),
        nsmap={
            None:
                NAMESPACE_NFE
        },
        versao="4.00"
    )

    tp_amb = etree.SubElement(
        raiz,
        etree.QName(
            NAMESPACE_NFE,
            "tpAmb"
        )
    )

    tp_amb.text = ambiente

    c_uf = etree.SubElement(
        raiz,
        etree.QName(
            NAMESPACE_NFE,
            "cUF"
        )
    )

    c_uf.text = str(
        codigo_uf
    )

    x_serv = etree.SubElement(
        raiz,
        etree.QName(
            NAMESPACE_NFE,
            "xServ"
        )
    )

    x_serv.text = "STATUS"

    return etree.tostring(
        raiz,
        encoding="utf-8",
        xml_declaration=False
    ).decode(
        "utf-8"
    )


# ============================================================
# GERAR SOAP 1.2
# ============================================================
def gerar_envelope_soap(
    xml_consulta
):
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

    nfe_dados_msg = etree.SubElement(
        body,
        etree.QName(
            NAMESPACE_WSDL_STATUS,
            "nfeDadosMsg"
        ),
        nsmap={
            None:
                NAMESPACE_WSDL_STATUS
        }
    )

    consulta = etree.fromstring(
        xml_consulta.encode(
            "utf-8"
        )
    )

    nfe_dados_msg.append(
        consulta
    )

    return etree.tostring(
        envelope,
        encoding="utf-8",
        xml_declaration=False,
        pretty_print=False
    )


# ============================================================
# CONSULTAR STATUS
# ============================================================
def consultar_status_sefaz_mg(
    caminho_certificado,
    senha,
    ambiente=2,
    codigo_uf="31",
    timeout=30
):
    try:
        ambiente = _normalizar_ambiente(
            ambiente
        )

        url = _url_por_ambiente(
            ambiente
        )

    except Exception as erro:
        return {
            "sucesso": False,
            "http_status": None,
            "ambiente": None,
            "url": None,
            "xml_consulta": None,
            "soap_enviado": None,
            "resposta": None,
            "erros": [
                f"{type(erro).__name__}: {erro}"
            ]
        }

    xml_consulta = gerar_consulta_status(
        ambiente=ambiente,
        codigo_uf=codigo_uf
    )

    soap = gerar_envelope_soap(
        xml_consulta
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
        "Content-Type":
            (
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
            "sucesso": False,
            "http_status": None,
            "ambiente": ambiente,
            "url": url,
            "xml_consulta":
                xml_consulta,
            "soap_enviado":
                soap.decode(
                    "utf-8"
                ),
            "resposta": None,
            "erros": [
                (
                    f"{type(erro).__name__}: "
                    f"{erro}"
                )
            ]
        }

    return {
        "sucesso":
            resposta.status_code == 200,

        "http_status":
            resposta.status_code,

        "ambiente":
            ambiente,

        "url":
            url,

        "xml_consulta":
            xml_consulta,

        "soap_enviado":
            soap.decode(
                "utf-8"
            ),

        "resposta":
            resposta.text,

        "content_type":
            resposta.headers.get(
                "content-type"
            ),

        "erros": []
    }
