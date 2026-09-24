from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
import unicodedata


TAMANHO_REGISTRO = 126


def _somente_digitos(valor):
    if valor is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor),
    )


def _texto_sintegra(valor):
    if valor is None:
        return ""

    texto = str(valor).strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    return texto.upper()


def _campo_alfanumerico(
    valor,
    tamanho,
):
    texto = _texto_sintegra(
        valor
    )

    return texto[:tamanho].ljust(
        tamanho
    )


def _campo_numerico(
    valor,
    tamanho,
):
    numeros = _somente_digitos(
        valor
    )

    if len(numeros) > tamanho:
        numeros = numeros[-tamanho:]

    return numeros.zfill(
        tamanho
    )


def _data_aaaammdd(valor):
    if isinstance(
        valor,
        datetime,
    ):
        valor = valor.date()

    if not isinstance(
        valor,
        date,
    ):
        raise ValueError(
            "Data invalida para SINTEGRA."
        )

    return valor.strftime(
        "%Y%m%d"
    )


def _validar_tamanho_registro(
    registro,
    tipo,
):
    if len(registro) != TAMANHO_REGISTRO:
        raise ValueError(
            f"Registro {tipo} possui "
            f"{len(registro)} caracteres; "
            f"esperado: {TAMANHO_REGISTRO}."
        )

    return registro


def gerar_registro_10(
    *,
    cnpj,
    inscricao_estadual,
    razao_social,
    municipio,
    uf,
    data_inicial,
    data_final,
    fax=None,
    codigo_estrutura="3",
    natureza_operacoes="3",
    finalidade="1",
):
    registro = "".join(
        [
            "10",
            _campo_numerico(
                cnpj,
                14,
            ),
            _campo_alfanumerico(
                inscricao_estadual,
                14,
            ),
            _campo_alfanumerico(
                razao_social,
                35,
            ),
            _campo_alfanumerico(
                municipio,
                30,
            ),
            _campo_alfanumerico(
                uf,
                2,
            ),
            _campo_numerico(
                fax,
                10,
            ),
            _data_aaaammdd(
                data_inicial
            ),
            _data_aaaammdd(
                data_final
            ),
            _campo_alfanumerico(
                codigo_estrutura,
                1,
            ),
            _campo_alfanumerico(
                natureza_operacoes,
                1,
            ),
            _campo_alfanumerico(
                finalidade,
                1,
            ),
        ]
    )

    return _validar_tamanho_registro(
        registro,
        "10",
    )


def gerar_registro_11(
    *,
    logradouro,
    numero,
    complemento,
    bairro,
    cep,
    contato,
    telefone,
):
    registro = "".join(
        [
            "11",
            _campo_alfanumerico(
                logradouro,
                34,
            ),
            _campo_numerico(
                numero,
                5,
            ),
            _campo_alfanumerico(
                complemento,
                22,
            ),
            _campo_alfanumerico(
                bairro,
                15,
            ),
            _campo_numerico(
                cep,
                8,
            ),
            _campo_alfanumerico(
                contato,
                28,
            ),
            _campo_numerico(
                telefone,
                12,
            ),
        ]
    )

    return _validar_tamanho_registro(
        registro,
        "11",
    )
def _decimal_sintegra(
    valor,
    casas_decimais,
):
    if valor in (
        None,
        "",
    ):
        numero = Decimal("0")
    else:
        try:
            numero = Decimal(
                str(valor)
            )
        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ) as erro:
            raise ValueError(
                f"Valor numerico invalido: {valor}"
            ) from erro

    if numero < 0:
        raise ValueError(
            "Valor negativo nao permitido "
            "neste campo SINTEGRA."
        )

    quantizador = Decimal(
        "1." + (
            "0" * casas_decimais
        )
    )

    return numero.quantize(
        quantizador,
        rounding=ROUND_HALF_UP,
    )


def _campo_decimal(
    valor,
    tamanho,
    casas_decimais,
):
    numero = _decimal_sintegra(
        valor,
        casas_decimais,
    )

    fator = Decimal(
        10 ** casas_decimais
    )

    inteiro = int(
        numero * fator
    )

    texto = str(
        inteiro
    )

    if len(texto) > tamanho:
        raise ValueError(
            "Valor numerico excede "
            f"{tamanho} posicoes."
        )

    return texto.zfill(
        tamanho
    )


def determinar_cst_registro_54(
    item,
):
    csosn = _somente_digitos(
        item.get(
            "csosn"
        )
    )

    if csosn:

        if len(csosn) != 3:
            raise ValueError(
                "CSOSN do Registro 54 deve "
                "possuir 3 digitos."
            )

        return csosn

    origem = _somente_digitos(
        item.get(
            "origem"
        )
    )

    cst = _somente_digitos(
        item.get(
            "cst"
        )
        or item.get(
            "cst_icms"
        )
    )

    if len(origem) != 1:
        raise ValueError(
            "Origem da mercadoria ausente "
            "ou invalida para o Registro 54."
        )

    if len(cst) != 2:
        raise ValueError(
            "CST do ICMS ausente ou invalido "
            "para o Registro 54."
        )

    resultado = (
        origem
        + cst
    )

    if len(resultado) != 3:
        raise ValueError(
            "Situacao tributaria invalida "
            "para o Registro 54."
        )

    return resultado


def normalizar_numero_documento_sintegra(
    numero,
):
    numero_digitos = _somente_digitos(
        numero
    )

    if not numero_digitos:
        raise ValueError(
            "Numero do documento fiscal "
            "nao informado."
        )

    # O leiaute SINTEGRA reserva 6 posicoes
    # para o numero do documento fiscal.
    #
    # Para documentos com mais de 6 digitos,
    # o Manual SINTEGRA determina a utilizacao
    # dos 6 ultimos digitos.
    if len(numero_digitos) > 6:
        numero_digitos = (
            numero_digitos[-6:]
        )

    return numero_digitos


def gerar_registro_54(
    *,
    cnpj,
    modelo,
    serie,
    numero,
    cfop,
    cst,
    numero_item,
    codigo_produto,
    quantidade,
    valor_produto,
    valor_desconto=0,
    base_icms=0,
    base_icms_st=0,
    valor_ipi=0,
    aliquota_icms=0,
    permitir_codigo_vazio=False,
):
    cnpj_digitos = _somente_digitos(
        cnpj
    )

    if len(cnpj_digitos) != 14:
        raise ValueError(
            "CNPJ do Registro 54 deve "
            "possuir 14 digitos."
        )

    modelo_digitos = _somente_digitos(
        modelo
    )

    if not modelo_digitos:
        raise ValueError(
            "Modelo do Registro 54 "
            "nao informado."
        )

    if len(modelo_digitos) > 2:
        raise ValueError(
            "Modelo do Registro 54 excede "
            "2 posicoes."
        )

    serie_texto = _texto_sintegra(
        serie
    )

    if len(serie_texto) > 3:
        raise ValueError(
            "Serie do Registro 54 excede "
            "3 posicoes."
        )

    numero_digitos = (
        normalizar_numero_documento_sintegra(
            numero
        )
    )

    cfop_digitos = _somente_digitos(
        cfop
    )

    if len(cfop_digitos) != 4:
        raise ValueError(
            "CFOP do Registro 54 deve "
            "possuir 4 digitos."
        )

    cst_texto = _texto_sintegra(
        cst
    )

    if not cst_texto:
        raise ValueError(
            "CST/CSOSN do Registro 54 "
            "nao informado."
        )

    if len(cst_texto) > 3:
        raise ValueError(
            "CST/CSOSN do Registro 54 "
            "excede 3 posicoes."
        )

    numero_item_digitos = _somente_digitos(
        numero_item
    )

    if not numero_item_digitos:
        raise ValueError(
            "Numero do item do Registro 54 "
            "nao informado."
        )

    if len(numero_item_digitos) > 3:
        raise ValueError(
            "Numero do item do Registro 54 "
            "excede 3 posicoes."
        )

    codigo_texto = _texto_sintegra(
        codigo_produto
    )

    if (
        not codigo_texto
        and not permitir_codigo_vazio
    ):
        raise ValueError(
            "Codigo do produto do Registro 54 "
            "nao informado."
        )

    if len(codigo_texto) > 14:
        raise ValueError(
            "Codigo do produto do Registro 54 "
            "excede 14 posicoes."
        )

    registro = "".join(
        [
            "54",
            _campo_numerico(
                cnpj_digitos,
                14,
            ),
            _campo_numerico(
                modelo_digitos,
                2,
            ),
            _campo_alfanumerico(
                serie_texto,
                3,
            ),
            _campo_numerico(
                numero_digitos,
                6,
            ),
            _campo_numerico(
                cfop_digitos,
                4,
            ),
            _campo_alfanumerico(
                cst_texto,
                3,
            ),
            _campo_numerico(
                numero_item_digitos,
                3,
            ),
            _campo_alfanumerico(
                codigo_texto,
                14,
            ),
            _campo_decimal(
                quantidade,
                11,
                3,
            ),
            _campo_decimal(
                valor_produto,
                12,
                2,
            ),
            _campo_decimal(
                valor_desconto,
                12,
                2,
            ),
            _campo_decimal(
                base_icms,
                12,
                2,
            ),
            _campo_decimal(
                base_icms_st,
                12,
                2,
            ),
            _campo_decimal(
                valor_ipi,
                12,
                2,
            ),
            _campo_decimal(
                aliquota_icms,
                4,
                2,
            ),
        ]
    )

    return _validar_tamanho_registro(
        registro,
        "54",
    )


def gerar_registros_54_despesas_acessorias(
    *,
    cnpj,
    modelo,
    serie,
    numero,
    cfop,
    cst,
    valor_frete=0,
    valor_seguro=0,
    valor_outras_despesas=0,
):
    especiais = (
        (
            "991",
            valor_frete,
        ),
        (
            "992",
            valor_seguro,
        ),
        (
            "999",
            valor_outras_despesas,
        ),
    )

    registros = []

    for numero_item, valor in especiais:

        valor_normalizado = _decimal_sintegra(
            valor,
            2,
        )

        if valor_normalizado < 0:
            raise ValueError(
                "Despesa acessoria do Registro "
                "54 nao pode ser negativa."
            )

        if valor_normalizado == 0:
            continue

        registro = gerar_registro_54(
            cnpj=cnpj,
            modelo=modelo,
            serie=serie,
            numero=numero,
            cfop=cfop,
            cst=cst,
            numero_item=numero_item,
            codigo_produto="",
            quantidade=0,
            valor_produto=0,
            valor_desconto=valor_normalizado,
            base_icms=0,
            base_icms_st=0,
            valor_ipi=0,
            aliquota_icms=0,
            permitir_codigo_vazio=True,
        )

        registros.append(
            registro
        )

    return registros


def gerar_registro_50(
    *,
    cnpj,
    inscricao_estadual,
    data_documento,
    uf,
    modelo,
    serie,
    numero,
    cfop,
    emitente,
    valor_total,
    base_icms,
    valor_icms,
    valor_isenta=0,
    valor_outras=0,
    aliquota_icms=0,
    situacao="N",
):
    cfop_digitos = _somente_digitos(
        cfop
    )

    if len(cfop_digitos) != 4:
        raise ValueError(
            "CFOP do Registro 50 deve "
            "possuir 4 digitos."
        )

    emitente_normalizado = (
        _texto_sintegra(
            emitente
        )
    )

    if emitente_normalizado not in (
        "P",
        "T",
    ):
        raise ValueError(
            "Emitente do Registro 50 "
            "deve ser P ou T."
        )

    situacao_normalizada = (
        _texto_sintegra(
            situacao
        )
    )

    if len(situacao_normalizada) != 1:
        raise ValueError(
            "Situacao do Registro 50 "
            "deve possuir 1 caractere."
        )

    registro = "".join(
        [
            "50",
            _campo_numerico(
                cnpj,
                14,
            ),
            _campo_alfanumerico(
                inscricao_estadual,
                14,
            ),
            _data_aaaammdd(
                data_documento
            ),
            _campo_alfanumerico(
                uf,
                2,
            ),
            _campo_numerico(
                modelo,
                2,
            ),
            _campo_alfanumerico(
                serie,
                3,
            ),
            _campo_numerico(
                normalizar_numero_documento_sintegra(
                    numero
                ),
                6,
            ),
            _campo_numerico(
                cfop_digitos,
                4,
            ),
            emitente_normalizado,
            _campo_decimal(
                valor_total,
                13,
                2,
            ),
            _campo_decimal(
                base_icms,
                13,
                2,
            ),
            _campo_decimal(
                valor_icms,
                13,
                2,
            ),
            _campo_decimal(
                valor_isenta,
                13,
                2,
            ),
            _campo_decimal(
                valor_outras,
                13,
                2,
            ),
            _campo_decimal(
                aliquota_icms,
                4,
                2,
            ),
            situacao_normalizada,
        ]
    )

    return _validar_tamanho_registro(
        registro,
        "50",
    )
def gerar_registros_50_agrupados(
    *,
    itens,
    cnpj,
    inscricao_estadual,
    data_documento,
    uf,
    modelo,
    serie,
    numero,
    emitente,
    valor_contabil_documento,
    situacao="N",
):
    grupos = agrupar_itens_registro_50(
        itens
    )

    if not grupos:
        raise ValueError(
            "Documento sem grupos para "
            "geracao do Registro 50."
        )

    valor_contabil_documento = (
        _decimal_sintegra(
            valor_contabil_documento,
            2,
        )
    )

    soma_grupos = sum(
        (
            _decimal_sintegra(
                grupo.get(
                    "valor_contabil",
                    0,
                ),
                2,
            )
            for grupo in grupos
        ),
        Decimal("0"),
    )

    soma_grupos = _decimal_sintegra(
        soma_grupos,
        2,
    )

    if soma_grupos != valor_contabil_documento:
        raise ValueError(
            "Registro 50 nao reconciliou com "
            "o valor contabil do documento: "
            f"grupos={soma_grupos} "
            f"documento={valor_contabil_documento}."
        )

    registros = []

    for grupo in grupos:

        registro = gerar_registro_50(
            cnpj=cnpj,
            inscricao_estadual=(
                inscricao_estadual
            ),
            data_documento=(
                data_documento
            ),
            uf=uf,
            modelo=modelo,
            serie=serie,
            numero=numero,
            cfop=grupo[
                "cfop_entrada"
            ],
            emitente=emitente,
            valor_total=grupo[
                "valor_contabil"
            ],
            base_icms=grupo[
                "base_icms"
            ],
            valor_icms=grupo[
                "valor_icms"
            ],
            valor_isenta=grupo[
                "valor_isenta_nao_tributada"
            ],
            valor_outras=grupo[
                "valor_outras"
            ],
            aliquota_icms=grupo[
                "aliquota_icms"
            ],
            situacao=situacao,
        )

        registros.append(
            registro
        )

    return registros


def calcular_valor_contabil_item_registro_50(
    item
):
    valor_produto = _decimal_sintegra(
        item.get(
            "valor_produto",
            0,
        ),
        2,
    )

    valor_frete = _decimal_sintegra(
        item.get(
            "valor_frete",
            0,
        ),
        2,
    )

    valor_seguro = _decimal_sintegra(
        item.get(
            "valor_seguro",
            0,
        ),
        2,
    )

    valor_outras_despesas = _decimal_sintegra(
        item.get(
            "valor_outras_despesas",
            0,
        ),
        2,
    )

    valor_ipi = _decimal_sintegra(
        item.get(
            "valor_ipi",
            0,
        ),
        2,
    )

    valor_desconto = _decimal_sintegra(
        item.get(
            "valor_desconto",
            0,
        ),
        2,
    )

    valor_contabil = (
        valor_produto
        + valor_frete
        + valor_seguro
        + valor_outras_despesas
        + valor_ipi
        - valor_desconto
    )

    if valor_contabil < 0:
        raise ValueError(
            "Valor contabil negativo no item "
            "do Registro 50."
        )

    return _decimal_sintegra(
        valor_contabil,
        2,
    )


def agrupar_itens_registro_50(
    itens,
):
    grupos = {}

    classificacoes_validas_registro_50 = {
        "TRIBUTADA",
        "ISENTA_NAO_TRIBUTADA",
        "OUTRAS",
    }

    for item in itens:

        cfop_entrada = _somente_digitos(
            item.get(
                "cfop_entrada"
            )
        )

        if len(cfop_entrada) != 4:
            raise ValueError(
                "Item sem CFOP de entrada confirmado "
                "para agrupamento do Registro 50."
            )

        aliquota = _decimal_sintegra(
            item.get(
                "aliquota_icms",
                0,
            ),
            4,
        )

        classificacao_registro_50 = str(
            item.get(
                "classificacao_registro_50"
            )
            or ""
        ).strip().upper()

        if (
            classificacao_registro_50
            not in classificacoes_validas_registro_50
        ):
            raise ValueError(
                "Item sem classificacao final valida "
                "para agrupamento do Registro 50."
            )

        valor_contabil_item = (
            calcular_valor_contabil_item_registro_50(
                item
            )
        )

        chave = (
            cfop_entrada,
            aliquota,
        )

        if chave not in grupos:

            grupos[chave] = {
                "cfop_entrada": cfop_entrada,
                "aliquota_icms": aliquota,
                "quantidade_itens": 0,
                "valor_produtos": Decimal("0"),
                "valor_desconto": Decimal("0"),
                "valor_contabil": Decimal("0"),
                "base_icms": Decimal("0"),
                "valor_icms": Decimal("0"),
                "valor_contabil_tributada":
                    Decimal("0"),
                "valor_isenta_nao_tributada":
                    Decimal("0"),
                "valor_outras":
                    Decimal("0"),
            }

        grupo = grupos[chave]

        grupo[
            "quantidade_itens"
        ] += 1

        grupo[
            "valor_produtos"
        ] += _decimal_sintegra(
            item.get(
                "valor_produto",
                0,
            ),
            2,
        )

        grupo[
            "valor_desconto"
        ] += _decimal_sintegra(
            item.get(
                "valor_desconto",
                0,
            ),
            2,
        )

        grupo[
            "valor_contabil"
        ] += valor_contabil_item

        grupo[
            "base_icms"
        ] += _decimal_sintegra(
            item.get(
                "base_icms",
                0,
            ),
            2,
        )

        grupo[
            "valor_icms"
        ] += _decimal_sintegra(
            item.get(
                "valor_icms",
                0,
            ),
            2,
        )

        if (
            classificacao_registro_50
            == "TRIBUTADA"
        ):
            grupo[
                "valor_contabil_tributada"
            ] += valor_contabil_item

        elif (
            classificacao_registro_50
            == "ISENTA_NAO_TRIBUTADA"
        ):
            grupo[
                "valor_isenta_nao_tributada"
            ] += valor_contabil_item

        elif (
            classificacao_registro_50
            == "OUTRAS"
        ):
            grupo[
                "valor_outras"
            ] += valor_contabil_item

    campos_monetarios = (
        "valor_produtos",
        "valor_desconto",
        "valor_contabil",
        "base_icms",
        "valor_icms",
        "valor_contabil_tributada",
        "valor_isenta_nao_tributada",
        "valor_outras",
    )

    resultado = []

    for chave in sorted(
        grupos
    ):

        grupo = grupos[
            chave
        ]

        for campo in campos_monetarios:
            grupo[campo] = (
                _decimal_sintegra(
                    grupo[campo],
                    2,
                )
            )

        resultado.append(
            grupo
        )

    return resultado



# ==========================================================
# PREPARAR ITENS PARA O REGISTRO 50
#
# O XML fornece os valores tributarios originais.
# O ERP fornece o CFOP de entrada confirmado.
#
# O vinculo entre as duas fontes e feito exclusivamente
# pelo numero do item (nItem) da NF-e.
#
# O CFOP existente no XML e preservado apenas como
# cfop_fornecedor. Ele nunca substitui cfop_entrada.
# ==========================================================

def preparar_itens_registro_50(
    itens_xml,
    itens_compra,
):
    itens_xml_por_numero = {}
    itens_compra_por_numero = {}

    for item_xml in itens_xml or []:
        numero_item = item_xml.get(
            "numero_item"
        )

        try:
            numero_item = int(
                numero_item
            )
        except (TypeError, ValueError):
            raise ValueError(
                "Item do XML sem nItem valido."
            )

        if numero_item <= 0:
            raise ValueError(
                "Item do XML com nItem invalido."
            )

        if numero_item in itens_xml_por_numero:
            raise ValueError(
                f"nItem {numero_item} duplicado no XML."
            )

        itens_xml_por_numero[
            numero_item
        ] = item_xml

    for item_compra in itens_compra or []:
        numero_item = item_compra.get(
            "numero_item_xml"
        )

        try:
            numero_item = int(
                numero_item
            )
        except (TypeError, ValueError):
            raise ValueError(
                "Item da compra sem numero_item_xml valido."
            )

        if numero_item <= 0:
            raise ValueError(
                "Item da compra com numero_item_xml invalido."
            )

        if numero_item in itens_compra_por_numero:
            raise ValueError(
                f"numero_item_xml {numero_item} "
                "duplicado na compra."
            )

        cfop_entrada = _somente_digitos(
            item_compra.get(
                "cfop_entrada"
            )
        )

        if len(cfop_entrada) != 4:
            raise ValueError(
                f"Item {numero_item} sem CFOP "
                "de entrada confirmado."
            )

        classificacao_registro_50 = str(
            item_compra.get(
                "classificacao_registro_50"
            )
            or ""
        ).strip().upper()

        classificacoes_validas_registro_50 = {
            "TRIBUTADA",
            "ISENTA_NAO_TRIBUTADA",
            "OUTRAS",
        }

        if (
            classificacao_registro_50
            not in classificacoes_validas_registro_50
        ):
            raise ValueError(
                f"Item {numero_item} sem classificacao "
                "final valida para o Registro 50."
            )

        itens_compra_por_numero[
            numero_item
        ] = item_compra

    numeros_xml = set(
        itens_xml_por_numero
    )

    numeros_compra = set(
        itens_compra_por_numero
    )

    faltando_na_compra = sorted(
        numeros_xml - numeros_compra
    )

    if faltando_na_compra:
        raise ValueError(
            "Itens do XML sem correspondente "
            "na compra: "
            + ", ".join(
                str(numero)
                for numero in faltando_na_compra
            )
        )

    faltando_no_xml = sorted(
        numeros_compra - numeros_xml
    )

    if faltando_no_xml:
        raise ValueError(
            "Itens da compra sem correspondente "
            "no XML: "
            + ", ".join(
                str(numero)
                for numero in faltando_no_xml
            )
        )

    resultado = []

    for numero_item in sorted(
        numeros_xml
    ):
        item_xml = dict(
            itens_xml_por_numero[
                numero_item
            ]
        )

        item_compra = (
            itens_compra_por_numero[
                numero_item
            ]
        )

        cfop_fornecedor = (
            _somente_digitos(
                item_xml.get(
                    "cfop"
                )
            )
        )

        cfop_entrada = (
            _somente_digitos(
                item_compra.get(
                    "cfop_entrada"
                )
            )
        )

        item_xml[
            "cfop_fornecedor"
        ] = cfop_fornecedor

        item_xml[
            "cfop_entrada"
        ] = cfop_entrada

        item_xml[
            "classificacao_registro_50"
        ] = str(
            item_compra.get(
                "classificacao_registro_50"
            )
            or ""
        ).strip().upper()

        resultado.append(
            item_xml
        )

    return resultado


# ==========================================================
# CLASSIFICAR ITEM PARA O REGISTRO 50
#
# Esta funcao e deliberadamente conservadora.
#
# Ela classifica automaticamente apenas situacoes cuja
# informacao disponivel permite determinar o tratamento
# nesta etapa.
#
# Situacoes ainda dependentes da escrituracao fiscal do
# estabelecimento retornam PENDENTE. O gerador final devera
# bloquear a competencia enquanto houver pendencias.
# ==========================================================

def classificar_item_registro_50(
    item,
):
    grupo = str(
        item.get("grupo") or ""
    ).strip().upper()

    cst = _somente_digitos(
        item.get("cst")
    )

    csosn = _somente_digitos(
        item.get("csosn")
    )

    base_icms = _decimal_sintegra(
        item.get(
            "base_icms",
            0,
        ),
        2,
    )

    valor_icms = _decimal_sintegra(
        item.get(
            "valor_icms",
            0,
        ),
        2,
    )

    aliquota_icms = _decimal_sintegra(
        item.get(
            "aliquota_icms",
            0,
        ),
        4,
    )

    resultado = {
        "classificacao_registro_50": "PENDENTE",
        "motivo_classificacao": None,
        "valor_isenta": Decimal("0"),
        "valor_outras": Decimal("0"),
    }

    # ------------------------------------------------------
    # CST 00 - tributacao integral
    # ------------------------------------------------------

    if (
        grupo == "ICMS00"
        and cst == "00"
    ):
        if (
            base_icms <= 0
            or aliquota_icms <= 0
        ):
            resultado[
                "motivo_classificacao"
            ] = (
                "CST 00 sem base ou aliquota de ICMS "
                "positiva."
            )

            return resultado

        resultado[
            "classificacao_registro_50"
        ] = "TRIBUTADA"

        resultado[
            "motivo_classificacao"
        ] = (
            "CST 00 com tributacao integral "
            "destacada no XML."
        )

        return resultado

    # ------------------------------------------------------
    # CST 40 - isenta
    # ------------------------------------------------------

    if (
        grupo == "ICMS40"
        and cst == "40"
    ):
        if (
            base_icms != 0
            or valor_icms != 0
        ):
            resultado[
                "motivo_classificacao"
            ] = (
                "CST 40 com base ou valor de ICMS "
                "diferente de zero; exige revisao."
            )

            return resultado

        resultado[
            "classificacao_registro_50"
        ] = "ISENTA_NAO_TRIBUTADA"

        resultado[
            "valor_isenta"
        ] = _decimal_sintegra(
            item.get(
                "valor_produto",
                0,
            ),
            2,
        )

        resultado[
            "motivo_classificacao"
        ] = (
            "CST 40 identificado como operacao isenta."
        )

        return resultado

    # ------------------------------------------------------
    # Simples Nacional
    #
    # CSOSN nao e convertido automaticamente em classificacao
    # do Registro 50. A classificacao deve refletir a
    # escrituracao fiscal do estabelecimento informante.
    # ------------------------------------------------------

    if csosn:
        resultado[
            "motivo_classificacao"
        ] = (
            f"CSOSN {csosn}: classificacao do Registro 50 "
            "depende da escrituracao fiscal da entrada."
        )

        return resultado

    resultado[
        "motivo_classificacao"
    ] = (
        "Situacao tributaria ainda nao mapeada "
        "para o Registro 50."
    )

    return resultado

# ==========================================================
# VINCULAR ITEM DO PARSER DE COMPRAS AO ITEM FISCAL DO XML
# ==========================================================

def vincular_itens_compra_fiscal(
    itens_compra,
    itens_fiscais,
):
    """
    Relaciona os itens do parser de Compras aos itens
    extraidos pelo leitor fiscal canonico do SINTEGRA.

    O vinculo e feito exclusivamente pelo nItem da NF-e:
        compras  -> numero_item_xml
        fiscal   -> numero_item

    Nao utiliza a posicao da lista como chave fiscal.
    """

    mapa_fiscal = {}

    for item_fiscal in (
        itens_fiscais
        or []
    ):
        try:
            numero_item = int(
                item_fiscal.get(
                    "numero_item"
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "Item fiscal sem numero_item valido."
            )

        if numero_item <= 0:
            raise ValueError(
                "Item fiscal com numero_item invalido."
            )

        if numero_item in mapa_fiscal:
            raise ValueError(
                "numero_item duplicado nos itens fiscais: "
                f"{numero_item}."
            )

        mapa_fiscal[
            numero_item
        ] = item_fiscal

    resultado = []
    numeros_compra = set()

    for item_compra in (
        itens_compra
        or []
    ):
        try:
            numero_item = int(
                item_compra.get(
                    "numero_item_xml"
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "Item da compra sem numero_item_xml valido."
            )

        if numero_item <= 0:
            raise ValueError(
                "Item da compra com numero_item_xml invalido."
            )

        if numero_item in numeros_compra:
            raise ValueError(
                "numero_item_xml duplicado nos itens da compra: "
                f"{numero_item}."
            )

        numeros_compra.add(
            numero_item
        )

        item_fiscal = mapa_fiscal.get(
            numero_item
        )

        if item_fiscal is None:
            raise ValueError(
                "Nao foi localizado o item fiscal correspondente "
                f"ao nItem {numero_item}."
            )

        item_enriquecido = dict(
            item_compra
        )

        item_enriquecido[
            "grupo"
        ] = item_fiscal.get(
            "grupo"
        )

        item_enriquecido[
            "origem"
        ] = item_fiscal.get(
            "origem"
        )

        item_enriquecido[
            "cst"
        ] = item_fiscal.get(
            "cst"
        )

        item_enriquecido[
            "cst_icms"
        ] = item_fiscal.get(
            "cst"
        )

        item_enriquecido[
            "csosn"
        ] = item_fiscal.get(
            "csosn"
        )

        item_enriquecido[
            "base_icms"
        ] = item_fiscal.get(
            "base_icms"
        )

        item_enriquecido[
            "aliquota_icms"
        ] = item_fiscal.get(
            "aliquota_icms"
        )

        item_enriquecido[
            "valor_icms"
        ] = item_fiscal.get(
            "valor_icms"
        )

        item_enriquecido[
            "valor_produto"
        ] = item_fiscal.get(
            "valor_produto"
        )

        resultado.append(
            item_enriquecido
        )

    numeros_fiscais = set(
        mapa_fiscal.keys()
    )

    if numeros_compra != numeros_fiscais:
        faltando_compra = sorted(
            numeros_fiscais
            - numeros_compra
        )

        extras_compra = sorted(
            numeros_compra
            - numeros_fiscais
        )

        raise ValueError(
            "Divergencia entre itens da compra e itens fiscais. "
            f"Somente fiscal={faltando_compra}; "
            f"somente compra={extras_compra}."
        )

    return resultado




def gerar_registro_61(
    data_emissao,
    modelo,
    serie,
    numero_inicial,
    numero_final,
    valor_total,
    base_icms=0,
    valor_icms=0,
    valor_isenta=0,
    valor_outras=0,
    aliquota_icms=0,
    subserie="",
):
    """
    Gera Registro Tipo 61 do SINTEGRA.

    Consolidacao diaria por:
    modelo + serie + subserie + aliquota.
    """

    modelo_texto = _texto_sintegra(
        modelo
    ).strip()

    if modelo_texto != "65":
        raise ValueError(
            "Registro 61 desta rotina "
            "aceita somente NFC-e modelo 65."
        )

    serie_texto = _texto_sintegra(
        serie
    ).strip()

    if len(serie_texto) > 3:
        raise ValueError(
            "Serie excede 3 caracteres "
            "no Registro 61."
        )

    subserie_texto = _texto_sintegra(
        subserie
    ).strip()

    if len(subserie_texto) > 2:
        raise ValueError(
            "Subserie excede 2 caracteres "
            "no Registro 61."
        )

    numero_inicial = (
        normalizar_numero_documento_sintegra(
            numero_inicial
        )
    )

    numero_final = (
        normalizar_numero_documento_sintegra(
            numero_final
        )
    )

    registro = "".join([
        "61",

        _campo_alfanumerico(
            "",
            14,
        ),

        _campo_alfanumerico(
            "",
            14,
        ),

        _data_aaaammdd(
            data_emissao
        ),

        _campo_alfanumerico(
            modelo_texto,
            2,
        ),

        _campo_alfanumerico(
            serie_texto,
            3,
        ),

        _campo_alfanumerico(
            subserie_texto,
            2,
        ),

        _campo_numerico(
            numero_inicial,
            6,
        ),

        _campo_numerico(
            numero_final,
            6,
        ),

        _campo_decimal(
            valor_total,
            13,
            2,
        ),

        _campo_decimal(
            base_icms,
            13,
            2,
        ),

        _campo_decimal(
            valor_icms,
            12,
            2,
        ),

        _campo_decimal(
            valor_isenta,
            13,
            2,
        ),

        _campo_decimal(
            valor_outras,
            13,
            2,
        ),

        _campo_decimal(
            aliquota_icms,
            4,
            2,
        ),

        _campo_alfanumerico(
            "",
            1,
        ),
    ])

    return _validar_tamanho_registro(
        registro,
        "61",
    )


def gerar_registro_61r(
    mes,
    ano,
    codigo_produto,
    quantidade,
    valor_bruto,
    base_icms,
    aliquota_icms,
):
    """
    Gera Registro Tipo 61R do SINTEGRA.

    Deve existir um registro para cada
    combinacao produto + aliquota no mes.
    """

    try:
        mes_numero = int(mes)
        ano_numero = int(ano)
    except (TypeError, ValueError):
        raise ValueError(
            "Mes e ano invalidos "
            "para Registro 61R."
        )

    if not 1 <= mes_numero <= 12:
        raise ValueError(
            "Mes invalido para Registro 61R."
        )

    if not 1900 <= ano_numero <= 9999:
        raise ValueError(
            "Ano invalido para Registro 61R."
        )

    codigo = _texto_sintegra(
        codigo_produto
    ).strip()

    if not codigo:
        raise ValueError(
            "Codigo do produto obrigatorio "
            "no Registro 61R."
        )

    if len(codigo) > 14:
        raise ValueError(
            "Codigo do produto excede "
            "14 caracteres no Registro 61R."
        )

    periodo = (
        f"{mes_numero:02d}"
        f"{ano_numero:04d}"
    )

    registro = "".join([
        "61",
        "R",

        periodo,

        _campo_alfanumerico(
            codigo,
            14,
        ),

        _campo_decimal(
            quantidade,
            13,
            3,
        ),

        _campo_decimal(
            valor_bruto,
            16,
            2,
        ),

        _campo_decimal(
            base_icms,
            16,
            2,
        ),

        _campo_decimal(
            aliquota_icms,
            4,
            2,
        ),

        _campo_alfanumerico(
            "",
            54,
        ),
    ])

    return _validar_tamanho_registro(
        registro,
        "61R",
    )



def agrupar_documentos_registros_61_61r(
    documentos,
    *,
    mes,
    ano,
):
    """
    Consolida dados de NFC-e modelo 65 para
    composicao dos Registros 61 e 61R.

    Registro 61:
    data + modelo + serie + subserie + aliquota

    Registro 61R:
    produto + aliquota no mes

    Esta funcao nao acessa banco e nao gera TXT.
    """

    from collections import defaultdict
    from datetime import datetime
    from decimal import Decimal

    try:
        mes_numero = int(mes)
        ano_numero = int(ano)
    except (TypeError, ValueError):
        raise ValueError(
            "Mes e ano invalidos para "
            "agrupamento 61/61R."
        )

    if not 1 <= mes_numero <= 12:
        raise ValueError(
            "Mes invalido para agrupamento "
            "61/61R."
        )

    if not 1900 <= ano_numero <= 9999:
        raise ValueError(
            "Ano invalido para agrupamento "
            "61/61R."
        )

    grupos_61 = defaultdict(
        lambda: {
            "numeros": [],
            "valor_total": Decimal("0.00"),
            "base_icms": Decimal("0.00"),
            "valor_icms": Decimal("0.00"),
            "valor_isenta": Decimal("0.00"),
            "valor_outras": Decimal("0.00"),
        }
    )

    grupos_61r = defaultdict(
        lambda: {
            "quantidade": Decimal("0.000"),
            "valor_bruto": Decimal("0.00"),
            "base_icms": Decimal("0.00"),
        }
    )

    def decimal(valor):
        if valor in (
            None,
            "",
        ):
            return Decimal("0")

        return Decimal(
            str(valor)
        )

    def data_documento(valor):
        if isinstance(
            valor,
            datetime,
        ):
            return valor.date()

        if hasattr(
            valor,
            "year",
        ) and hasattr(
            valor,
            "month",
        ) and hasattr(
            valor,
            "day",
        ):
            return valor

        texto_data = str(
            valor or ""
        ).strip()

        if not texto_data:
            raise ValueError(
                "Data de emissao ausente "
                "na NFC-e."
            )

        try:
            return datetime.fromisoformat(
                texto_data.replace(
                    "Z",
                    "+00:00",
                )
            ).date()
        except ValueError as exc:
            raise ValueError(
                "Data de emissao invalida "
                f"na NFC-e: {texto_data}"
            ) from exc

    for documento in documentos:

        modelo = _texto_sintegra(
            documento.get(
                "modelo"
            )
        ).strip()

        if modelo != "65":
            raise ValueError(
                "Agrupamento 61/61R recebeu "
                "documento diferente do modelo 65."
            )

        data_emissao = data_documento(
            documento.get(
                "data_emissao"
            )
        )

        if (
            data_emissao.month
            != mes_numero
            or data_emissao.year
            != ano_numero
        ):
            raise ValueError(
                "NFC-e fora da competencia "
                f"{mes_numero:02d}/{ano_numero}."
            )

        serie = _texto_sintegra(
            documento.get(
                "serie"
            )
        ).strip()

        if not serie:
            raise ValueError(
                "Serie ausente na NFC-e."
            )

        subserie = _texto_sintegra(
            documento.get(
                "subserie",
                "",
            )
        ).strip()

        numero = documento.get(
            "numero"
        )

        numero_normalizado = (
            normalizar_numero_documento_sintegra(
                numero
            )
        )

        totais = (
            documento.get(
                "totais"
            )
            or {}
        )

        valor_total_documento = decimal(
            totais.get(
                "valor_nota"
            )
        )

        itens = (
            documento.get(
                "itens"
            )
            or []
        )

        if not itens:
            raise ValueError(
                "NFC-e sem itens para "
                "agrupamento 61/61R."
            )

        soma_bruta = Decimal("0.00")

        for item in itens:

            codigo_produto = _texto_sintegra(
                item.get(
                    "codigo_produto"
                )
            ).strip()

            if not codigo_produto:
                raise ValueError(
                    "Item da NFC-e sem codigo "
                    "de produto."
                )

            icms = (
                item.get(
                    "icms"
                )
                or {}
            )

            aliquota = decimal(
                icms.get(
                    "aliquota_icms"
                )
            )

            base_icms_item = decimal(
                icms.get(
                    "base_icms"
                )
            )

            valor_icms_item = decimal(
                icms.get(
                    "valor_icms"
                )
            )

            quantidade = decimal(
                item.get(
                    "quantidade"
                )
            )

            valor_produto = decimal(
                item.get(
                    "valor_produto"
                )
            )

            if quantidade < 0:
                raise ValueError(
                    "Quantidade negativa "
                    "no Registro 61R."
                )

            if valor_produto < 0:
                raise ValueError(
                    "Valor bruto negativo "
                    "no Registro 61R."
                )

            soma_bruta += valor_produto

            chave_61r = (
                codigo_produto,
                aliquota,
            )

            grupo_61r = grupos_61r[
                chave_61r
            ]

            grupo_61r[
                "quantidade"
            ] += quantidade

            grupo_61r[
                "valor_bruto"
            ] += valor_produto

            grupo_61r[
                "base_icms"
            ] += base_icms_item

        valor_produtos_total = decimal(
            totais.get(
                "valor_produtos"
            )
        )

        if (
            soma_bruta.quantize(
                Decimal("0.01")
            )
            !=
            valor_produtos_total.quantize(
                Decimal("0.01")
            )
        ):
            raise ValueError(
                "Soma bruta dos itens da NFC-e "
                "nao confere com vProd."
            )

        aliquotas_documento = {
            decimal(
                (
                    item.get(
                        "icms"
                    )
                    or {}
                ).get(
                    "aliquota_icms"
                )
            )
            for item in itens
        }

        if len(
            aliquotas_documento
        ) != 1:
            raise ValueError(
                "NFC-e possui mais de uma "
                "aliquota de ICMS. "
                "A distribuicao do Registro 61 "
                "deve ser tratada explicitamente."
            )

        aliquota_documento = next(
            iter(
                aliquotas_documento
            )
        )

        base_icms_documento = decimal(
            totais.get(
                "base_icms"
            )
        )

        valor_icms_documento = decimal(
            totais.get(
                "valor_icms"
            )
        )

        valor_isenta_documento = (
            Decimal("0.00")
        )

        valor_outras_documento = (
            valor_total_documento
        )

        chave_61 = (
            data_emissao,
            modelo,
            serie,
            subserie,
            aliquota_documento,
        )

        grupo_61 = grupos_61[
            chave_61
        ]

        grupo_61[
            "numeros"
        ].append(
            int(
                numero_normalizado
            )
        )

        grupo_61[
            "valor_total"
        ] += valor_total_documento

        grupo_61[
            "base_icms"
        ] += base_icms_documento

        grupo_61[
            "valor_icms"
        ] += valor_icms_documento

        grupo_61[
            "valor_isenta"
        ] += valor_isenta_documento

        grupo_61[
            "valor_outras"
        ] += valor_outras_documento

    resultado_61 = []

    for chave in sorted(
        grupos_61.keys()
    ):

        (
            data_emissao,
            modelo,
            serie,
            subserie,
            aliquota,
        ) = chave

        grupo = grupos_61[
            chave
        ]

        numeros = sorted(
            grupo[
                "numeros"
            ]
        )

        resultado_61.append({
            "data_emissao": data_emissao,
            "modelo": modelo,
            "serie": serie,
            "subserie": subserie,
            "numero_inicial": min(
                numeros
            ),
            "numero_final": max(
                numeros
            ),
            "valor_total": grupo[
                "valor_total"
            ],
            "base_icms": grupo[
                "base_icms"
            ],
            "valor_icms": grupo[
                "valor_icms"
            ],
            "valor_isenta": grupo[
                "valor_isenta"
            ],
            "valor_outras": grupo[
                "valor_outras"
            ],
            "aliquota_icms": aliquota,
        })

    resultado_61r = []

    for chave in sorted(
        grupos_61r.keys()
    ):

        (
            codigo_produto,
            aliquota,
        ) = chave

        grupo = grupos_61r[
            chave
        ]

        resultado_61r.append({
            "mes": mes_numero,
            "ano": ano_numero,
            "codigo_produto": (
                codigo_produto
            ),
            "quantidade": grupo[
                "quantidade"
            ],
            "valor_bruto": grupo[
                "valor_bruto"
            ],
            "base_icms": grupo[
                "base_icms"
            ],
            "aliquota_icms": aliquota,
        })

    return {
        "registro_61": resultado_61,
        "registro_61r": resultado_61r,
    }


def gerar_registros_61_61r(
    documentos,
    *,
    mes,
    ano,
):
    """
    Consolida as NFC-e e devolve as linhas
    formatadas dos Registros 61 e 61R.
    """

    agrupado = (
        agrupar_documentos_registros_61_61r(
            documentos,
            mes=mes,
            ano=ano,
        )
    )

    registros_61 = [
        gerar_registro_61(
            **dados
        )
        for dados
        in agrupado[
            "registro_61"
        ]
    ]

    registros_61r = [
        gerar_registro_61r(
            **dados
        )
        for dados
        in agrupado[
            "registro_61r"
        ]
    ]

    return {
        "registro_61": registros_61,
        "registro_61r": registros_61r,
        "dados_61": agrupado[
            "registro_61"
        ],
        "dados_61r": agrupado[
            "registro_61r"
        ],
    }



def gerar_registro_75(
    *,
    data_inicial,
    data_final,
    codigo_produto,
    ncm,
    descricao,
    unidade,
    aliquota_ipi=0,
    aliquota_icms=0,
    reducao_base_icms=0,
    base_icms_st_unitaria=0,
):
    """
    Gera Registro Tipo 75 do SINTEGRA.

    Layout:
    01-02   Tipo
    03-10   Data inicial
    11-18   Data final
    19-32   Codigo produto
    33-40   NCM
    41-93   Descricao
    94-99   Unidade
    100-104 Aliquota IPI
    105-108 Aliquota ICMS
    109-113 Reducao BC ICMS
    114-126 BC ICMS-ST unitaria
    """

    codigo = _texto_sintegra(
        codigo_produto
    ).strip()

    if not codigo:
        raise ValueError(
            "Codigo do produto obrigatorio "
            "no Registro 75."
        )

    if len(codigo) > 14:
        raise ValueError(
            "Codigo do produto excede "
            "14 caracteres no Registro 75."
        )

    ncm_texto = _texto_sintegra(
        ncm
    ).strip()

    if ncm_texto:
        ncm_digitos = _somente_digitos(
            ncm_texto
        )

        if len(ncm_digitos) != 8:
            raise ValueError(
                "NCM deve possuir 8 digitos "
                "no Registro 75."
            )

        ncm_texto = ncm_digitos

    descricao_texto = _texto_sintegra(
        descricao
    ).strip()

    if not descricao_texto:
        raise ValueError(
            "Descricao obrigatoria "
            "no Registro 75."
        )

    unidade_texto = _texto_sintegra(
        unidade
    ).strip()

    if not unidade_texto:
        raise ValueError(
            "Unidade obrigatoria "
            "no Registro 75."
        )

    if len(unidade_texto) > 6:
        raise ValueError(
            "Unidade excede 6 caracteres "
            "no Registro 75."
        )

    registro = "".join([
        "75",

        _data_aaaammdd(
            data_inicial
        ),

        _data_aaaammdd(
            data_final
        ),

        _campo_alfanumerico(
            codigo,
            14,
        ),

        _campo_alfanumerico(
            ncm_texto,
            8,
        ),

        _campo_alfanumerico(
            descricao_texto,
            53,
        ),

        _campo_alfanumerico(
            unidade_texto,
            6,
        ),

        _campo_decimal(
            aliquota_ipi,
            5,
            2,
        ),

        _campo_decimal(
            aliquota_icms,
            4,
            2,
        ),

        _campo_decimal(
            reducao_base_icms,
            5,
            2,
        ),

        _campo_decimal(
            base_icms_st_unitaria,
            13,
            2,
        ),
    ])

    return _validar_tamanho_registro(
        registro,
        "75",
    )



def coletar_produtos_registro_75(
    documentos,
    *,
    data_inicial,
    data_final,
):
    """
    Coleta produtos dos documentos fiscais
    para composicao do Registro 75.

    Um produto e emitido uma unica vez para
    cada combinacao codigo + aliquota ICMS.

    A funcao nao acessa banco e nao gera TXT.
    """

    from decimal import Decimal

    produtos = {}

    def decimal(valor):
        if valor in (
            None,
            "",
        ):
            return Decimal("0")

        return Decimal(
            str(valor)
        )

    for documento in documentos:

        itens = (
            documento.get(
                "itens"
            )
            or []
        )

        for item in itens:

            codigo = _texto_sintegra(
                item.get(
                    "codigo_produto"
                )
            ).strip()

            if not codigo:
                raise ValueError(
                    "Produto sem codigo para "
                    "Registro 75."
                )

            ncm = _texto_sintegra(
                item.get(
                    "ncm"
                )
            ).strip()

            descricao = _texto_sintegra(
                item.get(
                    "descricao"
                )
            ).strip()

            unidade = _texto_sintegra(
                item.get(
                    "unidade"
                )
            ).strip()

            icms = (
                item.get(
                    "icms"
                )
                or {}
            )

            ipi = (
                item.get(
                    "ipi"
                )
                or {}
            )

            aliquota_icms = decimal(
                icms.get(
                    "aliquota_icms"
                )
            )

            aliquota_ipi = decimal(
                ipi.get(
                    "aliquota_ipi"
                )
            )

            base_icms_st = decimal(
                icms.get(
                    "base_icms_st"
                )
            )

            quantidade = decimal(
                item.get(
                    "quantidade"
                )
            )

            if (
                base_icms_st
                and quantidade > 0
            ):
                base_icms_st_unitaria = (
                    base_icms_st
                    / quantidade
                )
            else:
                base_icms_st_unitaria = (
                    Decimal("0")
                )

            chave = (
                codigo,
                aliquota_icms,
            )

            dados = {
                "data_inicial": data_inicial,
                "data_final": data_final,
                "codigo_produto": codigo,
                "ncm": ncm,
                "descricao": descricao,
                "unidade": unidade,
                "aliquota_ipi": aliquota_ipi,
                "aliquota_icms": aliquota_icms,
                "reducao_base_icms": (
                    Decimal("0")
                ),
                "base_icms_st_unitaria": (
                    base_icms_st_unitaria
                ),
            }

            if chave not in produtos:
                produtos[chave] = dados
                continue

            anterior = produtos[
                chave
            ]

            campos_identificacao = (
                "ncm",
                "descricao",
                "unidade",
            )

            divergencias = [
                campo
                for campo
                in campos_identificacao
                if anterior[campo]
                != dados[campo]
            ]

            if divergencias:
                raise ValueError(
                    "Produto com dados divergentes "
                    "no Registro 75. "
                    f"Codigo: {codigo}. "
                    "Campos: "
                    + ", ".join(
                        divergencias
                    )
                )

            if (
                anterior[
                    "aliquota_ipi"
                ]
                != dados[
                    "aliquota_ipi"
                ]
            ):
                raise ValueError(
                    "Produto com aliquota de IPI "
                    "divergente no Registro 75. "
                    f"Codigo: {codigo}."
                )

            if (
                anterior[
                    "base_icms_st_unitaria"
                ]
                != dados[
                    "base_icms_st_unitaria"
                ]
            ):
                raise ValueError(
                    "Produto com base unitaria "
                    "de ICMS-ST divergente no "
                    "Registro 75. "
                    f"Codigo: {codigo}."
                )

    return [
        produtos[chave]
        for chave
        in sorted(
            produtos.keys()
        )
    ]


def gerar_registros_75(
    documentos,
    *,
    data_inicial,
    data_final,
):
    """
    Coleta os produtos e gera os
    Registros 75 correspondentes.
    """

    produtos = (
        coletar_produtos_registro_75(
            documentos,
            data_inicial=data_inicial,
            data_final=data_final,
        )
    )

    return [
        gerar_registro_75(
            **produto
        )
        for produto
        in produtos
    ]



def identificar_tipo_registro_sintegra(
    registro,
):
    """
    Identifica o tipo SINTEGRA para totalizacao.

    Tipos alfanumericos derivados, como 61R,
    pertencem ao tipo numerico principal 61
    para efeito do Registro 90.
    """

    texto = str(
        registro or ""
    )

    if len(texto) < 2:
        raise ValueError(
            "Registro SINTEGRA invalido "
            "para totalizacao."
        )

    tipo = texto[:2]

    if not tipo.isdigit():
        raise ValueError(
            "Tipo de registro SINTEGRA "
            "invalido: "
            f"{tipo!r}."
        )

    return tipo


def contar_registros_para_90(
    registros,
):
    """
    Conta somente os tipos que recebem
    totalizador proprio no Registro 90.

    Registros 10, 11 e 90 participam apenas
    do Total Geral.
    """

    from collections import Counter

    contador = Counter()

    for registro in registros:

        tipo = (
            identificar_tipo_registro_sintegra(
                registro
            )
        )

        if tipo in {
            "10",
            "11",
            "90",
        }:
            continue

        contador[tipo] += 1

    return dict(
        sorted(
            contador.items()
        )
    )


def gerar_registros_90(
    *,
    cnpj,
    inscricao_estadual,
    registros,
):
    """
    Gera um ou mais Registros Tipo 90.

    Cada totalizador ocupa:
        tipo       = 2 posicoes
        quantidade = 8 posicoes

    O Total Geral usa:
        99         = 2 posicoes
        quantidade = 8 posicoes

    A posicao 126 informa a quantidade
    total de Registros Tipo 90.

    O Total Geral e informado apenas no
    ultimo Registro 90.
    """

    cnpj_digitos = _somente_digitos(
        cnpj
    )

    if len(cnpj_digitos) != 14:
        raise ValueError(
            "CNPJ do informante deve possuir "
            "14 digitos no Registro 90."
        )

    ie = _texto_sintegra(
        inscricao_estadual
    ).strip()

    if not ie:
        raise ValueError(
            "Inscricao Estadual obrigatoria "
            "no Registro 90."
        )

    if len(ie) > 14:
        raise ValueError(
            "Inscricao Estadual excede "
            "14 caracteres no Registro 90."
        )

    registros_base = list(
        registros
    )

    totais = contar_registros_para_90(
        registros_base
    )

    pares = list(
        totais.items()
    )

    # Posicoes 1-30:
    # tipo + CNPJ + IE.
    #
    # Posicao 126:
    # quantidade de Registros 90.
    #
    # Sobram 95 posicoes entre 31 e 125.
    #
    # Cada par tipo/quantidade ocupa 10.
    # No ultimo registro, o Total Geral
    # tambem ocupa 10.
    #
    # Assim, usamos no maximo 9 pares em
    # registros intermediarios e 8 pares
    # no ultimo, reservando espaco ao 99.
    grupos = []

    restantes = list(
        pares
    )

    while len(restantes) > 8:
        grupos.append(
            restantes[:9]
        )

        restantes = restantes[9:]

    grupos.append(
        restantes
    )

    quantidade_registros_90 = len(
        grupos
    )

    if quantidade_registros_90 > 9:
        raise ValueError(
            "Quantidade de Registros 90 "
            "excede uma posicao."
        )

    total_geral = (
        len(registros_base)
        + quantidade_registros_90
    )

    resultado = []

    for indice, grupo in enumerate(
        grupos
    ):

        ultimo = (
            indice
            == quantidade_registros_90 - 1
        )

        corpo = "".join([
            "90",
            cnpj_digitos,
            _campo_alfanumerico(
                ie,
                14,
            ),
        ])

        for tipo, quantidade in grupo:

            if len(tipo) != 2:
                raise ValueError(
                    "Tipo invalido para "
                    "Registro 90: "
                    f"{tipo!r}."
                )

            if quantidade > 99999999:
                raise ValueError(
                    "Quantidade excede "
                    "8 posicoes no "
                    f"totalizador {tipo}."
                )

            corpo += tipo
            corpo += str(
                quantidade
            ).zfill(8)

        if ultimo:

            if total_geral > 99999999:
                raise ValueError(
                    "Total geral excede "
                    "8 posicoes no "
                    "Registro 90."
                )

            corpo += "99"
            corpo += str(
                total_geral
            ).zfill(8)

        if len(corpo) > 125:
            raise ValueError(
                "Conteudo excedeu a posicao "
                "125 do Registro 90."
            )

        corpo = corpo.ljust(
            125
        )

        registro = (
            corpo
            + str(
                quantidade_registros_90
            )
        )

        if len(registro) != 126:
            raise ValueError(
                "Registro 90 deve possuir "
                "126 caracteres."
            )

        resultado.append(
            registro
        )

    return resultado



def montar_arquivo_sintegra(
    *,
    registro_10,
    registro_11,
    registros_50=None,
    registros_54=None,
    registros_61=None,
    registros_61r=None,
    registros_75=None,
    cnpj,
    inscricao_estadual,
):
    """
    Monta estruturalmente o arquivo SINTEGRA.

    Esta funcao nao acessa banco,
    nao grava arquivo e nao transmite dados.

    Ordem:
        10
        11
        50
        54
        61
        61R
        75
        90
    """

    grupos = {
        "50": list(
            registros_50 or []
        ),
        "54": list(
            registros_54 or []
        ),
        "61": list(
            registros_61 or []
        ),
        "61R": list(
            registros_61r or []
        ),
        "75": list(
            registros_75 or []
        ),
    }

    if not str(
        registro_10 or ""
    ).startswith("10"):
        raise ValueError(
            "Registro 10 ausente ou invalido."
        )

    if not str(
        registro_11 or ""
    ).startswith("11"):
        raise ValueError(
            "Registro 11 ausente ou invalido."
        )

    registros = [
        registro_10,
        registro_11,
    ]

    ordem = (
        "50",
        "54",
        "61",
        "61R",
        "75",
    )

    for tipo in ordem:

        for registro in grupos[tipo]:

            texto_registro = str(
                registro or ""
            )

            if not texto_registro.startswith(
                tipo
            ):
                raise ValueError(
                    "Registro recebido no grupo "
                    f"{tipo} possui tipo invalido: "
                    f"{texto_registro[:3]!r}."
                )

            registros.append(
                texto_registro
            )

    for registro in registros:

        if len(registro) != 126:
            raise ValueError(
                "Registro SINTEGRA com tamanho "
                "diferente de 126 antes do "
                "fechamento: "
                f"{registro[:3]!r} "
                f"({len(registro)} caracteres)."
            )

    registros_90 = gerar_registros_90(
        cnpj=cnpj,
        inscricao_estadual=inscricao_estadual,
        registros=registros,
    )

    registros.extend(
        registros_90
    )

    for registro in registros:

        if len(registro) != 126:
            raise ValueError(
                "Arquivo SINTEGRA contem "
                "registro diferente de "
                "126 caracteres."
            )

    if not registros[-1].startswith(
        "90"
    ):
        raise ValueError(
            "Arquivo SINTEGRA nao termina "
            "com Registro 90."
        )

    contagem = {}

    for registro in registros:

        tipo = (
            "61R"
            if registro.startswith("61R")
            else registro[:2]
        )

        contagem[tipo] = (
            contagem.get(
                tipo,
                0,
            )
            + 1
        )

    return {
        "registros": registros,
        "quantidade_total": len(
            registros
        ),
        "contagem": contagem,
        "quantidade_registros_90": len(
            registros_90
        ),
    }


def serializar_arquivo_sintegra(
    montagem,
):
    """
    Serializa a montagem em texto.

    Nao grava arquivo em disco.
    """

    registros = montagem.get(
        "registros"
    )

    if not registros:
        raise ValueError(
            "Montagem SINTEGRA vazia."
        )

    for registro in registros:

        if len(registro) != 126:
            raise ValueError(
                "Nao e possivel serializar "
                "registro diferente de "
                "126 caracteres."
            )

    return (
        "\r\n".join(
            registros
        )
        + "\r\n"
    )
