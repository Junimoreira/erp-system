from pathlib import Path

from lxml import etree

from requests import Session
from requests_pkcs12 import Pkcs12Adapter


# ============================================================
# AUTORIZAÇÃO NF-e - SEFAZ MG
#
# RESPONSABILIDADE:
# - Ler um envelope enviNFe já gerado e validado
# - Enviar para o serviço NFeAutorizacao4 em homologação
# - Usar certificado A1 PKCS#12 no mTLS
# - Capturar o SOAP bruto
# - Extrair os principais campos de retorno
#
# IMPORTANTE:
# - Este módulo NÃO gera NF-e
# - NÃO assina NF-e
# - NÃO altera banco
# - NÃO incrementa numeração fiscal do ERP
# - Este módulo de teste BLOQUEIA tpAmb diferente de 2
# - NÃO remove nós de texto do XML já assinado
# ============================================================


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

NAMESPACE_SOAP12 = (
    "http://www.w3.org/2003/05/soap-envelope"
)

NAMESPACE_WSDL = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"
)

NAMESPACE_WSDL_RET_AUTORIZACAO = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4"
)

NAMESPACE_DS = (
    "http://www.w3.org/2000/09/xmldsig#"
)

URL_HOMOLOGACAO_MG = (
    "https://hnfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeAutorizacao4"
)

URL_RET_AUTORIZACAO_HOMOLOGACAO_MG = (
    "https://hnfe.fazenda.mg.gov.br/"
    "nfe2/services/NFeRetAutorizacao4"
)


# ============================================================
# LER XML
# ============================================================
def _ler_xml(
    origem
):

    if isinstance(
        origem,
        Path
    ):

        if not origem.is_file():

            raise ValueError(
                "Arquivo XML não encontrado."
            )

        return origem.read_bytes()

    if isinstance(
        origem,
        bytes
    ):

        return origem

    if isinstance(
        origem,
        str
    ):

        texto = origem.strip()

        if texto.startswith(
            "<"
        ):

            return texto.encode(
                "utf-8"
            )

        caminho = Path(
            texto
        )

        if not caminho.is_file():

            raise ValueError(
                "Arquivo XML não encontrado."
            )

        return caminho.read_bytes()

    raise ValueError(
        "Tipo de origem XML não suportado."
    )


# ============================================================
# CARREGAR ELEMENTO XML
#
# O enviNFe contém uma NF-e já assinada.
# Não remover nós de texto, pois SignedInfo usa C14N inclusiva.
# ============================================================
def _carregar_elemento(
    origem
):

    xml_bytes = _ler_xml(
        origem
    )

    parser = etree.XMLParser(
        remove_blank_text=False,
        resolve_entities=False,
        no_network=True
    )

    return etree.fromstring(
        xml_bytes,
        parser
    )


# ============================================================
# VALIDAR ENVELOPE ANTES DO ENVIO
# ============================================================
def validar_envelope_para_homologacao(
    origem
):

    try:

        raiz = _carregar_elemento(
            origem
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "erros": [
                (
                    "Falha ao carregar enviNFe: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

    qname = etree.QName(
        raiz
    )

    if (
        qname.namespace
        !=
        NAMESPACE_NFE
        or
        qname.localname
        !=
        "enviNFe"
    ):

        return {
            "sucesso": False,
            "erros": [
                "Elemento raiz deve ser enviNFe."
            ]
        }

    versao = raiz.get(
        "versao"
    )

    if versao != "4.00":

        return {
            "sucesso": False,
            "erros": [
                (
                    "Versão do enviNFe deve ser 4.00. "
                    f"Recebido: {versao}"
                )
            ]
        }

    ns = {
        "nfe":
            NAMESPACE_NFE,

        "ds":
            NAMESPACE_DS
    }

    id_lote = raiz.findtext(
        "nfe:idLote",
        namespaces=ns
    )

    ind_sinc = raiz.findtext(
        "nfe:indSinc",
        namespaces=ns
    )

    nfes = raiz.findall(
        "nfe:NFe",
        ns
    )

    if not nfes:

        return {
            "sucesso": False,
            "erros": [
                "Nenhuma NFe encontrada no enviNFe."
            ]
        }

    ambientes = []
    numeros = []
    series = []
    chaves = []

    for nfe in nfes:

        inf_nfe = nfe.find(
            "nfe:infNFe",
            ns
        )

        if inf_nfe is None:

            return {
                "sucesso": False,
                "erros": [
                    "NFe sem infNFe."
                ]
            }

        ide = inf_nfe.find(
            "nfe:ide",
            ns
        )

        if ide is None:

            return {
                "sucesso": False,
                "erros": [
                    "NFe sem ide."
                ]
            }

        tp_amb = ide.findtext(
            "nfe:tpAmb",
            namespaces=ns
        )

        numero = ide.findtext(
            "nfe:nNF",
            namespaces=ns
        )

        serie = ide.findtext(
            "nfe:serie",
            namespaces=ns
        )

        id_infnfe = inf_nfe.get(
            "Id",
            ""
        )

        chave = (
            id_infnfe[3:]
            if id_infnfe.startswith(
                "NFe"
            )
            else id_infnfe
        )

        assinatura = nfe.find(
            "ds:Signature",
            ns
        )

        if assinatura is None:

            return {
                "sucesso": False,
                "erros": [
                    (
                        f"NF-e {numero or '?'} "
                        "não possui Signature."
                    )
                ]
            }

        if tp_amb != "2":

            return {
                "sucesso": False,
                "erros": [
                    (
                        "ENVIO BLOQUEADO: este módulo de teste "
                        "aceita somente tpAmb=2 (homologação). "
                        f"Encontrado tpAmb={tp_amb}."
                    )
                ]
            }

        ambientes.append(
            tp_amb
        )

        numeros.append(
            numero
        )

        series.append(
            serie
        )

        chaves.append(
            chave
        )

    return {
        "sucesso": True,
        "versao":
            versao,
        "id_lote":
            id_lote,
        "ind_sinc":
            ind_sinc,
        "quantidade_nfes":
            len(
                nfes
            ),
        "ambientes":
            ambientes,
        "numeros":
            numeros,
        "series":
            series,
        "chaves":
            chaves,
        "erros": []
    }


# ============================================================
# GERAR SOAP 1.2
#
# CORREÇÕES IMPORTANTES:
#
# 1. NÃO declaramos "soap12" como prefixo no Envelope.
#    Usamos namespace DEFAULT em cada nível para não alterar
#    o contexto de namespaces da assinatura XMLDSig.
#
# 2. NÃO geramos declaração XML no início do SOAP.
#    Isso evita o LF que o lxml insere entre:
#
#       <?xml version='1.0' encoding='utf-8'?>
#       <Envelope ...>
#
#    Esse LF foi identificado pelo teste da rejeição 588.
#
# 3. NÃO usamos pretty_print.
# ============================================================
def gerar_soap_autorizacao(
    origem_envi_nfe
):

    envi_nfe = _carregar_elemento(
        origem_envi_nfe
    )

    # --------------------------------------------------------
    # Envelope SOAP com namespace DEFAULT.
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # nfeDadosMsg com namespace WSDL DEFAULT.
    # --------------------------------------------------------
    dados_msg = etree.SubElement(
        body,
        etree.QName(
            NAMESPACE_WSDL,
            "nfeDadosMsg"
        ),
        nsmap={
            None:
                NAMESPACE_WSDL
        }
    )

    dados_msg.append(
        envi_nfe
    )

    # --------------------------------------------------------
    # IMPORTANTE PARA REJEIÇÃO 588:
    #
    # xml_declaration=False
    #
    # O payload HTTP começa diretamente em <Envelope>.
    # --------------------------------------------------------
    return etree.tostring(
        envelope,
        encoding="utf-8",
        xml_declaration=False,
        pretty_print=False
    )


# ============================================================
# EXTRAIR PRIMEIRO TEXTO POR local-name
# ============================================================
def _primeiro_texto(
    raiz,
    nome
):

    elementos = raiz.xpath(
        ".//*[local-name()=$nome]",
        nome=nome
    )

    if not elementos:

        return None

    texto = elementos[0].text

    if texto is None:

        return None

    return texto.strip()


# ============================================================
# EXTRAIR RETORNO DA AUTORIZAÇÃO
# ============================================================
def interpretar_retorno_autorizacao(
    xml_resposta
):

    if not xml_resposta:

        return {
            "sucesso_parse": False,
            "erros_parse": [
                "Resposta vazia."
            ]
        }

    try:

        parser = etree.XMLParser(
            remove_blank_text=False,
            resolve_entities=False,
            no_network=True
        )

        raiz = etree.fromstring(
            xml_resposta.encode(
                "utf-8"
            ),
            parser
        )

    except Exception as erro:

        return {
            "sucesso_parse": False,
            "erros_parse": [
                (
                    "Falha ao interpretar SOAP: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

    faults = raiz.xpath(
        ".//*[local-name()='Fault']"
    )

    if faults:

        fault = faults[0]

        return {
            "sucesso_parse": True,
            "soap_fault": True,
            "fault_code":
                _primeiro_texto(
                    fault,
                    "Value"
                ),
            "fault_reason":
                _primeiro_texto(
                    fault,
                    "Text"
                ),
            "erros_parse": []
        }

    ret_envios = raiz.xpath(
        ".//*[local-name()='retEnviNFe']"
    )

    if not ret_envios:

        return {
            "sucesso_parse": False,
            "soap_fault": False,
            "erros_parse": [
                "retEnviNFe não encontrado na resposta."
            ]
        }

    ret = ret_envios[0]

    tp_amb = _primeiro_texto(
        ret,
        "tpAmb"
    )

    ver_aplic = _primeiro_texto(
        ret,
        "verAplic"
    )

    c_stat_lote = _primeiro_texto(
        ret,
        "cStat"
    )

    x_motivo_lote = _primeiro_texto(
        ret,
        "xMotivo"
    )

    c_uf = _primeiro_texto(
        ret,
        "cUF"
    )

    dh_recbto = _primeiro_texto(
        ret,
        "dhRecbto"
    )

    n_rec = _primeiro_texto(
        ret,
        "nRec"
    )

    prot_nfes = ret.xpath(
        ".//*[local-name()='protNFe']"
    )

    protocolos = []

    for prot in prot_nfes:

        inf_prot_list = prot.xpath(
            "./*[local-name()='infProt']"
        )

        if not inf_prot_list:

            continue

        inf = inf_prot_list[0]

        protocolos.append(
            {
                "tpAmb":
                    _primeiro_texto(
                        inf,
                        "tpAmb"
                    ),

                "verAplic":
                    _primeiro_texto(
                        inf,
                        "verAplic"
                    ),

                "chNFe":
                    _primeiro_texto(
                        inf,
                        "chNFe"
                    ),

                "dhRecbto":
                    _primeiro_texto(
                        inf,
                        "dhRecbto"
                    ),

                "nProt":
                    _primeiro_texto(
                        inf,
                        "nProt"
                    ),

                "digVal":
                    _primeiro_texto(
                        inf,
                        "digVal"
                    ),

                "cStat":
                    _primeiro_texto(
                        inf,
                        "cStat"
                    ),

                "xMotivo":
                    _primeiro_texto(
                        inf,
                        "xMotivo"
                    )
            }
        )

    autorizado = any(
        protocolo.get(
            "cStat"
        )
        in (
            "100",
            "150"
        )
        for protocolo in protocolos
    )

    return {
        "sucesso_parse": True,
        "soap_fault": False,
        "tpAmb":
            tp_amb,
        "verAplic":
            ver_aplic,
        "cStat_lote":
            c_stat_lote,
        "xMotivo_lote":
            x_motivo_lote,
        "cUF":
            c_uf,
        "dhRecbto":
            dh_recbto,
        "nRec":
            n_rec,
        "protocolos":
            protocolos,
        "autorizado":
            autorizado,
        "erros_parse": []
    }


# ============================================================
# AUTORIZAR NF-e EM HOMOLOGAÇÃO
# ============================================================
def autorizar_nfe_homologacao_mg(
    origem_envi_nfe,
    caminho_certificado,
    senha,
    timeout=60
):

    validacao = validar_envelope_para_homologacao(
        origem_envi_nfe
    )

    if not validacao.get(
        "sucesso"
    ):

        return {
            "sucesso_http": False,
            "enviado": False,
            "validacao":
                validacao,
            "http_status": None,
            "content_type": None,
            "resposta_bruta": None,
            "retorno": None,
            "erros":
                validacao.get(
                    "erros",
                    []
                )
        }

    try:

        soap = gerar_soap_autorizacao(
            origem_envi_nfe
        )

    except Exception as erro:

        return {
            "sucesso_http": False,
            "enviado": False,
            "validacao":
                validacao,
            "http_status": None,
            "content_type": None,
            "resposta_bruta": None,
            "retorno": None,
            "erros": [
                (
                    "Falha ao gerar SOAP: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

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
            "application/soap+xml; charset=utf-8"
    }

    try:

        resposta = sessao.post(
            URL_HOMOLOGACAO_MG,
            data=soap,
            headers=headers,
            timeout=timeout
        )

    except Exception as erro:

        return {
            "sucesso_http": False,
            "enviado": True,
            "validacao":
                validacao,
            "http_status": None,
            "content_type": None,
            "resposta_bruta": None,
            "retorno": None,
            "erros": [
                (
                    "Falha na comunicação com a SEFAZ: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

    retorno = interpretar_retorno_autorizacao(
        resposta.text
    )

    return {
        "sucesso_http":
            resposta.status_code
            ==
            200,

        "enviado":
            True,

        "validacao":
            validacao,

        "http_status":
            resposta.status_code,

        "content_type":
            resposta.headers.get(
                "content-type"
            ),

        "resposta_bruta":
            resposta.text,

        "retorno":
            retorno,

        "erros": []
    }

# ============================================================
# NORMALIZAR NÚMERO DO RECIBO
# ============================================================
def _normalizar_numero_recibo(
    numero_recibo
):

    if numero_recibo is None:

        raise ValueError(
            "Número do recibo não informado."
        )

    numero = "".join(
        caractere
        for caractere in str(
            numero_recibo
        ).strip()
        if caractere.isdigit()
    )

    if not numero:

        raise ValueError(
            "Número do recibo inválido."
        )

    return numero


# ============================================================
# GERAR XML consReciNFe
# ============================================================
def gerar_consulta_recibo_nfe(
    numero_recibo,
    ambiente=2
):

    try:

        ambiente = int(
            ambiente
        )

    except (
        TypeError,
        ValueError
    ) as erro:

        raise ValueError(
            "Ambiente fiscal inválido."
        ) from erro

    # --------------------------------------------------------
    # ESTE MÓDULO CONTINUA RESTRITO À HOMOLOGAÇÃO
    # --------------------------------------------------------
    if ambiente != 2:

        raise ValueError(
            (
                "Consulta bloqueada. "
                "Este módulo aceita somente "
                "ambiente de homologação (tpAmb=2)."
            )
        )

    numero_recibo = (
        _normalizar_numero_recibo(
            numero_recibo
        )
    )

    raiz = etree.Element(
        "consReciNFe",
        nsmap={
            None:
                NAMESPACE_NFE
        },
        versao="4.00"
    )

    tp_amb = etree.SubElement(
        raiz,
        "tpAmb"
    )

    tp_amb.text = str(
        ambiente
    )

    n_rec = etree.SubElement(
        raiz,
        "nRec"
    )

    n_rec.text = numero_recibo

    return etree.tostring(
        raiz,
        encoding="utf-8",
        xml_declaration=False
    )


# ============================================================
# GERAR SOAP PARA NFeRetAutorizacao4
# ============================================================
def gerar_soap_consulta_recibo(
    numero_recibo,
    ambiente=2
):

    consulta = gerar_consulta_recibo_nfe(
        numero_recibo=numero_recibo,
        ambiente=ambiente
    )

    parser = etree.XMLParser(
        remove_blank_text=False,
        resolve_entities=False,
        no_network=True
    )

    consulta_elemento = etree.fromstring(
        consulta,
        parser
    )

    envelope = etree.Element(
        etree.QName(
            NAMESPACE_SOAP12,
            "Envelope"
        ),
        nsmap={
            "soap12":
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
            NAMESPACE_WSDL_RET_AUTORIZACAO,
            "nfeDadosMsg"
        )
    )

    dados_msg.append(
        consulta_elemento
    )

    return etree.tostring(
        envelope,
        encoding="utf-8",
        xml_declaration=True
    )


# ============================================================
# INTERPRETAR RETORNO DA CONSULTA DO RECIBO
# ============================================================
def interpretar_retorno_consulta_recibo(
    xml_resposta
):

    try:

        raiz = _carregar_elemento(
            xml_resposta
        )

    except Exception as erro:

        return {
            "sucesso_parse": False,
            "soap_fault": False,
            "autorizado": False,
            "erros_parse": [
                (
                    "Não foi possível interpretar "
                    "o XML de retorno: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

    # --------------------------------------------------------
    # SOAP FAULT
    # --------------------------------------------------------
    faults = raiz.xpath(
        ".//*[local-name()='Fault']"
    )

    if faults:

        fault = faults[0]

        return {
            "sucesso_parse": True,
            "soap_fault": True,

            "fault_code":
                _primeiro_texto(
                    fault,
                    "Value"
                ),

            "fault_reason":
                _primeiro_texto(
                    fault,
                    "Text"
                ),

            "autorizado":
                False,

            "erros_parse":
                []
        }

    # --------------------------------------------------------
    # retConsReciNFe
    # --------------------------------------------------------
    retornos = raiz.xpath(
        ".//*[local-name()='retConsReciNFe']"
    )

    if not retornos:

        return {
            "sucesso_parse": False,
            "soap_fault": False,
            "autorizado": False,
            "erros_parse": [
                (
                    "retConsReciNFe não encontrado "
                    "na resposta."
                )
            ]
        }

    ret = retornos[0]

    tp_amb = _primeiro_texto(
        ret,
        "tpAmb"
    )

    ver_aplic = _primeiro_texto(
        ret,
        "verAplic"
    )

    c_stat_lote = _primeiro_texto(
        ret,
        "cStat"
    )

    x_motivo_lote = _primeiro_texto(
        ret,
        "xMotivo"
    )

    c_uf = _primeiro_texto(
        ret,
        "cUF"
    )

    n_rec = _primeiro_texto(
        ret,
        "nRec"
    )

    prot_nfes = ret.xpath(
        ".//*[local-name()='protNFe']"
    )

    protocolos = []

    for prot in prot_nfes:

        inf_prot_list = prot.xpath(
            "./*[local-name()='infProt']"
        )

        if not inf_prot_list:

            continue

        inf = inf_prot_list[0]

        protocolos.append(
            {
                "tpAmb":
                    _primeiro_texto(
                        inf,
                        "tpAmb"
                    ),

                "verAplic":
                    _primeiro_texto(
                        inf,
                        "verAplic"
                    ),

                "chNFe":
                    _primeiro_texto(
                        inf,
                        "chNFe"
                    ),

                "dhRecbto":
                    _primeiro_texto(
                        inf,
                        "dhRecbto"
                    ),

                "nProt":
                    _primeiro_texto(
                        inf,
                        "nProt"
                    ),

                "digVal":
                    _primeiro_texto(
                        inf,
                        "digVal"
                    ),

                "cStat":
                    _primeiro_texto(
                        inf,
                        "cStat"
                    ),

                "xMotivo":
                    _primeiro_texto(
                        inf,
                        "xMotivo"
                    )
            }
        )

    autorizado = any(
        protocolo.get(
            "cStat"
        )
        in (
            "100",
            "150"
        )
        for protocolo in protocolos
    )

    return {
        "sucesso_parse":
            True,

        "soap_fault":
            False,

        "tpAmb":
            tp_amb,

        "verAplic":
            ver_aplic,

        "cStat_lote":
            c_stat_lote,

        "xMotivo_lote":
            x_motivo_lote,

        "cUF":
            c_uf,

        "nRec":
            n_rec,

        "protocolos":
            protocolos,

        "autorizado":
            autorizado,

        "erros_parse":
            []
    }


# ============================================================
# CONSULTAR RECIBO DE AUTORIZAÇÃO - HOMOLOGAÇÃO MG
#
# IMPORTANTE:
# - NÃO transmite nova NF-e
# - apenas consulta um lote já recebido
# - NÃO altera banco
# - NÃO incrementa numeração
# ============================================================
def consultar_recibo_autorizacao_mg(
    numero_recibo,
    caminho_certificado,
    senha,
    ambiente=2,
    timeout=60
):

    try:

        numero_recibo = (
            _normalizar_numero_recibo(
                numero_recibo
            )
        )

        soap = gerar_soap_consulta_recibo(
            numero_recibo=numero_recibo,
            ambiente=ambiente
        )

    except Exception as erro:

        return {
            "sucesso_http": False,
            "consultado": False,
            "numero_recibo":
                numero_recibo,
            "http_status": None,
            "content_type": None,
            "resposta_bruta": None,
            "retorno": None,
            "erros": [
                (
                    "Falha ao preparar consulta "
                    "do recibo: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

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
            "application/soap+xml; charset=utf-8"
    }

    try:

        resposta = sessao.post(
            URL_RET_AUTORIZACAO_HOMOLOGACAO_MG,
            data=soap,
            headers=headers,
            timeout=timeout
        )

    except Exception as erro:

        return {
            "sucesso_http": False,
            "consultado": True,
            "numero_recibo":
                numero_recibo,
            "http_status": None,
            "content_type": None,
            "resposta_bruta": None,
            "retorno": None,
            "erros": [
                (
                    "Falha na comunicação com "
                    "NFeRetAutorizacao4: "
                    f"{type(erro).__name__}: {erro}"
                )
            ]
        }

    retorno = interpretar_retorno_consulta_recibo(
        resposta.text
    )

    return {
        "sucesso_http":
            resposta.status_code
            ==
            200,

        "consultado":
            True,

        "numero_recibo":
            numero_recibo,

        "http_status":
            resposta.status_code,

        "content_type":
            resposta.headers.get(
                "content-type"
            ),

        "resposta_bruta":
            resposta.text,

        "retorno":
            retorno,

        "erros":
            []
    }

