from decimal import Decimal, InvalidOperation
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "nfe": "http://www.portalfiscal.inf.br/nfe"
}


FORMAS_PAGAMENTO = {
    "01": "Dinheiro",
    "02": "Cheque",
    "03": "Cartão de Crédito",
    "04": "Cartão de Débito",
    "05": "Crédito Loja",
    "10": "Vale Alimentação",
    "11": "Vale Refeição",
    "12": "Vale Presente",
    "13": "Vale Combustivel",
    "15": "Boleto Bancario",
    "16": "Depósito Bancário",
    "17": "PIX",
    "18": "Transferência bancária / Carteira Digital",
    "19": "Programa de fidelidade / Cashback",
    "90": "Sem pagamento",
    "99": "Outros",
}


def _texto(elemento, caminho, default=""):
    if elemento is None:
        return default

    encontrado = elemento.find(caminho, NS)

    if encontrado is None or encontrado.text is None:
        return default

    return encontrado.text.strip()


def _decimal(valor, padrao=Decimal("0.00")):
    try:
        if valor in (None, ""):
            return padrao

        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return padrao


def _somente_numeros(valor):
    return "".join(
        caractere
        for caractere in str(valor or "")
        if caractere.isdigit()
    )


def _formatar_cnpj(valor):
    numeros = _somente_numeros(valor)

    if len(numeros) != 14:
        return str(valor or "")

    return (
        f"{numeros[0:2]}.{numeros[2:5]}.{numeros[5:8]}/"
        f"{numeros[8:12]}-{numeros[12:14]}"
    )


def _formatar_cpf(valor):
    numeros = _somente_numeros(valor)

    if len(numeros) != 11:
        return str(valor or "")

    return (
        f"{numeros[0:3]}.{numeros[3:6]}.{numeros[6:9]}-"
        f"{numeros[9:11]}"
    )


def _formatar_chave(valor):
    numeros = _somente_numeros(valor)

    if len(numeros) != 44:
        return str(valor or "")

    return " ".join(
        numeros[indice:indice + 4]
        for indice in range(0, 44, 4)
    )


def _localizar_nfe(raiz):
    if raiz.tag.endswith("NFe"):
        return raiz

    return raiz.find(".//nfe:NFe", NS)


def _localizar_protocolo(raiz):
    return raiz.find(
        ".//nfe:protNFe/nfe:infProt",
        NS,
    )


def extrair_dados_danfe_nfce(caminho_xml):
    caminho_xml = Path(caminho_xml)

    if not caminho_xml.is_file():
        return {
            "sucesso": False,
            "erros": [
                f"XML nao encontrado: {caminho_xml}"
            ],
            "avisos": [],
        }

    try:
        raiz = ET.parse(caminho_xml).getroot()
    except Exception as erro:
        return {
            "sucesso": False,
            "erros": [
                "Falha ao ler XML NFC-e: "
                f"{type(erro).__name__}: {erro}"
            ],
            "avisos": [],
        }

    nfe = _localizar_nfe(raiz)

    if nfe is None:
        return {
            "sucesso": False,
            "erros": ["Elemento NFe nao encontrado no XML."],
            "avisos": [],
        }

    inf_nfe = nfe.find("nfe:infNFe", NS)

    if inf_nfe is None:
        return {
            "sucesso": False,
            "erros": ["Elemento infNFe nao encontrado."],
            "avisos": [],
        }

    ide = inf_nfe.find("nfe:ide", NS)
    emit = inf_nfe.find("nfe:emit", NS)
    dest = inf_nfe.find("nfe:dest", NS)
    total = inf_nfe.find("nfe:total/nfe:ICMSTot", NS)
    protocolo = _localizar_protocolo(raiz)

    modelo = _texto(ide, "nfe:mod")

    if modelo != "65":
        return {
            "sucesso": False,
            "erros": [
                f"XML nao e NFC-e modelo 65. Modelo encontrado: {modelo or '-'}"
            ],
            "avisos": [],
        }

    chave = _somente_numeros(
        inf_nfe.get("Id", "")
    )

    if chave.startswith("NFe"):
        chave = chave[3:]

    if not chave and protocolo is not None:
        chave = _texto(
            protocolo,
            "nfe:chNFe",
        )

    itens = []

    for det in inf_nfe.findall("nfe:det", NS):
        prod = det.find("nfe:prod", NS)

        if prod is None:
            continue

        itens.append(
            {
                "numero": det.get("nItem", ""),
                "codigo": _texto(prod, "nfe:cProd"),
                "descricao": _texto(prod, "nfe:xProd"),
                "quantidade": _decimal(
                    _texto(prod, "nfe:qCom")
                ),
                "unidade": _texto(prod, "nfe:uCom"),
                "valor_unitario": _decimal(
                    _texto(prod, "nfe:vUnCom")
                ),
                "valor_produto": _decimal(
                    _texto(prod, "nfe:vProd")
                ),
                "desconto": _decimal(
                    _texto(prod, "nfe:vDesc")
                ),
            }
        )

    pagamentos = []

    for det_pag in inf_nfe.findall(
        "nfe:pag/nfe:detPag",
        NS,
    ):
        codigo = _texto(
            det_pag,
            "nfe:tPag",
        )

        pagamentos.append(
            {
                "codigo": codigo,
                "descricao": FORMAS_PAGAMENTO.get(
                    codigo,
                    f"Forma {codigo or '-'}",
                ),
                "valor": _decimal(
                    _texto(det_pag, "nfe:vPag")
                ),
            }
        )

    qr_code = _texto(
        nfe,
        "nfe:infNFeSupl/nfe:qrCode",
    )

    url_consulta = _texto(
        nfe,
        "nfe:infNFeSupl/nfe:urlChave",
    )

    cpf_destinatario = _texto(
        dest,
        "nfe:CPF",
    )

    cnpj_destinatario = _texto(
        dest,
        "nfe:CNPJ",
    )

    documento_destinatario = ""

    if cpf_destinatario:
        documento_destinatario = _formatar_cpf(
            cpf_destinatario
        )
    elif cnpj_destinatario:
        documento_destinatario = _formatar_cnpj(
            cnpj_destinatario
        )

    dados = {
        "sucesso": True,
        "modelo": modelo,
        "serie": _texto(ide, "nfe:serie"),
        "numero": _texto(ide, "nfe:nNF"),
        "ambiente": _texto(ide, "nfe:tpAmb"),
        "data_emissao": _texto(ide, "nfe:dhEmi"),

        "emitente": {
            "cnpj": _formatar_cnpj(
                _texto(emit, "nfe:CNPJ")
            ),
            "razao_social": _texto(
                emit,
                "nfe:xNome",
            ),
            "fantasia": _texto(
                emit,
                "nfe:xFant",
            ),
            "ie": _texto(
                emit,
                "nfe:IE",
            ),
        },

        "destinatario": {
            "identificado": bool(
                cpf_destinatario
                or cnpj_destinatario
                or _texto(dest, "nfe:xNome")
            ),
            "nome": _texto(
                dest,
                "nfe:xNome",
            ),
            "documento": documento_destinatario,
        },

        "itens": itens,

        "totais": {
            "produtos": _decimal(
                _texto(total, "nfe:vProd")
            ),
            "desconto": _decimal(
                _texto(total, "nfe:vDesc")
            ),
            "frete": _decimal(
                _texto(total, "nfe:vFrete")
            ),
            "valor_nfce": _decimal(
                _texto(total, "nfe:vNF")
            ),
        },

        "pagamentos": pagamentos,

        "chave": chave,
        "chave_formatada": _formatar_chave(chave),

        "protocolo": _texto(
            protocolo,
            "nfe:nProt",
        ),
        "status_protocolo": _texto(
            protocolo,
            "nfe:cStat",
        ),
        "data_autorizacao": _texto(
            protocolo,
            "nfe:dhRecbto",
        ),

        "qr_code": qr_code,
        "url_consulta": url_consulta,

        "erros": [],
        "avisos": [],
    }

    if not itens:
        dados["avisos"].append(
            "NFC-e sem itens localizados."
        )

    if not qr_code:
        dados["avisos"].append(
            "QR Code nao localizado no XML."
        )

    if not dados["protocolo"]:
        dados["avisos"].append(
            "Protocolo de autorizacao nao localizado."
        )

    if dados["ambiente"] == "2":
        dados["avisos"].append(
            "NFC-e emitida em ambiente de homologacao - "
            "sem valor fiscal."
        )

    return dados


# ============================================================
# GERACAO DO DANFE NFC-e / CUPOM 80 MM
# ============================================================

def _moeda_nfce(valor):
    valor = _decimal(valor)

    texto = f"{valor:,.2f}"

    return (
        "R$ "
        + texto.replace(",", "#")
        .replace(".", ",")
        .replace("#", ".")
    )


def _numero_nfce(valor, casas=3):
    valor = _decimal(valor)

    texto = f"{valor:.{casas}f}"

    return texto.replace(".", ",")


def _formatar_data_hora_nfce(valor):
    from datetime import datetime

    valor = str(valor or "").strip()

    if not valor:
        return ""

    try:
        data = datetime.fromisoformat(valor)
        return data.strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError):
        return valor


def _quebrar_linha_nfce(
    canvas_pdf,
    texto,
    largura_maxima,
    fonte="Helvetica",
    tamanho=7,
):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    texto = str(texto or "").strip()

    if not texto:
        return [""]

    palavras = texto.split()
    linhas = []
    atual = ""

    for palavra in palavras:
        candidato = (
            palavra
            if not atual
            else f"{atual} {palavra}"
        )

        largura = stringWidth(
            candidato,
            fonte,
            tamanho,
        )

        if largura <= largura_maxima:
            atual = candidato
        else:
            if atual:
                linhas.append(atual)

            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas or [""]


def _texto_centralizado_nfce(
    canvas_pdf,
    y,
    texto,
    largura_pagina,
    tamanho=7,
    negrito=False,
):
    fonte = (
        "Helvetica-Bold"
        if negrito
        else "Helvetica"
    )

    canvas_pdf.setFont(fonte, tamanho)

    canvas_pdf.drawCentredString(
        largura_pagina / 2,
        y,
        str(texto or ""),
    )


def _linha_nfce(
    canvas_pdf,
    y,
    margem,
    largura_pagina,
):
    canvas_pdf.setLineWidth(0.4)

    canvas_pdf.line(
        margem,
        y,
        largura_pagina - margem,
        y,
    )


def _calcular_altura_nfce(dados):
    from reportlab.lib.units import mm

    itens = dados.get("itens", [])
    pagamentos = dados.get("pagamentos", [])

    # Base para cabecalho, totais, consulta,
    # QR Code, protocolo e margens.
    altura = 190 * mm

    # Reserva adicional por item.
    for item in itens:
        descricao = str(
            item.get("descricao") or ""
        )

        linhas_estimadas = max(
            1,
            (len(descricao) // 34) + 1,
        )

        altura += (
            13 + (linhas_estimadas * 8)
        )

    altura += max(
        1,
        len(pagamentos),
    ) * 10

    return max(
        altura,
        220 * mm,
    )


def gerar_danfe_nfce(
    caminho_xml,
    caminho_pdf,
):
    try:
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.graphics.barcode import qr
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF

        caminho_xml = Path(caminho_xml)
        caminho_pdf = Path(caminho_pdf)

        dados = extrair_dados_danfe_nfce(
            caminho_xml
        )

        if not dados.get("sucesso"):
            return {
                "sucesso": False,
                "caminho_pdf": None,
                "erros": dados.get(
                    "erros",
                    [],
                ),
                "avisos": dados.get(
                    "avisos",
                    [],
                ),
            }

        if dados.get("status_protocolo") not in (
            "100",
            "150",
        ):
            return {
                "sucesso": False,
                "caminho_pdf": None,
                "erros": [
                    "NFC-e sem protocolo de autorizacao "
                    "valido para gerar o DANFE."
                ],
                "avisos": dados.get(
                    "avisos",
                    [],
                ),
            }

        caminho_pdf.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        largura = 80 * mm
        altura = _calcular_altura_nfce(dados)
        margem = 4 * mm

        c = canvas.Canvas(
            str(caminho_pdf),
            pagesize=(largura, altura),
        )

        c.setTitle(
            "DANFE NFC-e "
            f"{dados.get('numero', '')}"
        )

        y = altura - (7 * mm)

        emitente = dados.get(
            "emitente",
            {},
        )

        nome_loja = (
            emitente.get("fantasia")
            or emitente.get("razao_social")
            or ""
        )

        _texto_centralizado_nfce(
            c,
            y,
            nome_loja,
            largura,
            tamanho=10,
            negrito=True,
        )
        y -= 11

        _texto_centralizado_nfce(
            c,
            y,
            emitente.get("razao_social", ""),
            largura,
            tamanho=6.5,
        )
        y -= 9

        _texto_centralizado_nfce(
            c,
            y,
            f"CNPJ: {emitente.get('cnpj', '')}",
            largura,
            tamanho=7,
        )
        y -= 9

        _texto_centralizado_nfce(
            c,
            y,
            f"IE: {emitente.get('ie', '')}",
            largura,
            tamanho=7,
        )
        y -= 11

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 12

        _texto_centralizado_nfce(
            c,
            y,
            "DANFE NFC-e",
            largura,
            tamanho=9,
            negrito=True,
        )
        y -= 10

        _texto_centralizado_nfce(
            c,
            y,
            "Documento Auxiliar da Nota Fiscal",
            largura,
            tamanho=6.5,
        )
        y -= 8

        _texto_centralizado_nfce(
            c,
            y,
            "de Consumidor Eletrônica",
            largura,
            tamanho=6.5,
        )
        y -= 12

        if str(dados.get("ambiente")) == "2":
            _texto_centralizado_nfce(
                c,
                y,
                "AMBIENTE DE HOMOLOGACAO",
                largura,
                tamanho=8,
                negrito=True,
            )
            y -= 9

            _texto_centralizado_nfce(
                c,
                y,
                "SEM VALOR FISCAL",
                largura,
                tamanho=8,
                negrito=True,
            )
            y -= 12

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 11

        c.setFont(
            "Helvetica-Bold",
            6.5,
        )

        c.drawString(
            margem,
            y,
            "CÓD  DESCRIÇÃO"
        )
        y -= 8

        c.setFont(
            "Helvetica",
            6,
        )

        c.drawString(
            margem,
            y,
            "QTD x UNIT.                 TOTAL"
        )
        y -= 10

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 10

        largura_texto = (
            largura - (2 * margem)
        )

        for item in dados.get(
            "itens",
            [],
        ):
            codigo = item.get(
                "codigo",
                "",
            )

            descricao = item.get(
                "descricao",
                "",
            )

            linhas_descricao = (
                _quebrar_linha_nfce(
                    c,
                    f"{codigo}  {descricao}",
                    largura_texto,
                    tamanho=6.5,
                )
            )

            c.setFont(
                "Helvetica",
                6.5,
            )

            for linha in linhas_descricao:
                c.drawString(
                    margem,
                    y,
                    linha,
                )
                y -= 8

            quantidade = _numero_nfce(
                item.get("quantidade"),
                3,
            )

            unitario = _moeda_nfce(
                item.get("valor_unitario")
            )

            total_item = _moeda_nfce(
                item.get("valor_produto")
            )

            c.drawString(
                margem,
                y,
                f"{quantidade} {item.get('unidade', '')}"
                f" x {unitario}"
            )

            c.drawRightString(
                largura - margem,
                y,
                total_item,
            )

            y -= 11

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 11

        totais = dados.get(
            "totais",
            {},
        )

        c.setFont(
            "Helvetica",
            7,
        )

        c.drawString(
            margem,
            y,
            "Subtotal"
        )

        c.drawRightString(
            largura - margem,
            y,
            _moeda_nfce(
                totais.get("produtos")
            ),
        )

        y -= 10

        desconto = _decimal(
            totais.get("desconto")
        )

        if desconto > 0:
            c.drawString(
                margem,
                y,
                "Desconto"
            )

            c.drawRightString(
                largura - margem,
                y,
                f"- {_moeda_nfce(desconto)}",
            )

            y -= 10

        frete = _decimal(
            totais.get("frete")
        )

        if frete > 0:
            c.drawString(
                margem,
                y,
                "Frete"
            )

            c.drawRightString(
                largura - margem,
                y,
                _moeda_nfce(frete),
            )

            y -= 10

        c.setFont(
            "Helvetica-Bold",
            10,
        )

        c.drawString(
            margem,
            y,
            "TOTAL"
        )

        c.drawRightString(
            largura - margem,
            y,
            _moeda_nfce(
                totais.get("valor_nfce")
            ),
        )

        y -= 14

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 11

        c.setFont(
            "Helvetica-Bold",
            7,
        )

        c.drawString(
            margem,
            y,
            "FORMA DE PAGAMENTO"
        )

        c.drawRightString(
            largura - margem,
            y,
            "VALOR"
        )

        y -= 10

        c.setFont(
            "Helvetica",
            7,
        )

        for pagamento in dados.get(
            "pagamentos",
            [],
        ):
            c.drawString(
                margem,
                y,
                pagamento.get(
                    "descricao",
                    "",
                ),
            )

            c.drawRightString(
                largura - margem,
                y,
                _moeda_nfce(
                    pagamento.get("valor")
                ),
            )

            y -= 10

        y -= 2

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 11

        destinatario = dados.get(
            "destinatario",
            {},
        )

        if destinatario.get(
            "identificado"
        ):
            c.setFont(
                "Helvetica-Bold",
                7,
            )

            c.drawString(
                margem,
                y,
                "CONSUMIDOR"
            )
            y -= 9

            c.setFont(
                "Helvetica",
                6.5,
            )

            if destinatario.get("nome"):
                c.drawString(
                    margem,
                    y,
                    destinatario.get("nome"),
                )
                y -= 8

            if destinatario.get("documento"):
                c.drawString(
                    margem,
                    y,
                    destinatario.get(
                        "documento"
                    ),
                )
                y -= 8
        else:
            _texto_centralizado_nfce(
                c,
                y,
                "CONSUMIDOR NÃO IDENTIFICADO",
                largura,
                tamanho=7,
            )
            y -= 11

        _linha_nfce(
            c,
            y,
            margem,
            largura,
        )
        y -= 11

        _texto_centralizado_nfce(
            c,
            y,
            (
                f"NFC-e n. {dados.get('numero', '')} "
                f"Serie {dados.get('serie', '')}"
            ),
            largura,
            tamanho=7,
            negrito=True,
        )
        y -= 11

        _texto_centralizado_nfce(
            c,
            y,
            "Consulte pela chave de acesso",
            largura,
            tamanho=6.5,
        )
        y -= 9

        chave_formatada = dados.get(
            "chave_formatada",
            "",
        )

        partes_chave = (
            chave_formatada.split()
        )

        metade = (
            len(partes_chave) // 2
        )

        if partes_chave:
            _texto_centralizado_nfce(
                c,
                y,
                " ".join(
                    partes_chave[:metade]
                ),
                largura,
                tamanho=6,
            )
            y -= 8

            _texto_centralizado_nfce(
                c,
                y,
                " ".join(
                    partes_chave[metade:]
                ),
                largura,
                tamanho=6,
            )
            y -= 11

        qr_conteudo = dados.get(
            "qr_code",
            "",
        )

        if qr_conteudo:
            tamanho_qr = 34 * mm

            widget = qr.QrCodeWidget(
                qr_conteudo
            )

            bounds = widget.getBounds()

            largura_qr = (
                bounds[2] - bounds[0]
            )

            altura_qr = (
                bounds[3] - bounds[1]
            )

            desenho = Drawing(
                tamanho_qr,
                tamanho_qr,
                transform=[
                    tamanho_qr / largura_qr,
                    0,
                    0,
                    tamanho_qr / altura_qr,
                    0,
                    0,
                ],
            )

            desenho.add(widget)

            x_qr = (
                largura - tamanho_qr
            ) / 2

            y_qr = y - tamanho_qr

            renderPDF.draw(
                desenho,
                c,
                x_qr,
                y_qr,
            )

            y = y_qr - 9

        _texto_centralizado_nfce(
            c,
            y,
            "Protocolo de autorização:",
            largura,
            tamanho=6,
        )
        y -= 8

        _texto_centralizado_nfce(
            c,
            y,
            dados.get(
                "protocolo",
                "",
            ),
            largura,
            tamanho=6.5,
            negrito=True,
        )
        y -= 9

        if dados.get(
            "data_autorizacao"
        ):
            _texto_centralizado_nfce(
                c,
                y,
                _formatar_data_hora_nfce(
                    dados.get(
                        "data_autorizacao"
                    )
                ),
                largura,
                tamanho=6,
            )
            y -= 10

        if str(
            dados.get("ambiente")
        ) == "2":
            _linha_nfce(
                c,
                y,
                margem,
                largura,
            )
            y -= 11

            _texto_centralizado_nfce(
                c,
                y,
                "EMITIDA EM HOMOLOGACAO",
                largura,
                tamanho=7,
                negrito=True,
            )
            y -= 9

            _texto_centralizado_nfce(
                c,
                y,
                "SEM VALOR FISCAL",
                largura,
                tamanho=7,
                negrito=True,
            )

        c.save()

        return {
            "sucesso": True,
            "caminho_pdf": str(
                caminho_pdf
            ),
            "chave": dados.get(
                "chave"
            ),
            "protocolo": dados.get(
                "protocolo"
            ),
            "modelo": dados.get(
                "modelo"
            ),
            "serie": dados.get(
                "serie"
            ),
            "numero": dados.get(
                "numero"
            ),
            "ambiente": dados.get(
                "ambiente"
            ),
            "erros": [],
            "avisos": dados.get(
                "avisos",
                [],
            ),
        }

    except Exception as erro:
        return {
            "sucesso": False,
            "caminho_pdf": None,
            "erros": [
                "Falha ao gerar DANFE NFC-e: "
                f"{type(erro).__name__}: {erro}"
            ],
            "avisos": [],
        }
