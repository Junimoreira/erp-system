from xml.etree.ElementTree import SubElement


# ============================================================
# INFORMACOES SUPLEMENTARES NFC-e
#
# Responsabilidade:
# - montar infNFeSupl da NFC-e modelo 65
# - montar URL do QR Code versao 3
# - manter regras especificas da NFC-e fora do gerador comum
#
# Nesta etapa:
# - somente emissao normal online (tpEmis = 1)
# - nenhuma transmissao para SEFAZ
# - nenhuma leitura/gravação em banco
# ============================================================


VERSAO_QRCODE_NFCE = "3"


URL_QRCODE_MG = {
    1: (
        "https://portalsped.fazenda.mg.gov.br/"
        "portalnfce/sistema/qrcode.xhtml"
    ),
    2: (
        "https://portalsped.fazenda.mg.gov.br/"
        "portalnfce/sistema/qrcode.xhtml"
    ),
}


URL_CONSULTA_NFCE_MG = {
    1: (
        "https://portalsped.fazenda.mg.gov.br/"
        "portalnfce"
    ),
    2: (
        "https://hportalsped.fazenda.mg.gov.br/"
        "portalnfce"
    ),
}


def _normalizar_tp_amb(tp_amb):

    try:
        tp_amb = int(tp_amb)
    except (TypeError, ValueError):
        raise ValueError(
            "tpAmb invalido para NFC-e. "
            "Use 1 para producao ou 2 para homologacao."
        )

    if tp_amb not in (1, 2):
        raise ValueError(
            "tpAmb invalido para NFC-e. "
            "Use 1 para producao ou 2 para homologacao."
        )

    return tp_amb


def _normalizar_chave_acesso(chave_acesso):

    chave = "".join(
        caractere
        for caractere in str(chave_acesso or "")
        if caractere.isdigit()
    )

    if len(chave) != 44:
        raise ValueError(
            "Chave de acesso da NFC-e deve possuir 44 digitos."
        )

    return chave


# ============================================================
# MONTAR URL QR CODE V3 - EMISSAO NORMAL ONLINE
# ============================================================
def montar_url_qrcode_nfce_online(
    chave_acesso,
    tp_amb
):

    chave = _normalizar_chave_acesso(
        chave_acesso
    )

    ambiente = _normalizar_tp_amb(
        tp_amb
    )

    parametros = "|".join(
        (
            chave,
            VERSAO_QRCODE_NFCE,
            str(ambiente)
        )
    )

    return (
        URL_QRCODE_MG[ambiente]
        + "?p="
        + parametros
    )


# ============================================================
# MONTAR infNFeSupl
# ============================================================
def montar_infnfe_supl_nfce(
    nfe,
    chave_acesso,
    tp_amb,
    tp_emis=1
):

    try:
        tp_emis = int(tp_emis)
    except (TypeError, ValueError):
        raise ValueError(
            "tpEmis invalido para NFC-e."
        )

    if tp_emis != 1:
        raise NotImplementedError(
            "Nesta etapa o ERP suporta infNFeSupl somente "
            "para NFC-e em emissao normal online (tpEmis=1)."
        )

    ambiente = _normalizar_tp_amb(
        tp_amb
    )

    qr_code = montar_url_qrcode_nfce_online(
        chave_acesso=chave_acesso,
        tp_amb=ambiente
    )

    inf_nfe_supl = SubElement(
        nfe,
        "infNFeSupl"
    )

    qr_code_elemento = SubElement(
        inf_nfe_supl,
        "qrCode"
    )

    qr_code_elemento.text = qr_code

    url_chave_elemento = SubElement(
        inf_nfe_supl,
        "urlChave"
    )

    url_chave_elemento.text = (
        URL_CONSULTA_NFCE_MG[
            ambiente
        ]
    )

    return inf_nfe_supl
