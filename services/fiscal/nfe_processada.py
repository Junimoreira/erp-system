from copy import deepcopy
from pathlib import Path

from lxml import etree


NAMESPACE_NFE = "http://www.portalfiscal.inf.br/nfe"
NAMESPACE_DS = "http://www.w3.org/2000/09/xmldsig#"
VERSAO_NFE = "4.00"
CSTAT_AUTORIZADOS = {"100", "150"}


def _ler_xml(origem):
    if isinstance(origem, Path):
        if not origem.is_file():
            raise ValueError("Arquivo XML não encontrado.")
        return origem.read_bytes()

    if isinstance(origem, bytes):
        return origem

    if isinstance(origem, str):
        texto = origem.strip()
        if not texto:
            raise ValueError("XML não informado.")
        if texto.startswith("<"):
            return texto.encode("utf-8")
        caminho = Path(texto)
        if not caminho.is_file():
            raise ValueError("Arquivo XML não encontrado.")
        return caminho.read_bytes()

    if isinstance(origem, etree._Element):
        return etree.tostring(
            origem,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=False
        )

    if isinstance(origem, etree._ElementTree):
        return etree.tostring(
            origem.getroot(),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=False
        )

    raise ValueError("Tipo de origem XML não suportado.")


def _carregar_elemento(origem):
    parser = etree.XMLParser(
        remove_blank_text=False,
        resolve_entities=False,
        no_network=True
    )
    return etree.fromstring(
        _ler_xml(origem),
        parser
    )


def _primeiro_elemento(raiz, nome):
    elementos = raiz.xpath(
        ".//*[local-name()=$nome]",
        nome=nome
    )
    return elementos[0] if elementos else None


def _primeiro_texto(raiz, nome):
    elemento = _primeiro_elemento(
        raiz,
        nome
    )
    if elemento is None or elemento.text is None:
        return None
    texto = elemento.text.strip()
    return texto or None


def _validar_nfe_assinada(nfe):
    qname = etree.QName(nfe)

    if (
        qname.namespace != NAMESPACE_NFE
        or
        qname.localname != "NFe"
    ):
        raise ValueError(
            "O XML informado não possui elemento raiz NFe."
        )

    ns = {
        "nfe": NAMESPACE_NFE,
        "ds": NAMESPACE_DS
    }

    inf_nfe = nfe.find(
        "nfe:infNFe",
        ns
    )

    if inf_nfe is None:
        raise ValueError("A NF-e não possui infNFe.")

    id_infnfe = (
        inf_nfe.get("Id")
        or ""
    ).strip()

    if not id_infnfe.startswith("NFe"):
        raise ValueError("Id da infNFe inválido.")

    chave = id_infnfe[3:]

    if len(chave) != 44 or not chave.isdigit():
        raise ValueError(
            "Chave de acesso da NF-e inválida."
        )

    signature = nfe.find(
        "ds:Signature",
        ns
    )

    if signature is None:
        raise ValueError(
            "A NF-e ainda não possui assinatura digital."
        )

    digest_elementos = signature.xpath(
        "./ds:SignedInfo/ds:Reference/ds:DigestValue",
        namespaces=ns
    )

    if not digest_elementos:
        raise ValueError(
            "DigestValue não encontrado na assinatura."
        )

    digest_value = (
        digest_elementos[0].text
        or ""
    ).strip()

    if not digest_value:
        raise ValueError(
            "DigestValue da assinatura está vazio."
        )

    tp_amb = inf_nfe.findtext(
        "nfe:ide/nfe:tpAmb",
        namespaces=ns
    )

    return {
        "nfe": nfe,
        "id_infnfe": id_infnfe,
        "chave": chave,
        "digest_value": digest_value,
        "tp_amb": tp_amb.strip() if tp_amb else None
    }


def _extrair_protocolo(resposta_sefaz):
    raiz = _carregar_elemento(
        resposta_sefaz
    )

    protocolos = raiz.xpath(
        ".//*[local-name()='protNFe']"
    )

    if not protocolos:
        raise ValueError(
            "protNFe não encontrado na resposta da SEFAZ."
        )

    if len(protocolos) != 1:
        raise ValueError(
            "A resposta deve possuir exatamente um protNFe."
        )

    prot_nfe = protocolos[0]

    versao = (
        prot_nfe.get("versao")
        or ""
    ).strip()

    if versao != VERSAO_NFE:
        raise ValueError(
            f"Versão do protNFe incompatível: {versao or '?'}."
        )

    inf_prot = _primeiro_elemento(
        prot_nfe,
        "infProt"
    )

    if inf_prot is None:
        raise ValueError("protNFe sem infProt.")

    return {
        "prot_nfe": prot_nfe,
        "versao": versao,
        "c_stat": _primeiro_texto(inf_prot, "cStat"),
        "x_motivo": _primeiro_texto(inf_prot, "xMotivo"),
        "chave": _primeiro_texto(inf_prot, "chNFe"),
        "digest_value": _primeiro_texto(inf_prot, "digVal"),
        "n_prot": _primeiro_texto(inf_prot, "nProt"),
        "tp_amb": _primeiro_texto(inf_prot, "tpAmb")
    }


def _validar_compatibilidade(
    dados_nfe,
    dados_protocolo
):
    erros = []

    c_stat = dados_protocolo.get("c_stat")

    if c_stat not in CSTAT_AUTORIZADOS:
        erros.append(
            "O protocolo não representa uma NF-e autorizada. "
            f"cStat={c_stat or '?'} "
            f"xMotivo={dados_protocolo.get('x_motivo') or '?'}"
        )

    if not dados_protocolo.get("n_prot"):
        erros.append(
            "Protocolo autorizado sem nProt."
        )

    if (
        dados_protocolo.get("chave")
        !=
        dados_nfe.get("chave")
    ):
        erros.append(
            "A chave do protocolo não corresponde "
            "à chave da NF-e assinada."
        )

    if (
        dados_protocolo.get("digest_value")
        !=
        dados_nfe.get("digest_value")
    ):
        erros.append(
            "O digVal do protocolo não corresponde "
            "ao DigestValue da NF-e assinada."
        )

    if (
        dados_nfe.get("tp_amb")
        and
        dados_protocolo.get("tp_amb")
        and
        dados_nfe.get("tp_amb")
        !=
        dados_protocolo.get("tp_amb")
    ):
        erros.append(
            "O ambiente do protocolo não corresponde "
            "ao ambiente da NF-e."
        )

    return erros


def montar_nfe_processada(
    origem_nfe_assinada,
    resposta_sefaz
):
    try:
        nfe = _carregar_elemento(
            origem_nfe_assinada
        )

        dados_nfe = _validar_nfe_assinada(
            nfe
        )

        dados_protocolo = _extrair_protocolo(
            resposta_sefaz
        )

        erros = _validar_compatibilidade(
            dados_nfe,
            dados_protocolo
        )

        if erros:
            return {
                "sucesso": False,
                "xml": None,
                "chave_acesso": dados_nfe.get("chave"),
                "numero_protocolo": dados_protocolo.get("n_prot"),
                "c_stat": dados_protocolo.get("c_stat"),
                "x_motivo": dados_protocolo.get("x_motivo"),
                "erros": erros,
                "avisos": []
            }

        nfe_proc = etree.Element(
            etree.QName(
                NAMESPACE_NFE,
                "nfeProc"
            ),
            nsmap={
                None: NAMESPACE_NFE
            },
            versao=VERSAO_NFE
        )

        nfe_proc.append(
            deepcopy(
                dados_nfe["nfe"]
            )
        )

        nfe_proc.append(
            deepcopy(
                dados_protocolo["prot_nfe"]
            )
        )

        xml_bytes = etree.tostring(
            nfe_proc,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=False
        )

        return {
            "sucesso": True,
            "xml": xml_bytes.decode("utf-8"),
            "chave_acesso": dados_nfe["chave"],
            "id_infnfe": dados_nfe["id_infnfe"],
            "digest_value": dados_nfe["digest_value"],
            "numero_protocolo": dados_protocolo["n_prot"],
            "c_stat": dados_protocolo["c_stat"],
            "x_motivo": dados_protocolo["x_motivo"],
            "tp_amb": dados_protocolo["tp_amb"],
            "erros": [],
            "avisos": [
                "nfeProc montado localmente com NF-e assinada e protocolo autorizado da SEFAZ.",
                "Nenhuma transmissão foi realizada.",
                "Nenhum dado do banco foi alterado."
            ]
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "xml": None,
            "chave_acesso": None,
            "numero_protocolo": None,
            "c_stat": None,
            "x_motivo": None,
            "erros": [
                "Falha ao montar nfeProc: "
                f"{type(erro).__name__}: {erro}"
            ],
            "avisos": []
        }


def salvar_nfe_processada(
    resultado,
    caminho_saida
):
    if not isinstance(resultado, dict):
        raise ValueError(
            "Resultado do nfeProc inválido."
        )

    if not resultado.get("sucesso"):
        raise ValueError(
            "Não é possível salvar um nfeProc inválido."
        )

    xml = resultado.get("xml")

    if not xml:
        raise ValueError(
            "XML nfeProc não informado."
        )

    caminho = Path(
        caminho_saida
    )

    caminho.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho.write_text(
        xml,
        encoding="utf-8"
    )

    return caminho
