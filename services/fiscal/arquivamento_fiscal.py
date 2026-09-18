from pathlib import Path
from xml.etree import ElementTree as ET


NAMESPACE_NFE = {
    "nfe": "http://www.portalfiscal.inf.br/nfe"
}


# ============================================================
# NORMALIZAR XML
# ============================================================
def _ler_xml_xml_fiscal(xml):
    if isinstance(xml, Path):
        return xml.read_bytes()

    if isinstance(xml, bytes):
        return xml

    if isinstance(xml, str):
        caminho = Path(xml)

        if caminho.is_file():
            return caminho.read_bytes()

        return xml.encode("utf-8")

    raise TypeError(
        "XML fiscal deve ser caminho, texto ou bytes."
    )


# ============================================================
# EXTRAIR INFORMACOES DO XML AUTORIZADO
# ============================================================
def extrair_dados_arquivamento(xml_processado):
    conteudo = _ler_xml_xml_fiscal(
        xml_processado
    )

    raiz = ET.fromstring(conteudo)

    # O arquivo mensal deve receber somente XML processado
    # efetivamente autorizado pela SEFAZ.
    if raiz.tag != (
        "{http://www.portalfiscal.inf.br/nfe}nfeProc"
    ):
        raise ValueError(
            "XML informado nao e um nfeProc autorizado."
        )

    inf_prot = raiz.find(
        ".//nfe:protNFe/nfe:infProt",
        NAMESPACE_NFE
    )

    if inf_prot is None:
        raise ValueError(
            "Protocolo de autorizacao nao encontrado no XML."
        )

    elemento_cstat = inf_prot.find(
        "nfe:cStat",
        NAMESPACE_NFE
    )

    cstat = (
        (elemento_cstat.text or "").strip()
        if elemento_cstat is not None
        else ""
    )

    if cstat not in {"100", "150"}:
        raise ValueError(
            "XML fiscal nao esta autorizado. "
            f"cStat recebido: {cstat or 'ausente'}"
        )

    elemento_chave_protocolo = inf_prot.find(
        "nfe:chNFe",
        NAMESPACE_NFE
    )

    chave_protocolo = (
        (elemento_chave_protocolo.text or "").strip()
        if elemento_chave_protocolo is not None
        else ""
    )

    inf_nfe = raiz.find(
        ".//nfe:infNFe",
        NAMESPACE_NFE
    )

    if inf_nfe is None:
        raise ValueError(
            "infNFe nao encontrado no XML."
        )

    id_inf_nfe = (
        inf_nfe.attrib.get("Id") or ""
    ).strip()

    chave_inf_nfe = (
        id_inf_nfe[3:]
        if id_inf_nfe.startswith("NFe")
        else ""
    )

    if (
        not chave_inf_nfe
        or not chave_protocolo
        or chave_inf_nfe != chave_protocolo
    ):
        raise ValueError(
            "Chave do protocolo nao confere com "
            "a chave da NF-e/NFC-e."
        )

    ide = inf_nfe.find(
        "nfe:ide",
        NAMESPACE_NFE
    )

    if ide is None:
        raise ValueError(
            "ide nao encontrado no XML."
        )

    def texto(tag):
        elemento = ide.find(
            f"nfe:{tag}",
            NAMESPACE_NFE
        )

        if elemento is None:
            return None

        return (
            elemento.text or ""
        ).strip()

    modelo = int(
        texto("mod")
    )

    serie = int(
        texto("serie")
    )

    numero = int(
        texto("nNF")
    )

    dh_emi = texto(
        "dhEmi"
    )

    if not dh_emi:
        raise ValueError(
            "dhEmi nao encontrado no XML."
        )

    if modelo not in (55, 65):
        raise ValueError(
            f"Modelo fiscal nao suportado: {modelo}"
        )

    # dhEmi no leiaute NF-e:
    # AAAA-MM-DDTHH:MM:SS-03:00
    if len(dh_emi) < 7:
        raise ValueError(
            "dhEmi invalido."
        )

    ano = dh_emi[0:4]
    mes = dh_emi[5:7]

    if (
        not ano.isdigit()
        or not mes.isdigit()
        or int(mes) not in range(1, 13)
    ):
        raise ValueError(
            f"dhEmi invalido: {dh_emi}"
        )

    competencia = (
        f"{mes}{ano}"
    )

    tipo_documento = (
        "nfce"
        if modelo == 65
        else "nfe"
    )

    prefixo = (
        f"{tipo_documento}_{modelo}"
        f"_serie_{serie}"
        f"_numero_{numero}"
    )

    return {
        "modelo": modelo,
        "serie": serie,
        "numero": numero,
        "dhEmi": dh_emi,
        "competencia": competencia,
        "tipo_documento": tipo_documento,
        "prefixo": prefixo,
        "xml_bytes": conteudo,
    }


# ============================================================
# RESOLVER PASTAS FISCAIS
# ============================================================
def resolver_pastas_fiscais(
    xml_processado,
    diretorio_base="documentos_fiscais"
):
    dados = extrair_dados_arquivamento(
        xml_processado
    )

    base = Path(
        diretorio_base
    )

    pasta_documento = (
        base
        / dados["competencia"]
        / dados["tipo_documento"]
    )

    pasta_xml = (
        pasta_documento
        / "xml"
    )

    pasta_danfe = (
        pasta_documento
        / "danfe"
    )

    return {
        **dados,
        "diretorio_base": base,
        "pasta_documento": pasta_documento,
        "pasta_xml": pasta_xml,
        "pasta_danfe": pasta_danfe,
    }


# ============================================================
# ARQUIVAR XML PROCESSADO AUTORIZADO
# ============================================================
def arquivar_xml_processado(
    xml_processado,
    diretorio_base="documentos_fiscais"
):
    resultado = resolver_pastas_fiscais(
        xml_processado=xml_processado,
        diretorio_base=diretorio_base,
    )

    pasta_xml = resultado[
        "pasta_xml"
    ]

    pasta_danfe = resultado[
        "pasta_danfe"
    ]

    pasta_xml.mkdir(
        parents=True,
        exist_ok=True,
    )

    pasta_danfe.mkdir(
        parents=True,
        exist_ok=True,
    )

    caminho_xml = (
        pasta_xml
        / (
            resultado["prefixo"]
            + "_processada.xml"
        )
    )

    conteudo = resultado[
        "xml_bytes"
    ]

    # Idempotencia:
    # se o arquivo ja existe e for identico,
    # nao ha necessidade de regravar.
    if caminho_xml.exists():
        existente = (
            caminho_xml.read_bytes()
        )

        if existente != conteudo:
            raise FileExistsError(
                "Ja existe XML fiscal com o mesmo "
                "modelo/serie/numero, mas conteudo diferente: "
                f"{caminho_xml}"
            )

    else:
        caminho_xml.write_bytes(
            conteudo
        )

    return {
        "sucesso": True,
        "modelo": resultado["modelo"],
        "serie": resultado["serie"],
        "numero": resultado["numero"],
        "dhEmi": resultado["dhEmi"],
        "competencia":
            resultado["competencia"],
        "tipo_documento":
            resultado["tipo_documento"],
        "pasta_xml":
            str(pasta_xml),
        "pasta_danfe":
            str(pasta_danfe),
        "caminho_xml":
            str(caminho_xml),
        "prefixo":
            resultado["prefixo"],
    }
