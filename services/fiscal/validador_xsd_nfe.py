from pathlib import Path


# ============================================================
# VALIDADOR XSD NF-e
#
# RESPONSABILIDADE:
# - Receber XML da NF-e
# - Receber caminho do schema principal
# - Validar o XML contra os schemas XSD
# - Retornar erros estruturados
#
# IMPORTANTE:
# - NÃO assina XML
# - NÃO transmite para SEFAZ
# - NÃO altera banco
# - NÃO altera venda
# - NÃO consome numeração fiscal
#
# Os schemas devem permanecer juntos na estrutura original
# do pacote oficial, pois existem includes/imports entre XSDs.
# ============================================================


# ============================================================
# IMPORTAR LXML
# ============================================================
try:

    from lxml import etree

    LXML_DISPONIVEL = True

except ImportError:

    etree = None

    LXML_DISPONIVEL = False


# ============================================================
# NORMALIZAR CAMINHO
# ============================================================
def _normalizar_caminho(
    caminho
):

    if caminho is None:
        return None

    try:

        return Path(
            caminho
        ).expanduser().resolve()

    except Exception:

        return None


# ============================================================
# FORMATAR ERRO DO LXML
# ============================================================
def _formatar_erro(
    erro
):

    return {
        "linha":
            getattr(
                erro,
                "line",
                None
            ),

        "coluna":
            getattr(
                erro,
                "column",
                None
            ),

        "nivel":
            getattr(
                erro,
                "level_name",
                None
            ),

        "dominio":
            getattr(
                erro,
                "domain_name",
                None
            ),

        "tipo":
            getattr(
                erro,
                "type_name",
                None
            ),

        "mensagem":
            str(
                getattr(
                    erro,
                    "message",
                    erro
                )
            ).strip()
    }


# ============================================================
# VALIDAR DEPENDÊNCIA
# ============================================================
def verificar_dependencia_lxml():

    if LXML_DISPONIVEL:

        return {
            "sucesso": True,
            "disponivel": True,
            "mensagem":
                "Biblioteca lxml disponível."
        }

    return {
        "sucesso": False,
        "disponivel": False,
        "mensagem": (
            "Biblioteca lxml não instalada. "
            "Instale o pacote lxml antes de validar XSD."
        )
    }


# ============================================================
# CARREGAR SCHEMA
# ============================================================
def carregar_schema_nfe(
    caminho_xsd
):

    if not LXML_DISPONIVEL:

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd": None,
            "erros": [
                (
                    "A biblioteca lxml não está disponível."
                )
            ]
        }

    caminho = _normalizar_caminho(
        caminho_xsd
    )

    if caminho is None:

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd": None,
            "erros": [
                "Caminho do XSD inválido."
            ]
        }

    if not caminho.exists():

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros": [
                (
                    "Arquivo XSD não encontrado: "
                    f"{caminho}"
                )
            ]
        }

    if not caminho.is_file():

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros": [
                (
                    "O caminho informado para o XSD "
                    "não é um arquivo."
                )
            ]
        }

    if caminho.suffix.lower() != ".xsd":

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros": [
                (
                    "O arquivo informado não possui "
                    "extensão .xsd."
                )
            ]
        }

    try:

        parser = etree.XMLParser(
            remove_blank_text=False,
            resolve_entities=False,
            no_network=True
        )

        documento_xsd = etree.parse(
            str(
                caminho
            ),
            parser
        )

        schema = etree.XMLSchema(
            documento_xsd
        )

        return {
            "sucesso": True,
            "schema":
                schema,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros": []
        }

    except etree.XMLSchemaParseError as erro:

        erros = []

        for item in erro.error_log:

            erros.append(
                _formatar_erro(
                    item
                )
            )

        if not erros:

            erros.append(
                {
                    "linha": None,
                    "coluna": None,
                    "nivel": "ERROR",
                    "dominio": "XMLSCHEMA",
                    "tipo": None,
                    "mensagem":
                        str(
                            erro
                        )
                }
            )

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros":
                erros
        }

    except etree.XMLSyntaxError as erro:

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros": [
                {
                    "linha":
                        getattr(
                            erro,
                            "lineno",
                            None
                        ),

                    "coluna":
                        None,

                    "nivel":
                        "ERROR",

                    "dominio":
                        "XML",

                    "tipo":
                        "XMLSyntaxError",

                    "mensagem":
                        str(
                            erro
                        )
                }
            ]
        }

    except Exception as erro:

        return {
            "sucesso": False,
            "schema": None,
            "caminho_xsd":
                str(
                    caminho
                ),
            "erros": [
                {
                    "linha": None,
                    "coluna": None,
                    "nivel": "ERROR",
                    "dominio": "INTERNO",
                    "tipo":
                        type(
                            erro
                        ).__name__,
                    "mensagem":
                        str(
                            erro
                        )
                }
            ]
        }


# ============================================================
# CONVERTER XML PARA DOCUMENTO LXML
# ============================================================
def _carregar_xml(
    xml
):

    if not LXML_DISPONIVEL:

        return {
            "sucesso": False,
            "documento": None,
            "erros": [
                (
                    "A biblioteca lxml não está disponível."
                )
            ]
        }

    if xml is None:

        return {
            "sucesso": False,
            "documento": None,
            "erros": [
                "XML não informado."
            ]
        }

    # --------------------------------------------------------
    # XML EM BYTES
    # --------------------------------------------------------
    if isinstance(
        xml,
        bytes
    ):

        xml_bytes = xml

    # --------------------------------------------------------
    # XML EM STRING
    # --------------------------------------------------------
    elif isinstance(
        xml,
        str
    ):

        texto = xml.strip()

        if not texto:

            return {
                "sucesso": False,
                "documento": None,
                "erros": [
                    "XML vazio."
                ]
            }

        # ----------------------------------------------------
        # SE FOR CAMINHO DE ARQUIVO
        # ----------------------------------------------------
        if not texto.startswith(
            "<"
        ):

            caminho = _normalizar_caminho(
                texto
            )

            if (
                caminho is not None
                and
                caminho.exists()
                and
                caminho.is_file()
            ):

                try:

                    xml_bytes = caminho.read_bytes()

                except Exception as erro:

                    return {
                        "sucesso": False,
                        "documento": None,
                        "erros": [
                            (
                                "Não foi possível ler "
                                f"o XML: {erro}"
                            )
                        ]
                    }

            else:

                return {
                    "sucesso": False,
                    "documento": None,
                    "erros": [
                        (
                            "O conteúdo informado não parece "
                            "ser XML e o arquivo não foi encontrado."
                        )
                    ]
                }

        else:

            xml_bytes = texto.encode(
                "utf-8"
            )

    # --------------------------------------------------------
    # PATH
    # --------------------------------------------------------
    elif isinstance(
        xml,
        Path
    ):

        caminho = _normalizar_caminho(
            xml
        )

        if (
            caminho is None
            or
            not caminho.exists()
            or
            not caminho.is_file()
        ):

            return {
                "sucesso": False,
                "documento": None,
                "erros": [
                    "Arquivo XML não encontrado."
                ]
            }

        try:

            xml_bytes = caminho.read_bytes()

        except Exception as erro:

            return {
                "sucesso": False,
                "documento": None,
                "erros": [
                    (
                        "Não foi possível ler "
                        f"o XML: {erro}"
                    )
                ]
            }

    else:

        return {
            "sucesso": False,
            "documento": None,
            "erros": [
                (
                    "Tipo de entrada XML não suportado."
                )
            ]
        }

    try:

        parser = etree.XMLParser(
            remove_blank_text=False,
            resolve_entities=False,
            no_network=True
        )

        documento = etree.fromstring(
            xml_bytes,
            parser
        )

        return {
            "sucesso": True,
            "documento":
                documento,
            "erros": []
        }

    except etree.XMLSyntaxError as erro:

        erros = []

        for item in erro.error_log:

            erros.append(
                _formatar_erro(
                    item
                )
            )

        if not erros:

            erros.append(
                {
                    "linha":
                        getattr(
                            erro,
                            "lineno",
                            None
                        ),

                    "coluna":
                        None,

                    "nivel":
                        "ERROR",

                    "dominio":
                        "XML",

                    "tipo":
                        "XMLSyntaxError",

                    "mensagem":
                        str(
                            erro
                        )
                }
            )

        return {
            "sucesso": False,
            "documento": None,
            "erros":
                erros
        }


# ============================================================
# VALIDAR XML CONTRA XSD
# ============================================================
def validar_xml_nfe_xsd(
    xml,
    caminho_xsd
):

    # --------------------------------------------------------
    # DEPENDÊNCIA
    # --------------------------------------------------------
    dependencia = verificar_dependencia_lxml()

    if not dependencia.get(
        "disponivel"
    ):

        return {
            "sucesso": False,
            "valido": False,
            "xml_bem_formado": False,
            "schema_carregado": False,
            "quantidade_erros": 1,
            "erros": [
                dependencia.get(
                    "mensagem"
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # XML
    # --------------------------------------------------------
    resultado_xml = _carregar_xml(
        xml
    )

    if not resultado_xml.get(
        "sucesso"
    ):

        erros = resultado_xml.get(
            "erros",
            []
        )

        return {
            "sucesso": False,
            "valido": False,
            "xml_bem_formado": False,
            "schema_carregado": False,
            "quantidade_erros":
                len(
                    erros
                ),
            "erros":
                erros,
            "avisos": []
        }

    # --------------------------------------------------------
    # XSD
    # --------------------------------------------------------
    resultado_schema = carregar_schema_nfe(
        caminho_xsd
    )

    if not resultado_schema.get(
        "sucesso"
    ):

        erros = resultado_schema.get(
            "erros",
            []
        )

        return {
            "sucesso": False,
            "valido": False,
            "xml_bem_formado": True,
            "schema_carregado": False,
            "caminho_xsd":
                resultado_schema.get(
                    "caminho_xsd"
                ),
            "quantidade_erros":
                len(
                    erros
                ),
            "erros":
                erros,
            "avisos": []
        }

    documento = resultado_xml.get(
        "documento"
    )

    schema = resultado_schema.get(
        "schema"
    )

    # --------------------------------------------------------
    # VALIDAR
    # --------------------------------------------------------
    try:

        valido = schema.validate(
            documento
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "valido": False,
            "xml_bem_formado": True,
            "schema_carregado": True,
            "caminho_xsd":
                resultado_schema.get(
                    "caminho_xsd"
                ),
            "quantidade_erros": 1,
            "erros": [
                {
                    "linha": None,
                    "coluna": None,
                    "nivel": "ERROR",
                    "dominio": "INTERNO",
                    "tipo":
                        type(
                            erro
                        ).__name__,
                    "mensagem":
                        str(
                            erro
                        )
                }
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # APROVADO
    # --------------------------------------------------------
    if valido:

        return {
            "sucesso": True,
            "valido": True,
            "xml_bem_formado": True,
            "schema_carregado": True,
            "caminho_xsd":
                resultado_schema.get(
                    "caminho_xsd"
                ),
            "quantidade_erros": 0,
            "erros": [],
            "avisos": []
        }

    # --------------------------------------------------------
    # REJEITADO PELO XSD
    # --------------------------------------------------------
    erros = []

    for erro in schema.error_log:

        erros.append(
            _formatar_erro(
                erro
            )
        )

    return {
        "sucesso": True,
        "valido": False,
        "xml_bem_formado": True,
        "schema_carregado": True,
        "caminho_xsd":
            resultado_schema.get(
                "caminho_xsd"
            ),
        "quantidade_erros":
            len(
                erros
            ),
        "erros":
            erros,
        "avisos": [
            (
                "O XML é bem formado, mas ainda "
                "não atende integralmente ao XSD."
            )
        ]
    }


# ============================================================
# VALIDAR ARQUIVO XML CONTRA XSD
# ============================================================
def validar_arquivo_nfe_xsd(
    caminho_xml,
    caminho_xsd
):

    return validar_xml_nfe_xsd(
        xml=caminho_xml,
        caminho_xsd=caminho_xsd
    )