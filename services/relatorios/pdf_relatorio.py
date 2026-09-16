from io import BytesIO
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.utils import ImageReader

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from services.relatorios.relatorio_base import (
    obter_dados_cabecalho,
    formatar_data,
    formatar_data_hora,
)


# ============================================================
# IDENTIDADE VISUAL VERDE INFÂNCIA
# ============================================================

COR_VERDE = colors.HexColor(
    "#44D62C"
)

COR_ROSA = colors.HexColor(
    "#D5066F"
)

COR_AZUL = colors.HexColor(
    "#008ACD"
)

COR_TEXTO = colors.HexColor(
    "#333333"
)

COR_CINZA = colors.HexColor(
    "#666666"
)

COR_LINHA = colors.HexColor(
    "#D9D9D9"
)

COR_FUNDO = colors.HexColor(
    "#F6F6F6"
)


# ============================================================
# LOGO
# ============================================================

def _obter_logo_image_reader(
    dados_empresa,
):

    logo_bytes = dados_empresa.get(
        "logo"
    )

    # --------------------------------------------------------
    # PRIMEIRA OPÇÃO:
    # LOGO CADASTRADA NO BANCO
    # --------------------------------------------------------

    if logo_bytes:

        try:

            if isinstance(
                logo_bytes,
                memoryview,
            ):

                logo_bytes = (
                    logo_bytes.tobytes()
                )

            return ImageReader(
                BytesIO(
                    bytes(
                        logo_bytes
                    )
                )
            )

        except Exception as erro:

            print(
                "Não foi possível carregar "
                "a logo do banco:",
                erro,
            )

    # --------------------------------------------------------
    # SEGUNDA OPÇÃO:
    # ARQUIVO LOCAL
    # --------------------------------------------------------

    caminhos = [
        os.path.join(
            os.getcwd(),
            "assets",
            "logo_verde_infancia.png",
        ),

        os.path.join(
            os.getcwd(),
            "assets",
            "Logo.png",
        ),

        os.path.join(
            os.getcwd(),
            "assets",
            "logo1.png",
        ),
    ]

    for caminho in caminhos:

        if os.path.exists(
            caminho
        ):

            try:

                return ImageReader(
                    caminho
                )

            except Exception:
                pass

    return None


# ============================================================
# CABEÇALHO / RODAPÉ
# ============================================================

def _desenhar_cabecalho_rodape(
    canvas,
    doc,
    dados_empresa,
    titulo,
    periodo_texto,
):

    canvas.saveState()

    largura_pagina, altura_pagina = (
        doc.pagesize
    )

    # ========================================================
    # CABEÇALHO
    # ========================================================

    topo = (
        altura_pagina
        - 28
    )

    logo = (
        _obter_logo_image_reader(
            dados_empresa
        )
    )

    if logo:

        try:

            canvas.drawImage(
                logo,
                28,
                topo - 66,
                width=98,
                height=60,
                preserveAspectRatio=True,
                mask="auto",
            )

        except Exception as erro:

            print(
                "Erro ao desenhar logo:",
                erro,
            )

    x_dados = 138

    # --------------------------------------------------------
    # NOME FANTASIA
    # --------------------------------------------------------

    canvas.setFillColor(
        COR_VERDE
    )

    canvas.setFont(
        "Helvetica-Bold",
        17,
    )

    canvas.drawString(
        x_dados,
        topo - 8,
        str(
            dados_empresa.get(
                "nome_fantasia",
                "",
            )
        ),
    )

    # --------------------------------------------------------
    # RAZÃO SOCIAL
    # --------------------------------------------------------

    canvas.setFillColor(
        COR_TEXTO
    )

    canvas.setFont(
        "Helvetica-Bold",
        10,
    )

    canvas.drawString(
        x_dados,
        topo - 25,
        str(
            dados_empresa.get(
                "razao_social",
                "",
            )
        ),
    )

    # --------------------------------------------------------
    # CNPJ / IE
    # --------------------------------------------------------

    canvas.setFont(
        "Helvetica",
        9,
    )

    cnpj = dados_empresa.get(
        "cnpj_formatado",
        "",
    )

    ie = dados_empresa.get(
        "inscricao_estadual",
        "",
    )

    linha_documentos = ""

    if cnpj:

        linha_documentos += (
            f"CNPJ: {cnpj}"
        )

    if ie:

        if linha_documentos:

            linha_documentos += (
                "    |    "
            )

        linha_documentos += (
            f"IE: {ie}"
        )

    if linha_documentos:

        canvas.drawString(
            x_dados,
            topo - 40,
            linha_documentos,
        )

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    endereco = dados_empresa.get(
        "endereco",
        "",
    )

    if endereco:

        canvas.drawString(
            x_dados,
            topo - 54,
            endereco[:110],
        )

    # --------------------------------------------------------
    # TELEFONE / E-MAIL
    # --------------------------------------------------------

    contato = []

    telefone = dados_empresa.get(
        "telefone",
        "",
    )

    email = dados_empresa.get(
        "email",
        "",
    )

    if telefone:

        contato.append(
            f"Telefone: {telefone}"
        )

    if email:

        contato.append(
            f"E-mail: {email}"
        )

    if contato:

        canvas.drawString(
            x_dados,
            topo - 68,
            "    |    ".join(
                contato
            ),
        )

    # --------------------------------------------------------
    # LINHA DA IDENTIDADE VISUAL
    # --------------------------------------------------------

    canvas.setStrokeColor(
        COR_VERDE
    )

    canvas.setLineWidth(
        2
    )

    canvas.line(
        28,
        topo - 80,
        largura_pagina - 28,
        topo - 80,
    )

    # ========================================================
    # IDENTIFICAÇÃO DO RELATÓRIO
    # ========================================================

    canvas.setFillColor(
        COR_TEXTO
    )

    canvas.setFont(
        "Helvetica-Bold",
        14,
    )

    canvas.drawCentredString(
        largura_pagina / 2,
        topo - 101,
        titulo.upper(),
    )

    if periodo_texto:

        canvas.setFont(
            "Helvetica",
            9,
        )

        canvas.setFillColor(
            COR_CINZA
        )

        canvas.drawCentredString(
            largura_pagina / 2,
            topo - 116,
            periodo_texto,
        )

    # ========================================================
    # RODAPÉ
    # ========================================================

    canvas.setStrokeColor(
        COR_LINHA
    )

    canvas.setLineWidth(
        0.5
    )

    canvas.line(
        28,
        36,
        largura_pagina - 28,
        36,
    )

    canvas.setFillColor(
        COR_CINZA
    )

    canvas.setFont(
        "Helvetica",
        8,
    )

    canvas.drawString(
        28,
        22,
        "ERP Verde Infância",
    )

    gerado_em = (
        dados_empresa.get(
            "gerado_em"
        )
    )

    canvas.drawCentredString(
        largura_pagina / 2,
        22,
        (
            "Emitido em "
            f"{formatar_data_hora(gerado_em)}"
        ),
    )

    canvas.drawRightString(
        largura_pagina - 28,
        22,
        f"Página {doc.page}",
    )

    canvas.restoreState()


# ============================================================
# ESTILOS
# ============================================================

def _criar_estilos():

    estilos = (
        getSampleStyleSheet()
    )

    # --------------------------------------------------------
    # TÍTULO DE SEÇÃO
    #
    # Mantemos a mesma fonte/tamanho.
    # Apenas reduzimos um pouco o espaço vertical.
    # --------------------------------------------------------

    estilos.add(
        ParagraphStyle(
            name="RelatorioSecao",
            parent=estilos[
                "Heading2"
            ],
            fontName=(
                "Helvetica-Bold"
            ),
            fontSize=13,
            leading=16,
            textColor=COR_AZUL,

            # Antes: 10
            spaceBefore=7,

            # Antes: 9
            spaceAfter=6,
        )
    )

    # --------------------------------------------------------
    # TEXTO NORMAL
    # --------------------------------------------------------

    estilos.add(
        ParagraphStyle(
            name="RelatorioTexto",
            parent=estilos[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=COR_TEXTO,
        )
    )

    # --------------------------------------------------------
    # OBSERVAÇÃO
    # --------------------------------------------------------

    estilos.add(
        ParagraphStyle(
            name="RelatorioObservacao",
            parent=estilos[
                "Normal"
            ],
            fontName=(
                "Helvetica-Oblique"
            ),
            fontSize=8,
            leading=11,
            textColor=COR_CINZA,
        )
    )

    return estilos


# ============================================================
# BLOCO DE INDICADORES
# ============================================================

def criar_bloco_indicadores(
    indicadores,
):

    if not indicadores:

        return []

    dados = []

    cabecalho = []
    valores = []

    for indicador in indicadores:

        cabecalho.append(
            str(
                indicador.get(
                    "titulo",
                    "",
                )
            )
        )

        valores.append(
            str(
                indicador.get(
                    "valor",
                    "",
                )
            )
        )

    dados.append(
        cabecalho
    )

    dados.append(
        valores
    )

    largura_total = (
        landscape(A4)[0]
        - 56
    )

    largura_coluna = (
        largura_total
        / len(
            indicadores
        )
    )

    tabela = Table(
        dados,
        colWidths=[
            largura_coluna
            for _ in indicadores
        ],
    )

    tabela.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    COR_AZUL,
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),

                (
                    "BACKGROUND",
                    (0, 1),
                    (-1, 1),
                    COR_FUNDO,
                ),

                (
                    "TEXTCOLOR",
                    (0, 1),
                    (-1, 1),
                    COR_TEXTO,
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),

                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold",
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    9,
                ),

                (
                    "FONTSIZE",
                    (0, 1),
                    (-1, 1),
                    14,
                ),

                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    COR_LINHA,
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    COR_LINHA,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    return [
        tabela,

        # Antes: 14
        Spacer(
            1,
            9,
        ),
    ]


# ============================================================
# TABELA PADRÃO
# ============================================================

def criar_tabela_relatorio(
    colunas,
    linhas,
    larguras=None,
    alinhamentos=None,
    quebrar_texto=False,
):

    if quebrar_texto:

        estilo_cabecalho = ParagraphStyle(
            "TabelaCabecalho",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=colors.white,
        )

        estilo_celula = ParagraphStyle(
            "TabelaCelula",
            fontName="Helvetica",
            fontSize=8.5,
            leading=10,
            textColor=colors.black,
        )

        dados = [
            [
                Paragraph(
                    escape(str(coluna)),
                    estilo_cabecalho,
                )
                for coluna in colunas
            ]
        ]

        for linha in linhas:

            dados.append(
                [
                    Paragraph(
                        escape(
                            ""
                            if valor is None
                            else str(valor)
                        ),
                        estilo_celula,
                    )
                    for valor in linha
                ]
            )

    else:

        dados = [
            [
                str(
                    coluna
                )
                for coluna
                in colunas
            ]
        ]

        for linha in linhas:

            dados.append(
                [
                    (
                        ""
                        if valor is None
                        else str(valor)
                    )
                    for valor in linha
                ]
            )

    tabela = Table(
        dados,
        colWidths=larguras,
        repeatRows=1,
        hAlign="LEFT",
    )

    estilos = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            COR_AZUL,
        ),

        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white,
        ),

        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold",
        ),

        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            8.5,
        ),

        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.35,
            COR_LINHA,
        ),

        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE",
        ),

        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),

        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
    ]

    # ========================================================
    # LINHAS ALTERNADAS
    # ========================================================

    for indice in range(
        1,
        len(
            dados
        ),
    ):

        if indice % 2 == 0:

            estilos.append(
                (
                    "BACKGROUND",
                    (0, indice),
                    (-1, indice),
                    COR_FUNDO,
                )
            )

    # ========================================================
    # ALINHAMENTOS
    # ========================================================

    if alinhamentos:

        for (
            indice,
            alinhamento,
        ) in enumerate(
            alinhamentos
        ):

            estilos.append(
                (
                    "ALIGN",
                    (indice, 1),
                    (indice, -1),
                    alinhamento,
                )
            )

    tabela.setStyle(
        TableStyle(
            estilos
        )
    )

    return tabela


# ============================================================
# GERADOR PRINCIPAL
# ============================================================

def gerar_pdf_profissional(
    titulo,
    periodo_inicio=None,
    periodo_fim=None,
    indicadores=None,
    secoes=None,
    orientacao="paisagem",
):

    dados_empresa = (
        obter_dados_cabecalho()
    )

    buffer = BytesIO()

    # ========================================================
    # ORIENTAÇÃO
    # ========================================================

    if orientacao == "retrato":

        tamanho_pagina = A4

    else:

        tamanho_pagina = (
            landscape(A4)
        )

    # ========================================================
    # PERÍODO
    # ========================================================

    periodo_texto = ""

    if (
        periodo_inicio
        is not None
        and
        periodo_fim
        is not None
    ):

        periodo_texto = (
            "Período: "
            f"{formatar_data(periodo_inicio)} "
            "a "
            f"{formatar_data(periodo_fim)}"
        )

    # ========================================================
    # DOCUMENTO
    # ========================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=tamanho_pagina,
        rightMargin=28,
        leftMargin=28,

        # Mantido:
        # espaço reservado ao cabeçalho.
        topMargin=158,

        # Mantido:
        # espaço reservado ao rodapé.
        bottomMargin=50,
    )

    estilos = (
        _criar_estilos()
    )

    elementos = []

    # ========================================================
    # INDICADORES PRINCIPAIS
    # ========================================================

    elementos.extend(
        criar_bloco_indicadores(
            indicadores
        )
    )

    # ========================================================
    # SEÇÕES
    # ========================================================

    for secao in (
        secoes
        or []
    ):

        titulo_secao = (
            secao.get(
                "titulo"
            )
        )

        texto = (
            secao.get(
                "texto"
            )
        )

        tabela = (
            secao.get(
                "tabela"
            )
        )

        observacao = (
            secao.get(
                "observacao"
            )
        )

        # ====================================================
        # TÍTULO
        # ====================================================

        if titulo_secao:

            elementos.append(
                Paragraph(
                    str(
                        titulo_secao
                    ),
                    estilos[
                        "RelatorioSecao"
                    ],
                )
            )

        # ====================================================
        # CASO ESPECIAL:
        #
        # TEXTO + OBSERVAÇÃO SEM TABELA
        #
        # Isso evita que uma observação curta seja empurrada
        # sozinha para uma nova página.
        # ====================================================

        if (
            texto
            and observacao
            and tabela is None
        ):

            texto_principal = (
                escape(
                    str(
                        texto
                    )
                )
            )

            texto_observacao = (
                escape(
                    str(
                        observacao
                    )
                )
            )

            conteudo = (
                f"{texto_principal}"
                "<br/>"
                "<font size='8' "
                "color='#666666'>"
                "<i>"
                f"{texto_observacao}"
                "</i>"
                "</font>"
            )

            elementos.append(
                Paragraph(
                    conteudo,
                    estilos[
                        "RelatorioTexto"
                    ],
                )
            )

            elementos.append(
                Spacer(
                    1,
                    4,
                )
            )

            # Marcamos para não inserir
            # novamente a observação.
            texto = None
            observacao = None

        # ====================================================
        # TEXTO NORMAL
        # ====================================================

        if texto:

            elementos.append(
                Paragraph(
                    str(
                        texto
                    ),
                    estilos[
                        "RelatorioTexto"
                    ],
                )
            )

            # Antes: 8
            elementos.append(
                Spacer(
                    1,
                    5,
                )
            )

        # ====================================================
        # TABELA
        # ====================================================

        if tabela is not None:

            elementos.append(
                tabela
            )

            # Antes: 12
            elementos.append(
                Spacer(
                    1,
                    8,
                )
            )

        # ====================================================
        # OBSERVAÇÃO NORMAL
        # ====================================================

        if observacao:

            elementos.append(
                Paragraph(
                    str(
                        observacao
                    ),
                    estilos[
                        "RelatorioObservacao"
                    ],
                )
            )

            # Antes: 10
            elementos.append(
                Spacer(
                    1,
                    5,
                )
            )

        # ====================================================
        # QUEBRA DE PÁGINA INTENCIONAL
        # ====================================================

        nova_pagina = (
            secao.get(
                "nova_pagina",
                False,
            )
        )

        if nova_pagina:

            elementos.append(
                PageBreak()
            )

    # ========================================================
    # CABEÇALHO / RODAPÉ
    # ========================================================

    def desenhar_pagina(
        canvas,
        documento,
    ):

        _desenhar_cabecalho_rodape(
            canvas,
            documento,
            dados_empresa,
            titulo,
            periodo_texto,
        )

    # ========================================================
    # CONSTRUIR PDF
    # ========================================================

    doc.build(
        elementos,
        onFirstPage=(
            desenhar_pagina
        ),
        onLaterPages=(
            desenhar_pagina
        ),
    )

    buffer.seek(
        0
    )

    return buffer