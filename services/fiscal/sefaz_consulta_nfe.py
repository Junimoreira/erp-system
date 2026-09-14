from lxml import etree

from requests import Session
from requests_pkcs12 import Pkcs12Adapter


# ============================================================
# CONSULTA SITUACAO NF-e POR CHAVE - SEFAZ MG
#
# IMPORTANTE:
# - NAO transmite nova NF-e
# - NAO cancela NF-e
# - NAO altera banco
# - NAO consome numeracao
# - apenas consulta uma chave ja existente
# ============================================================


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

NAMESPACE_SOAP12 = (
    "http://www.w3.org/2003/05/soap-envelope"
)

NAMESPACE_WSDL_CONSULTA = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/"
    "NFeConsultaProtocolo4"
)

URL_PRODUCAO_MG = (
    "https://nfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeConsultaProtocolo4"
)

URL_HOMOLOGACAO_MG = (
    "https://hnfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeConsultaProtocolo4"
)


def _normalizar_ambiente(ambiente):

    ambiente = str(
        ambiente
    ).strip()

    if ambiente not in {"1", "2"}:
        raise ValueError(
            "Ambiente fiscal invalido. "
            "Use 1 para producao ou 2 para homologacao."
        )

    return ambiente


def _normalizar_chave(chave):

    chave = "".join(
        caractere
        for caractere in str(chave or "")
        if caractere.isdigit()
    )

    if len(chave) != 44:
        raise ValueError(
            "A chave de acesso da NF-e deve possuir "
            "44 digitos."
        )

    return chave


def _url_por_ambiente(ambiente):

    ambiente = _normalizar_ambiente(
        ambiente
    )

    if ambiente == "1":
        return URL_PRODUCAO_MG

    return URL_HOMOLOGACAO_MG


# ============================================================
# GERAR XML consSitNFe
# ============================================================

def gerar_consulta_nfe(
    chave,
    ambiente=1,
):

    ambiente = _normalizar_ambiente(
        ambiente
    )

    chave = _normalizar_chave(
        chave
    )

    raiz = etree.Element(
        etree.QName(
            NAMESPACE_NFE,
            "consSitNFe"
        ),
        nsmap={
            None: NAMESPACE_NFE
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

    x_serv = etree.SubElement(
        raiz,
        etree.QName(
            NAMESPACE_NFE,
            "xServ"
        )
    )

    x_serv.text = "CONSULTAR"

    ch_nfe = etree.SubElement(
        raiz,
        etree.QName(
            NAMESPACE_NFE,
            "chNFe"
        )
    )

    ch_nfe.text = chave

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
            None: NAMESPACE_SOAP12
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
            NAMESPACE_WSDL_CONSULTA,
            "nfeDadosMsg"
        ),
        nsmap={
            None: NAMESPACE_WSDL_CONSULTA
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
# EXTRAIR RETORNO
# ============================================================

def _extrair_retorno(
    xml_resposta
):

    resultado = {
        "cstat": None,
        "xmotivo": None,
        "chave": None,
        "protocolo": None,
        "eventos": [],
    }

    if not xml_resposta:
        return resultado

    try:
        raiz = etree.fromstring(
            xml_resposta.encode(
                "utf-8"
            )
        )

    except Exception:
        return resultado

    def primeiro_texto(nome):

        encontrados = raiz.xpath(
            f"//*[local-name()='{nome}']/text()"
        )

        if not encontrados:
            return None

        return str(
            encontrados[0]
        ).strip()

    resultado["cstat"] = primeiro_texto(
        "cStat"
    )

    resultado["xmotivo"] = primeiro_texto(
        "xMotivo"
    )

    resultado["chave"] = primeiro_texto(
        "chNFe"
    )

    resultado["protocolo"] = primeiro_texto(
        "nProt"
    )

    eventos = raiz.xpath(
        "//*[local-name()='retEvento']"
    )

    for evento in eventos:

        def texto_evento(nome):

            encontrados = evento.xpath(
                f".//*[local-name()='{nome}']/text()"
            )

            if not encontrados:
                return None

            return str(
                encontrados[0]
            ).strip()

        resultado["eventos"].append(
            {
                "tp_evento":
                    texto_evento("tpEvento"),

                "cstat":
                    texto_evento("cStat"),

                "xmotivo":
                    texto_evento("xMotivo"),

                "protocolo":
                    texto_evento("nProt"),

                "data_evento":
                    texto_evento("dhRegEvento"),
            }
        )

    return resultado


# ============================================================
# CONSULTAR NF-e
# ============================================================

def consultar_nfe_sefaz_mg(
    chave,
    caminho_certificado,
    senha,
    ambiente=1,
    timeout=30,
):

    try:

        ambiente = _normalizar_ambiente(
            ambiente
        )

        chave = _normalizar_chave(
            chave
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
            "chave": None,
            "cstat": None,
            "xmotivo": None,
            "protocolo": None,
            "eventos": [],
            "resposta": None,
            "erros": [
                f"{type(erro).__name__}: {erro}"
            ],
        }

    xml_consulta = gerar_consulta_nfe(
        chave=chave,
        ambiente=ambiente,
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
            "sucesso": False,
            "http_status": None,
            "ambiente": ambiente,
            "url": url,
            "chave": chave,
            "cstat": None,
            "xmotivo": None,
            "protocolo": None,
            "eventos": [],
            "resposta": None,
            "erros": [
                (
                    f"{type(erro).__name__}: "
                    f"{erro}"
                )
            ],
        }

    dados = _extrair_retorno(
        resposta.text
    )

    return {
        "sucesso":
            resposta.status_code == 200,

        "http_status":
            resposta.status_code,

        "ambiente":
            ambiente,

        "url":
            url,

        "chave":
            dados["chave"] or chave,

        "cstat":
            dados["cstat"],

        "xmotivo":
            dados["xmotivo"],

        "protocolo":
            dados["protocolo"],

        "eventos":
            dados["eventos"],

        "resposta":
            resposta.text,

        "erros": [],
    }
