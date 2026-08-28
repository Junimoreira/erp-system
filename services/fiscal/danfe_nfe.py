from pathlib import Path
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128


NAMESPACE_NFE = "http://www.portalfiscal.inf.br/nfe"
NAMESPACE = {"nfe": NAMESPACE_NFE}
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOGO_PADRAO = BASE_DIR / "assets" / "logo1.png"

def _texto(elemento, caminho, default=""):
    if elemento is None:
        return default
    encontrado = elemento.find(caminho, NAMESPACE)
    if encontrado is None or encontrado.text is None:
        return default
    return str(encontrado.text).strip()


def _decimal(valor, padrao=Decimal("0.00")):
    if valor is None:
        return padrao
    texto = str(valor).strip().replace(",", ".")
    if not texto:
        return padrao
    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError, TypeError):
        return padrao


def _moeda(valor):
    numero = _decimal(valor)
    return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _numero(valor, casas=2):
    numero = _decimal(valor)
    return f"{numero:.{casas}f}".replace(".", ",")


def _somente_numeros(valor):
    return "".join(c for c in str(valor or "") if c.isdigit())


def _formatar_documento(valor):
    numero = _somente_numeros(valor)
    if len(numero) == 14:
        return f"{numero[0:2]}.{numero[2:5]}.{numero[5:8]}/{numero[8:12]}-{numero[12:14]}"
    if len(numero) == 11:
        return f"{numero[0:3]}.{numero[3:6]}.{numero[6:9]}-{numero[9:11]}"
    return valor or ""


def _formatar_cep(valor):
    numero = _somente_numeros(valor)
    if len(numero) != 8:
        return valor or ""
    return f"{numero[:5]}-{numero[5:]}"


def _formatar_chave(chave):
    numero = _somente_numeros(chave)
    if len(numero) != 44:
        return chave or ""
    return " ".join(numero[i:i+4] for i in range(0, 44, 4))


def _formatar_data_hora(valor):
    if not valor:
        return ""
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(valor).strip()).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(valor)


def _localizar_nfe(raiz):
    if raiz.tag.split("}")[-1] == "NFe":
        return raiz
    return raiz.find("nfe:NFe", NAMESPACE) or raiz.find(".//nfe:NFe", NAMESPACE)


def _localizar_protocolo(raiz):
    return raiz.find("nfe:protNFe/nfe:infProt", NAMESPACE) or raiz.find(".//nfe:protNFe/nfe:infProt", NAMESPACE)


def extrair_dados_danfe(caminho_xml):
    try:
        caminho_xml = Path(caminho_xml)
        if not caminho_xml.is_file():
            return {"sucesso": False, "erros": [f"XML não encontrado: {caminho_xml}"]}

        raiz = ET.parse(caminho_xml).getroot()
        nfe = _localizar_nfe(raiz)
        if nfe is None:
            return {"sucesso": False, "erros": ["Estrutura NFe não encontrada no XML."]}

        inf_nfe = nfe.find("nfe:infNFe", NAMESPACE)
        if inf_nfe is None:
            return {"sucesso": False, "erros": ["Grupo infNFe não encontrado."]}

        ide = inf_nfe.find("nfe:ide", NAMESPACE)
        emit = inf_nfe.find("nfe:emit", NAMESPACE)
        dest = inf_nfe.find("nfe:dest", NAMESPACE)
        total = inf_nfe.find("nfe:total/nfe:ICMSTot", NAMESPACE)
        total_ibs = inf_nfe.find("nfe:total/nfe:IBSCBSTot", NAMESPACE)
        prot = _localizar_protocolo(raiz)

        chave = inf_nfe.attrib.get("Id", "")
        if chave.startswith("NFe"):
            chave = chave[3:]
        chave_prot = _texto(prot, "nfe:chNFe") if prot is not None else ""
        if chave_prot:
            chave = chave_prot

        emit_end = emit.find("nfe:enderEmit", NAMESPACE) if emit is not None else None
        dest_end = dest.find("nfe:enderDest", NAMESPACE) if dest is not None else None
        emit_doc = _texto(emit, "nfe:CNPJ") or _texto(emit, "nfe:CPF")
        dest_doc = _texto(dest, "nfe:CNPJ") or _texto(dest, "nfe:CPF")

        itens = []
        for det in inf_nfe.findall("nfe:det", NAMESPACE):
            prod = det.find("nfe:prod", NAMESPACE)
            imposto = det.find("nfe:imposto", NAMESPACE)
            csosn = _texto(imposto, "nfe:ICMS/*/nfe:CSOSN") if imposto is not None else ""
            cst_icms = _texto(imposto, "nfe:ICMS/*/nfe:CST") if imposto is not None else ""
            itens.append({
                "numero_item": det.attrib.get("nItem", ""),
                "codigo": _texto(prod, "nfe:cProd"),
                "ean": _texto(prod, "nfe:cEAN"),
                "descricao": _texto(prod, "nfe:xProd"),
                "ncm": _texto(prod, "nfe:NCM"),
                "cest": _texto(prod, "nfe:CEST"),
                "cfop": _texto(prod, "nfe:CFOP"),
                "unidade": _texto(prod, "nfe:uCom"),
                "quantidade": _texto(prod, "nfe:qCom"),
                "valor_unitario": _texto(prod, "nfe:vUnCom"),
                "valor_produto": _texto(prod, "nfe:vProd"),
                "valor_desconto": _texto(prod, "nfe:vDesc", "0.00"),
                "csosn": csosn,
                "cst_icms": cst_icms,
                "cst_ibs_cbs": _texto(imposto.find("nfe:IBSCBS", NAMESPACE), "nfe:CST") if imposto is not None else "",
                "classificacao_tributaria": _texto(imposto.find("nfe:IBSCBS", NAMESPACE), "nfe:cClassTrib") if imposto is not None else "",
                "valor_ibs": _texto(imposto.find("nfe:IBSCBS", NAMESPACE), "nfe:gIBSCBS/nfe:vIBS", "0.00") if imposto is not None else "0.00",
                "valor_cbs": _texto(imposto.find("nfe:IBSCBS", NAMESPACE), "nfe:gIBSCBS/nfe:gCBS/nfe:vCBS", "0.00") if imposto is not None else "0.00",
            })

        det_pag = inf_nfe.find("nfe:pag/nfe:detPag", NAMESPACE)
        protocolo = _texto(prot, "nfe:nProt") if prot is not None else ""
        data_aut = _texto(prot, "nfe:dhRecbto") if prot is not None else ""
        cstat = _texto(prot, "nfe:cStat") if prot is not None else ""
        xmotivo = _texto(prot, "nfe:xMotivo") if prot is not None else ""

        return {
            "sucesso": True,
            "erros": [],
            "modelo": _texto(ide, "nfe:mod"),
            "serie": _texto(ide, "nfe:serie"),
            "numero": _texto(ide, "nfe:nNF"),
            "dh_emi": _texto(ide, "nfe:dhEmi"),
            "ambiente": _texto(ide, "nfe:tpAmb"),
            "natureza_operacao": _texto(ide, "nfe:natOp"),
            "chave": chave,
            "protocolo": protocolo,
            "data_autorizacao": data_aut,
            "cstat": cstat,
            "xmotivo": xmotivo,
            "emitente": {
                "razao_social": _texto(emit, "nfe:xNome"),
                "nome_fantasia": _texto(emit, "nfe:xFant"),
                "cnpj": _formatar_documento(emit_doc),
                "ie": _texto(emit, "nfe:IE"),
                "logradouro": _texto(emit_end, "nfe:xLgr"),
                "numero": _texto(emit_end, "nfe:nro"),
                "complemento": _texto(emit_end, "nfe:xCpl"),
                "bairro": _texto(emit_end, "nfe:xBairro"),
                "cidade": _texto(emit_end, "nfe:xMun"),
                "uf": _texto(emit_end, "nfe:UF"),
                "cep": _formatar_cep(_texto(emit_end, "nfe:CEP")),
            },
            "destinatario": {
                "nome": _texto(dest, "nfe:xNome"),
                "documento": _formatar_documento(dest_doc),
                "ie": _texto(dest, "nfe:IE"),
                "logradouro": _texto(dest_end, "nfe:xLgr"),
                "numero": _texto(dest_end, "nfe:nro"),
                "complemento": _texto(dest_end, "nfe:xCpl"),
                "bairro": _texto(dest_end, "nfe:xBairro"),
                "cidade": _texto(dest_end, "nfe:xMun"),
                "uf": _texto(dest_end, "nfe:UF"),
                "cep": _formatar_cep(_texto(dest_end, "nfe:CEP")),
            },
            "itens": itens,
            "totais": {
                "produtos": _texto(total, "nfe:vProd", "0.00"),
                "frete": _texto(total, "nfe:vFrete", "0.00"),
                "desconto": _texto(total, "nfe:vDesc", "0.00"),
                "icms": _texto(total, "nfe:vICMS", "0.00"),
                "nota": _texto(total, "nfe:vNF", "0.00"),
                "ibs": _texto(total_ibs, "nfe:vIBS", "0.00"),
                "cbs": _texto(total_ibs, "nfe:vCBS", "0.00"),
            },
            "pagamento": {
                "tipo": _texto(det_pag, "nfe:tPag"),
                "valor": _texto(det_pag, "nfe:vPag"),
            },
        }
    except Exception as erro:
        return {"sucesso": False, "erros": [f"Falha ao extrair dados do DANFE: {type(erro).__name__}: {erro}"]}


def _retangulo(c, x, y, largura, altura, espessura=0.6):
    c.setLineWidth(espessura)
    c.rect(x, y, largura, altura, stroke=1, fill=0)


def _linha(c, x1, y1, x2, y2, espessura=0.4):
    c.setLineWidth(espessura)
    c.line(x1, y1, x2, y2)


def _texto_pdf(c, x, y, texto, tamanho=7, negrito=False, alinhar="left"):
    c.setFont("Helvetica-Bold" if negrito else "Helvetica", tamanho)
    texto = str(texto or "")
    if alinhar == "right":
        c.drawRightString(x, y, texto)
    elif alinhar == "center":
        c.drawCentredString(x, y, texto)
    else:
        c.drawString(x, y, texto)


def _campo(c, x, y, largura, altura, titulo, valor, tamanho_valor=7, negrito_valor=False):
    _retangulo(c, x, y, largura, altura)
    _texto_pdf(c, x + 1.5*mm, y + altura - 3.2*mm, titulo.upper(), tamanho=5.5, negrito=True)
    _texto_pdf(c, x + 1.5*mm, y + 2.2*mm, valor, tamanho=tamanho_valor, negrito=negrito_valor)


def _endereco_texto(dados):
    partes = []
    logradouro = dados.get("logradouro")
    numero = dados.get("numero")
    complemento = dados.get("complemento")
    if logradouro:
        partes.append(str(logradouro) + (f", {numero}" if numero else ""))
    if complemento:
        partes.append(str(complemento))
    if dados.get("bairro"):
        partes.append(str(dados.get("bairro")))
    cidade = dados.get("cidade")
    uf = dados.get("uf")
    if cidade:
        partes.append(f"{cidade}/{uf}" if uf else str(cidade))
    if dados.get("cep"):
        partes.append(f"CEP {dados.get('cep')}")
    return " - ".join(partes)


def _desenhar_codigo_barras(c, chave, x, y, largura_max, altura=11*mm):
    chave = _somente_numeros(chave)
    if len(chave) != 44:
        return
    try:
        barra = code128.Code128(chave, barHeight=altura, barWidth=0.27*mm, humanReadable=False)
        escala = min(1.0, largura_max / barra.width)
        c.saveState()
        c.translate(x, y)
        if escala != 1.0:
            c.scale(escala, 1)
        barra.drawOn(c, 0, 0)
        c.restoreState()
    except Exception:
        pass


def _ajustar_texto_largura(
    c,
    texto,
    largura_max,
    tamanho=7,
    negrito=False,
):
    texto = str(texto or "").strip()

    if not texto:
        return ""

    fonte = (
        "Helvetica-Bold"
        if negrito
        else
        "Helvetica"
    )

    if c.stringWidth(
        texto,
        fonte,
        tamanho
    ) <= largura_max:
        return texto

    sufixo = "..."

    while texto:

        candidato = (
            texto
            +
            sufixo
        )

        if c.stringWidth(
            candidato,
            fonte,
            tamanho
        ) <= largura_max:
            return candidato

        texto = texto[:-1]

    return sufixo



def _quebrar_texto_linhas(
    c,
    texto,
    largura_max,
    tamanho=6,
    negrito=False,
    max_linhas=2,
):
    texto = str(texto or "").strip()

    if not texto:
        return [""]

    fonte = (
        "Helvetica-Bold"
        if negrito
        else
        "Helvetica"
    )

    palavras = texto.split()
    linhas = []
    atual = ""

    for palavra in palavras:
        candidato = (
            palavra
            if not atual
            else
            f"{atual} {palavra}"
        )

        if c.stringWidth(
            candidato,
            fonte,
            tamanho
        ) <= largura_max:
            atual = candidato
        else:
            if atual:
                linhas.append(atual)
            atual = palavra

            if len(linhas) >= max_linhas - 1:
                break

    if atual and len(linhas) < max_linhas:
        linhas.append(atual)

    if len(linhas) > max_linhas:
        linhas = linhas[:max_linhas]

    # Se o texto original não coube integralmente, aplica reticências
    reconstruido = " ".join(linhas).strip()

    if reconstruido != texto and linhas:
        ultima = linhas[-1]
        sufixo = "..."

        while ultima and c.stringWidth(
            ultima + sufixo,
            fonte,
            tamanho
        ) > largura_max:
            ultima = ultima[:-1]

        linhas[-1] = (
            ultima + sufixo
            if ultima
            else sufixo
        )

    return linhas


def _campo_profissional(
    c,
    x,
    y,
    largura,
    altura,
    titulo,
    valor,
    tamanho_valor=7,
    negrito_valor=False,
    alinhar="left",
):
    _retangulo(
        c,
        x,
        y,
        largura,
        altura,
        espessura=0.45
    )

    _texto_pdf(
        c,
        x + 1.4*mm,
        y + altura - 3.0*mm,
        titulo.upper(),
        tamanho=5.2,
        negrito=True
    )

    valor_ajustado = _ajustar_texto_largura(
        c,
        valor,
        largura - 3*mm,
        tamanho=tamanho_valor,
        negrito=negrito_valor
    )

    if alinhar == "right":

        _texto_pdf(
            c,
            x + largura - 1.4*mm,
            y + 2.4*mm,
            valor_ajustado,
            tamanho=tamanho_valor,
            negrito=negrito_valor,
            alinhar="right"
        )

    elif alinhar == "center":

        _texto_pdf(
            c,
            x + largura/2,
            y + 2.4*mm,
            valor_ajustado,
            tamanho=tamanho_valor,
            negrito=negrito_valor,
            alinhar="center"
        )

    else:

        _texto_pdf(
            c,
            x + 1.4*mm,
            y + 2.4*mm,
            valor_ajustado,
            tamanho=tamanho_valor,
            negrito=negrito_valor
        )


def _desenhar_pagina(
    c,
    dados,
    pagina,
    total_paginas,
    itens_pagina
):
    largura_pagina, altura_pagina = A4

    margem = 7*mm
    largura_util = (
        largura_pagina
        -
        2*margem
    )

    y = (
        altura_pagina
        -
        margem
    )

    # ========================================================
    # MARCA D'ÁGUA DE HOMOLOGAÇÃO
    # ========================================================
    if str(
        dados.get(
            "ambiente"
        )
    ) == "2":

        c.saveState()

        c.setFillColor(
            colors.Color(
                0.88,
                0.88,
                0.88,
                alpha=0.38
            )
        )

        c.setFont(
            "Helvetica-Bold",
            29
        )

        c.translate(
            largura_pagina/2,
            altura_pagina/2
        )

        c.rotate(
            45
        )

        c.drawCentredString(
            0,
            0,
            "HOMOLOGAÇÃO - SEM VALOR FISCAL"
        )

        c.restoreState()

    # ========================================================
    # CABEÇALHO
    # ========================================================
    cab_h = 43*mm

    _retangulo(
        c,
        margem,
        y-cab_h,
        largura_util,
        cab_h,
        espessura=0.85
    )

    bloco_emit_w = 86*mm
    bloco_danfe_w = 34*mm
    bloco_chave_w = (
        largura_util
        -
        bloco_emit_w
        -
        bloco_danfe_w
    )

    x_emit = margem
    x_danfe = (
        x_emit
        +
        bloco_emit_w
    )
    x_chave = (
        x_danfe
        +
        bloco_danfe_w
    )

    _linha(
        c,
        x_danfe,
        y-cab_h,
        x_danfe,
        y,
        espessura=0.55
    )

    _linha(
        c,
        x_chave,
        y-cab_h,
        x_chave,
        y,
        espessura=0.55
    )

    # --------------------------------------------------------
    # EMITENTE
    #
    # Layout:
    # - logo grande à esquerda
    # - dados cadastrais compactos à direita
    # - tudo dentro do mesmo bloco do emitente
    # --------------------------------------------------------
    emit = dados.get(
        "emitente",
        {}
    )

    # --------------------------------------------------------
    # ÁREA DA LOGO
    # --------------------------------------------------------
    logo_w = 35*mm
    logo_h = 36*mm

    if LOGO_PADRAO.is_file():

        try:

            c.drawImage(
                str(
                    LOGO_PADRAO
                ),
                x_emit + 3*mm,
                y - 39*mm,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto"
            )

        except Exception:
            pass

    # --------------------------------------------------------
    # ÁREA DOS DADOS DO EMITENTE
    # --------------------------------------------------------
    x_dados_emit = (
        x_emit
        +
        43*mm
    )

    largura_dados_emit = (
        bloco_emit_w
        -
        46*mm
    )

    nome_fantasia = (
        emit.get(
            "nome_fantasia"
        )
        or
        emit.get(
            "razao_social"
        )
    )

    nome_fantasia = _ajustar_texto_largura(
        c,
        nome_fantasia,
        largura_dados_emit,
        tamanho=9.5,
        negrito=True
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 6.5*mm,
        nome_fantasia,
        tamanho=9.5,
        negrito=True
    )

    razao = _ajustar_texto_largura(
        c,
        emit.get(
            "razao_social"
        ),
        largura_dados_emit,
        tamanho=6.2
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 11.5*mm,
        razao,
        tamanho=6.2
    )

    doc_emit = (
        f"CNPJ: {emit.get('cnpj','')}"
    )

    doc_emit = _ajustar_texto_largura(
        c,
        doc_emit,
        largura_dados_emit,
        tamanho=6.0,
        negrito=True
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 17.5*mm,
        doc_emit,
        tamanho=6.0,
        negrito=True
    )

    ie_emit = (
        f"IE: {emit.get('ie','')}"
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 22.5*mm,
        ie_emit,
        tamanho=6.0
    )

    endereco_emit = (
        f"{emit.get('logradouro','')}, "
        f"{emit.get('numero','')}"
    )

    if emit.get(
        "bairro"
    ):

        endereco_emit += (
            f" - {emit.get('bairro')}"
        )

    endereco_emit = _ajustar_texto_largura(
        c,
        endereco_emit,
        largura_dados_emit,
        tamanho=5.8
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 28.5*mm,
        endereco_emit,
        tamanho=5.8
    )

    cidade_emit = (
        f"{emit.get('cidade','')}"
        f"/{emit.get('uf','')}"
    )

    cidade_emit = _ajustar_texto_largura(
        c,
        cidade_emit,
        largura_dados_emit,
        tamanho=5.8
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 33.5*mm,
        cidade_emit,
        tamanho=5.8
    )

    cep_emit = (
        f"CEP: {emit.get('cep','')}"
    )

    _texto_pdf(
        c,
        x_dados_emit,
        y - 38.5*mm,
        cep_emit,
        tamanho=5.8
    )

    # --------------------------------------------------------
    # BLOCO DANFE
    # --------------------------------------------------------
    _texto_pdf(
        c,
        x_danfe + bloco_danfe_w/2,
        y - 7*mm,
        "DANFE",
        tamanho=15,
        negrito=True,
        alinhar="center"
    )

    _texto_pdf(
        c,
        x_danfe + bloco_danfe_w/2,
        y - 12*mm,
        "Documento Auxiliar",
        tamanho=6.0,
        alinhar="center"
    )

    _texto_pdf(
        c,
        x_danfe + bloco_danfe_w/2,
        y - 16*mm,
        "da Nota Fiscal Eletrônica",
        tamanho=6.0,
        alinhar="center"
    )

    _texto_pdf(
        c,
        x_danfe + 3*mm,
        y - 23*mm,
        "0 - ENTRADA",
        tamanho=6.1
    )

    _texto_pdf(
        c,
        x_danfe + 3*mm,
        y - 27*mm,
        "1 - SAÍDA",
        tamanho=6.1,
        negrito=True
    )

    _retangulo(
        c,
        x_danfe + bloco_danfe_w - 9*mm,
        y - 29*mm,
        6*mm,
        8*mm,
        espessura=0.55
    )

    _texto_pdf(
        c,
        x_danfe + bloco_danfe_w - 6*mm,
        y - 26.5*mm,
        "1",
        tamanho=12,
        negrito=True,
        alinhar="center"
    )

    _texto_pdf(
        c,
        x_danfe + bloco_danfe_w/2,
        y - 35*mm,
        f"Nº {dados.get('numero','')}",
        tamanho=8.2,
        negrito=True,
        alinhar="center"
    )

    _texto_pdf(
        c,
        x_danfe + bloco_danfe_w/2,
        y - 39*mm,
        f"Série {dados.get('serie','')}",
        tamanho=7.0,
        negrito=True,
        alinhar="center"
    )

    # --------------------------------------------------------
    # CHAVE / PROTOCOLO
    # --------------------------------------------------------
    _texto_pdf(
        c,
        x_chave + 2*mm,
        y - 4*mm,
        "CHAVE DE ACESSO",
        tamanho=5.3,
        negrito=True
    )

    _desenhar_codigo_barras(
        c,
        dados.get(
            "chave"
        ),
        x_chave + 2*mm,
        y - 17*mm,
        bloco_chave_w - 4*mm,
        altura=9.5*mm
    )

    _texto_pdf(
        c,
        x_chave + bloco_chave_w/2,
        y - 21*mm,
        _formatar_chave(
            dados.get(
                "chave"
            )
        ),
        tamanho=5.9,
        alinhar="center"
    )

    _linha(
        c,
        x_chave,
        y - 24*mm,
        x_chave + bloco_chave_w,
        y - 24*mm,
        espessura=0.35
    )

    protocolo_txt = (
        dados.get(
            "protocolo"
        )
        or
        "SEM PROTOCOLO DE AUTORIZAÇÃO"
    )

    if (
        dados.get(
            "protocolo"
        )
        and
        dados.get(
            "data_autorizacao"
        )
    ):

        protocolo_txt += (
            " - "
            +
            _formatar_data_hora(
                dados.get(
                    "data_autorizacao"
                )
            )
        )

    protocolo_txt = _ajustar_texto_largura(
        c,
        protocolo_txt,
        bloco_chave_w - 4*mm,
        tamanho=6.0,
        negrito=bool(
            dados.get(
                "protocolo"
            )
        )
    )

    _texto_pdf(
        c,
        x_chave + 2*mm,
        y - 28*mm,
        "PROTOCOLO DE AUTORIZAÇÃO DE USO",
        tamanho=5.2,
        negrito=True
    )

    _texto_pdf(
        c,
        x_chave + 2*mm,
        y - 33*mm,
        protocolo_txt,
        tamanho=6.0,
        negrito=bool(
            dados.get(
                "protocolo"
            )
        )
    )

    if dados.get(
        "cstat"
    ):

        _texto_pdf(
            c,
            x_chave + 2*mm,
            y - 38*mm,
            (
                f"cStat {dados.get('cstat')} - "
                f"{dados.get('xmotivo','')}"
            )[:70],
            tamanho=5.7
        )

    y -= (
        cab_h
        +
        2*mm
    )

    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================
    _campo_profissional(
        c,
        margem,
        y - 10*mm,
        103*mm,
        10*mm,
        "Natureza da operação",
        dados.get(
            "natureza_operacao"
        ),
        tamanho_valor=7.0,
        negrito_valor=True
    )

    _campo_profissional(
        c,
        margem + 103*mm,
        y - 10*mm,
        largura_util - 103*mm,
        10*mm,
        "Data de emissão",
        _formatar_data_hora(
            dados.get(
                "dh_emi"
            )
        ),
        tamanho_valor=7.0
    )

    y -= 12*mm

    # ========================================================
    # DESTINATÁRIO
    # ========================================================
    _texto_pdf(
        c,
        margem,
        y,
        "DESTINATÁRIO / REMETENTE",
        tamanho=6.0,
        negrito=True
    )

    y -= 1.5*mm

    dest = dados.get(
        "destinatario",
        {}
    )

    altura_dest = 25*mm

    _retangulo(
        c,
        margem,
        y-altura_dest,
        largura_util,
        altura_dest,
        espessura=0.5
    )

    _linha(
        c,
        margem,
        y-10*mm,
        margem+largura_util,
        y-10*mm
    )

    _linha(
        c,
        margem+126*mm,
        y-altura_dest,
        margem+126*mm,
        y
    )

    _texto_pdf(
        c,
        margem+1.5*mm,
        y-3*mm,
        "NOME / RAZÃO SOCIAL",
        tamanho=5.1,
        negrito=True
    )

    nome_dest = _ajustar_texto_largura(
        c,
        dest.get(
            "nome"
        ),
        122*mm,
        tamanho=7.0,
        negrito=True
    )

    _texto_pdf(
        c,
        margem+1.5*mm,
        y-7.5*mm,
        nome_dest,
        tamanho=7.0,
        negrito=True
    )

    _texto_pdf(
        c,
        margem+127.5*mm,
        y-3*mm,
        "CPF / CNPJ",
        tamanho=5.1,
        negrito=True
    )

    _texto_pdf(
        c,
        margem+127.5*mm,
        y-7.5*mm,
        dest.get(
            "documento"
        ),
        tamanho=7.0
    )

    _texto_pdf(
        c,
        margem+1.5*mm,
        y-13*mm,
        "ENDEREÇO",
        tamanho=5.1,
        negrito=True
    )

    endereco_dest = _ajustar_texto_largura(
        c,
        _endereco_texto(
            dest
        ),
        122*mm,
        tamanho=6.3
    )

    _texto_pdf(
        c,
        margem+1.5*mm,
        y-18*mm,
        endereco_dest,
        tamanho=6.3
    )

    _texto_pdf(
        c,
        margem+127.5*mm,
        y-13*mm,
        "INSCRIÇÃO ESTADUAL",
        tamanho=5.1,
        negrito=True
    )

    _texto_pdf(
        c,
        margem+127.5*mm,
        y-18*mm,
        dest.get(
            "ie"
        ),
        tamanho=6.3
    )

    y -= (
        altura_dest
        +
        3*mm
    )

    # ========================================================
    # CÁLCULO DO IMPOSTO
    # ========================================================
    _texto_pdf(
        c,
        margem,
        y,
        "CÁLCULO DO IMPOSTO",
        tamanho=6.0,
        negrito=True
    )

    y -= 1.5*mm

    totais = dados.get(
        "totais",
        {}
    )

    larg_campo = (
        largura_util
        /
        5
    )

    campos = [
        (
            "VALOR DOS PRODUTOS",
            _moeda(
                totais.get(
                    "produtos"
                )
            )
        ),
        (
            "DESCONTO",
            _moeda(
                totais.get(
                    "desconto"
                )
            )
        ),
        (
            "FRETE",
            _moeda(
                totais.get(
                    "frete"
                )
            )
        ),
        (
            "VALOR DO ICMS",
            _moeda(
                totais.get(
                    "icms"
                )
            )
        ),
        (
            "VALOR TOTAL DA NF-e",
            _moeda(
                totais.get(
                    "nota"
                )
            )
        ),
    ]

    for i, (
        titulo,
        valor
    ) in enumerate(
        campos
    ):

        _campo_profissional(
            c,
            margem + i*larg_campo,
            y - 12*mm,
            larg_campo,
            12*mm,
            titulo,
            valor,
            tamanho_valor=7.3,
            negrito_valor=(
                titulo
                ==
                "VALOR TOTAL DA NF-e"
            ),
            alinhar="right"
        )

    y -= 15*mm

    # --------------------------------------------------------
    # IBS/CBS - somente quando houver informação efetiva
    # --------------------------------------------------------
    informar_ibs_cbs = (
        _decimal(
            totais.get(
                "ibs"
            )
        )
        >
        Decimal("0")
        or
        _decimal(
            totais.get(
                "cbs"
            )
        )
        >
        Decimal("0")
    )

    if informar_ibs_cbs:

        _campo_profissional(
            c,
            margem,
            y - 10*mm,
            largura_util/2,
            10*mm,
            "Valor IBS",
            _moeda(
                totais.get(
                    "ibs"
                )
            ),
            tamanho_valor=7.2,
            negrito_valor=True,
            alinhar="right"
        )

        _campo_profissional(
            c,
            margem + largura_util/2,
            y - 10*mm,
            largura_util/2,
            10*mm,
            "Valor CBS",
            _moeda(
                totais.get(
                    "cbs"
                )
            ),
            tamanho_valor=7.2,
            negrito_valor=True,
            alinhar="right"
        )

        y -= 13*mm

    # ========================================================
    # PRODUTOS
    # ========================================================
    _texto_pdf(
        c,
        margem,
        y,
        "DADOS DOS PRODUTOS / SERVIÇOS",
        tamanho=6.0,
        negrito=True
    )

    y -= 1.5*mm

    # Distribuição otimizada das colunas para privilegiar
    # a descrição dos produtos sem perder os dados fiscais.
    colunas = [
        (
            "CÓD.",
            12*mm
        ),
        (
            "DESCRIÇÃO",
            64*mm
        ),
        (
            "NCM",
            17*mm
        ),
        (
            "CST/CSOSN",
            15*mm
        ),
        (
            "CFOP",
            11*mm
        ),
        (
            "UN",
            7*mm
        ),
        (
            "QTD.",
            14*mm
        ),
        (
            "V.UNIT.",
            17*mm
        ),
        (
            "DESC.",
            15*mm
        ),
        (
            "V.TOTAL",
            21*mm
        ),
    ]

    altura_cab = 7.5*mm

    x = margem

    for titulo, largura in colunas:

        _retangulo(
            c,
            x,
            y-altura_cab,
            largura,
            altura_cab,
            espessura=0.4
        )

        _texto_pdf(
            c,
            x+largura/2,
            y-4.5*mm,
            titulo,
            tamanho=4.7,
            negrito=True,
            alinhar="center"
        )

        x += largura

    y -= altura_cab

    altura_item = 11*mm

    for item in itens_pagina:

        cst_csosn = (
            item.get(
                "csosn"
            )
            or
            item.get(
                "cst_icms"
            )
            or
            ""
        )

        valores = [
            item.get(
                "codigo",
                ""
            ),
            item.get(
                "descricao",
                ""
            ),
            item.get(
                "ncm",
                ""
            ),
            cst_csosn,
            item.get(
                "cfop",
                ""
            ),
            item.get(
                "unidade",
                ""
            ),
            _numero(
                item.get(
                    "quantidade"
                ),
                4
            ),
            _numero(
                item.get(
                    "valor_unitario"
                ),
                2
            ),
            _numero(
                item.get(
                    "valor_desconto"
                ),
                2
            ),
            _numero(
                item.get(
                    "valor_produto"
                ),
                2
            ),
        ]

        x = margem

        for i, (
            titulo,
            largura
        ) in enumerate(
            colunas
        ):

            _retangulo(
                c,
                x,
                y-altura_item,
                largura,
                altura_item,
                espessura=0.35
            )

            valor = str(
                valores[i]
                or
                ""
            )

            if titulo == "DESCRIÇÃO":

                linhas_desc = _quebrar_texto_linhas(
                    c,
                    valor,
                    largura - 2*mm,
                    tamanho=5.7,
                    max_linhas=2
                )

                if len(linhas_desc) == 1:

                    _texto_pdf(
                        c,
                        x+1*mm,
                        y-6.0*mm,
                        linhas_desc[0],
                        tamanho=5.7
                    )

                else:

                    _texto_pdf(
                        c,
                        x+1*mm,
                        y-4.2*mm,
                        linhas_desc[0],
                        tamanho=5.7
                    )

                    _texto_pdf(
                        c,
                        x+1*mm,
                        y-7.6*mm,
                        linhas_desc[1],
                        tamanho=5.7
                    )

            elif titulo in (
                "QTD.",
                "V.UNIT.",
                "DESC.",
                "V.TOTAL"
            ):

                _texto_pdf(
                    c,
                    x+largura-1*mm,
                    y-6.0*mm,
                    valor,
                    tamanho=5.5,
                    alinhar="right"
                )

            else:

                _texto_pdf(
                    c,
                    x+largura/2,
                    y-6.0*mm,
                    valor,
                    tamanho=5.2,
                    alinhar="center"
                )

            x += largura

        y -= altura_item

    # ========================================================
    # PAGAMENTO
    # ========================================================
    y -= 3*mm

    pagamento = dados.get(
        "pagamento",
        {}
    )

    tipos = {
        "01": "Dinheiro",
        "03": "Cartão de crédito",
        "04": "Cartão de débito",
        "05": "Crédito loja",
        "15": "Boleto bancário",
        "16": "Depósito bancário",
        "17": "PIX",
        "18": "Transferência bancária",
        "90": "Sem pagamento",
        "99": "Outros",
    }

    descricao_pag = tipos.get(
        pagamento.get(
            "tipo"
        ),
        pagamento.get(
            "tipo"
        )
        or
        ""
    )

    _campo_profissional(
        c,
        margem,
        y-11*mm,
        largura_util/2,
        11*mm,
        "Forma de pagamento",
        descricao_pag,
        tamanho_valor=7.0,
        negrito_valor=True
    )

    _campo_profissional(
        c,
        margem+largura_util/2,
        y-11*mm,
        largura_util/2,
        11*mm,
        "Valor pago",
        _moeda(
            pagamento.get(
                "valor"
            )
        ),
        tamanho_valor=7.4,
        negrito_valor=True,
        alinhar="right"
    )

    # ========================================================
    # INFORMAÇÕES COMPLEMENTARES
    # ========================================================
    y -= 15*mm

    altura_rodape = 26*mm

    base_rodape_y = max(
        14*mm,
        y-altura_rodape
    )

    _retangulo(
        c,
        margem,
        base_rodape_y,
        largura_util,
        altura_rodape,
        espessura=0.5
    )

    _texto_pdf(
        c,
        margem+1.5*mm,
        base_rodape_y + altura_rodape - 3.5*mm,
        "INFORMAÇÕES COMPLEMENTARES",
        tamanho=5.4,
        negrito=True
    )

    msg = (
        "Documento Auxiliar da Nota Fiscal Eletrônica. "
        "Consulte a autenticidade pela chave de acesso."
    )

    if str(
        dados.get(
            "ambiente"
        )
    ) == "2":

        msg += (
            " EMITIDO EM AMBIENTE DE HOMOLOGAÇÃO "
            "- SEM VALOR FISCAL."
        )

    linhas_info = _quebrar_texto_linhas(
        c,
        msg,
        largura_util - 3*mm,
        tamanho=6.1,
        max_linhas=2
    )

    for indice_linha, linha_info in enumerate(
        linhas_info
    ):

        _texto_pdf(
            c,
            margem+1.5*mm,
            base_rodape_y
            +
            altura_rodape
            -
            (
                9
                +
                indice_linha*4
            )*mm,
            linha_info,
            tamanho=6.1
        )

    if informar_ibs_cbs:

        _texto_pdf(
            c,
            margem+1.5*mm,
            base_rodape_y + 8*mm,
            (
                f"IBS: {_moeda(totais.get('ibs'))}    "
                f"CBS: {_moeda(totais.get('cbs'))}"
            ),
            tamanho=6.1,
            negrito=True
        )

    if dados.get(
        "protocolo"
    ):

        _texto_pdf(
            c,
            margem+1.5*mm,
            base_rodape_y + 4*mm,
            (
                "NF-e autorizada. "
                f"Protocolo: {dados.get('protocolo')}"
            ),
            tamanho=5.8
        )

    # ========================================================
    # RODAPÉ
    # ========================================================
    _texto_pdf(
        c,
        margem,
        6.5*mm,
        "ERP Verde Infância",
        tamanho=5.8
    )

    _texto_pdf(
        c,
        largura_pagina-margem,
        6.5*mm,
        f"Página {pagina}/{total_paginas}",
        tamanho=5.8,
        alinhar="right"
    )


def gerar_danfe_nfe(caminho_xml, caminho_pdf):
    try:
        caminho_xml = Path(caminho_xml)
        caminho_pdf = Path(caminho_pdf)
        dados = extrair_dados_danfe(caminho_xml)
        if not dados.get("sucesso"):
            return {"sucesso": False, "erros": dados.get("erros", []), "avisos": []}

        caminho_pdf.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(caminho_pdf), pagesize=A4)
        c.setTitle(f"DANFE {dados.get('numero','')}")
        itens = dados.get("itens", [])
        itens_por_pagina = 10
        paginas = [itens[i:i+itens_por_pagina] for i in range(0, len(itens), itens_por_pagina)] if itens else [[]]
        total_paginas = len(paginas)
        for indice, itens_pagina in enumerate(paginas, start=1):
            _desenhar_pagina(c, dados, indice, total_paginas, itens_pagina)
            c.showPage()
        c.save()

        avisos = []
        if not dados.get("protocolo"):
            avisos.append("DANFE gerado sem protocolo de autorização. Trata-se de prévia sem validade fiscal.")
        if str(dados.get("ambiente")) == "2":
            avisos.append("DANFE emitido em ambiente de homologação - sem valor fiscal.")

        return {
            "sucesso": True,
            "caminho_pdf": str(caminho_pdf),
            "chave": dados.get("chave"),
            "protocolo": dados.get("protocolo"),
            "modelo": dados.get("modelo"),
            "serie": dados.get("serie"),
            "numero": dados.get("numero"),
            "ambiente": dados.get("ambiente"),
            "erros": [],
            "avisos": avisos,
        }
    except Exception as erro:
        return {
            "sucesso": False,
            "caminho_pdf": None,
            "protocolo": None,
            "erros": [f"Falha ao gerar DANFE: {type(erro).__name__}: {erro}"],
            "avisos": [],
        }