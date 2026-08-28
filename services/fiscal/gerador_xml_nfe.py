from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from services.fiscal.chave_acesso_nfe import (
    gerar_chave_acesso_nfe
)

from xml.etree.ElementTree import (
    Element,
    SubElement,
    tostring
)


# ============================================================
# GERADOR XML NF-e
#
# ETAPA ATUAL:
# - monta estrutura da NF-e modelo 55
# - gera chave de acesso de 44 dígitos
# - inclui cNF, dhEmi, cDV e Id da infNFe
# - monta emitente e destinatário
# - monta ICMS
# - monta PIS / COFINS
# - monta totais, transporte e pagamento
# - NÃO assina XML
# - NÃO transmite para SEFAZ
# - NÃO grava documento fiscal
# - NÃO consome numeração
# ============================================================


NAMESPACE_NFE = (
    "http://www.portalfiscal.inf.br/nfe"
)

VERSAO_NFE = "4.00"

XNOME_DESTINATARIO_HOMOLOGACAO = (
    "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
)


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _texto(
    valor
):

    if valor is None:
        return None

    texto = str(
        valor
    ).strip()

    if texto.upper() in (
        "",
        "NONE",
        "NULL",
        "NAN",
        "<NA>"
    ):

        return None

    return texto


# ============================================================
# CONVERTER PARA DECIMAL
# ============================================================
def _decimal(
    valor,
    padrao=None
):

    if valor is None:
        return padrao

    texto = str(
        valor
    ).strip()

    if not texto:
        return padrao

    texto = texto.replace(
        ",",
        "."
    )

    try:

        return Decimal(
            texto
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError
    ):

        return padrao


# ============================================================
# CRIAR TAG SOMENTE QUANDO HOUVER VALOR
# ============================================================
def _tag(
    pai,
    nome,
    valor
):

    valor = _texto(
        valor
    )

    if valor is None:
        return None

    elemento = SubElement(
        pai,
        nome
    )

    elemento.text = valor

    return elemento


# ============================================================
# FORMATAR QUANTIDADE
# ============================================================
def _formatar_quantidade(
    valor
):

    numero = _decimal(
        valor,
        Decimal("0")
    )

    return (
        f"{numero:.4f}"
    )


# ============================================================
# FORMATAR VALOR MONETÁRIO
# ============================================================
def _formatar_valor(
    valor
):

    numero = _decimal(
        valor,
        Decimal("0")
    )

    numero = numero.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    return (
        f"{numero:.2f}"
    )


# ============================================================
# FORMATAR ALÍQUOTA
# ============================================================
def _formatar_aliquota(
    valor
):

    numero = _decimal(
        valor,
        Decimal("0")
    )

    numero = numero.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP
    )

    return (
        f"{numero:.4f}"
    )


# ============================================================
# CALCULAR TRIBUTO PERCENTUAL
# ============================================================
def _calcular_tributo_percentual(
    base,
    aliquota
):

    base_decimal = _decimal(
        base,
        Decimal("0")
    )

    aliquota_decimal = _decimal(
        aliquota,
        Decimal("0")
    )

    valor = (
        base_decimal
        *
        aliquota_decimal
        /
        Decimal("100")
    )

    return valor.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ============================================================
# FUSO HORÁRIO PADRÃO DA EMPRESA
#
# Verde Infância / MG: UTC-03:00
# ============================================================
FUSO_EMPRESA = timezone(
    timedelta(
        hours=-3
    )
)


# ============================================================
# NORMALIZAR DATA/HORA DE EMISSÃO
# ============================================================
def _normalizar_data_emissao(
    valor
):

    if valor is None:

        return datetime.now(
            FUSO_EMPRESA
        )

    if isinstance(
        valor,
        datetime
    ):

        data_emissao = valor

    else:

        try:

            data_emissao = datetime.fromisoformat(
                str(
                    valor
                ).strip()
            )

        except Exception as erro:

            raise ValueError(
                "Data/hora de emissão inválida."
            ) from erro

    if data_emissao.tzinfo is None:

        data_emissao = data_emissao.replace(
            tzinfo=FUSO_EMPRESA
        )

    return data_emissao.astimezone(
        FUSO_EMPRESA
    )


# ============================================================
# RESOLVER DATA/HORA DE EMISSÃO DO RASCUNHO
# ============================================================
def _resolver_data_emissao(
    rascunho
):

    valor = rascunho.get(
        "data_emissao"
    )

    if valor is None:

        venda = rascunho.get(
            "venda",
            {}
        )

        if isinstance(
            venda,
            dict
        ):

            valor = venda.get(
                "data_venda"
            )

    return _normalizar_data_emissao(
        valor
    )


# ============================================================
# RESOLVER CÓDIGO DA UF
# ============================================================
def _resolver_codigo_uf(
    rascunho
):

    codigo_uf = _texto(
        rascunho.get(
            "codigo_uf"
        )
    )

    if codigo_uf:

        return codigo_uf.zfill(
            2
        )

    emitente = rascunho.get(
        "emitente",
        {}
    )

    codigo_municipio = _texto(
        emitente.get(
            "codigo_municipio_ibge"
        )
    )

    if (
        codigo_municipio
        and
        len(
            codigo_municipio
        ) >= 2
    ):

        return codigo_municipio[
            :2
        ]

    raise ValueError(
        "Não foi possível determinar o código da UF."
    )


# ============================================================
# RESOLVER cNF
# ============================================================
def _resolver_codigo_numerico(
    rascunho
):

    codigo = _texto(
        rascunho.get(
            "codigo_numerico"
        )
    )

    if codigo:

        numeros = "".join(
            caractere
            for caractere in codigo
            if caractere.isdigit()
        )

        if not numeros:

            raise ValueError(
                "Código numérico da NF-e inválido."
            )

        if len(
            numeros
        ) > 8:

            raise ValueError(
                "Código numérico da NF-e deve possuir até 8 dígitos."
            )

        return numeros.zfill(
            8
        )

    numero = rascunho.get(
        "numero_sugerido"
    )

    try:

        numero = int(
            numero
        )

    except (
        TypeError,
        ValueError
    ) as erro:

        raise ValueError(
            "Número sugerido da NF-e inválido."
        ) from erro

    return str(
        numero % 100000000
    ).zfill(
        8
    )


# ============================================================
# PREPARAR DADOS DA CHAVE DE ACESSO
# ============================================================
def _preparar_chave_acesso(
    rascunho
):

    emitente = rascunho.get(
        "emitente",
        {}
    )

    data_emissao = _resolver_data_emissao(
        rascunho
    )

    codigo_uf = _resolver_codigo_uf(
        rascunho
    )

    codigo_numerico = _resolver_codigo_numerico(
        rascunho
    )

    resultado = gerar_chave_acesso_nfe(
        codigo_uf=codigo_uf,
        data_emissao=data_emissao,
        cnpj=emitente.get(
            "cnpj"
        ),
        modelo=rascunho.get(
            "modelo"
        ),
        serie=rascunho.get(
            "serie"
        ),
        numero=rascunho.get(
            "numero_sugerido"
        ),
        tipo_emissao=1,
        codigo_numerico=codigo_numerico
    )

    resultado[
        "data_emissao"
    ] = data_emissao

    resultado[
        "dhEmi"
    ] = data_emissao.isoformat(
        timespec="seconds"
    )

    return resultado


# ============================================================
# VALIDAR PIS / COFINS DO ITEM
#
# Nesta etapa o gerador exige que o motor fiscal já tenha
# resolvido CST e alíquota. O gerador NÃO escolhe tributação.
# ============================================================
def _validar_pis_cofins_item(
    item,
    numero_item
):

    erros = []

    cst_pis = _texto(
        item.get(
            "cst_pis"
        )
    )

    cst_cofins = _texto(
        item.get(
            "cst_cofins"
        )
    )

    aliquota_pis = item.get(
        "aliquota_pis"
    )

    aliquota_cofins = item.get(
        "aliquota_cofins"
    )

    if not cst_pis:

        erros.append(
            (
                f"Item {numero_item}: "
                "CST PIS não informado pelo motor fiscal."
            )
        )

    if not cst_cofins:

        erros.append(
            (
                f"Item {numero_item}: "
                "CST COFINS não informado pelo motor fiscal."
            )
        )

    if aliquota_pis is None:

        erros.append(
            (
                f"Item {numero_item}: "
                "alíquota PIS não informada pelo motor fiscal."
            )
        )

    if aliquota_cofins is None:

        erros.append(
            (
                f"Item {numero_item}: "
                "alíquota COFINS não informada pelo motor fiscal."
            )
        )

    if (
        cst_pis
        and
        (
            len(
                cst_pis
            ) != 2
            or
            not cst_pis.isdigit()
        )
    ):

        erros.append(
            (
                f"Item {numero_item}: "
                "CST PIS inválido."
            )
        )

    if (
        cst_cofins
        and
        (
            len(
                cst_cofins
            ) != 2
            or
            not cst_cofins.isdigit()
        )
    ):

        erros.append(
            (
                f"Item {numero_item}: "
                "CST COFINS inválido."
            )
        )

    return erros


# ============================================================
# VALIDAR RASCUNHO
# ============================================================
def validar_rascunho_para_xml(
    rascunho
):

    erros = []

    if not isinstance(
        rascunho,
        dict
    ):

        return {
            "valido": False,
            "erros": [
                "Rascunho fiscal inválido."
            ]
        }

    if not rascunho.get(
        "sucesso"
    ):

        erros.append(
            "Rascunho fiscal não está aprovado."
        )

    if not rascunho.get(
        "pode_gerar_xml"
    ):

        erros.append(
            (
                "Rascunho fiscal não está liberado "
                "para geração de XML."
            )
        )

    if rascunho.get(
        "modelo"
    ) != 55:

        erros.append(
            (
                "Este gerador aceita somente "
                "NF-e modelo 55."
            )
        )

    emitente = rascunho.get(
        "emitente"
    )

    if not isinstance(
        emitente,
        dict
    ):

        erros.append(
            "Emitente não informado."
        )

    itens = rascunho.get(
        "itens",
        []
    )

    if not itens:

        erros.append(
            "Documento fiscal sem itens."
        )

    for indice, item in enumerate(
        itens,
        start=1
    ):

        numero_item = (
            item.get(
                "numero_item"
            )
            or
            indice
        )

        erros.extend(
            _validar_pis_cofins_item(
                item,
                numero_item
            )
        )

    return {
        "valido":
            len(
                erros
            ) == 0,

        "erros":
            erros
    }


# ============================================================
# MONTAR IDENTIFICAÇÃO
# ============================================================
def _montar_identificacao(
    inf_nfe,
    rascunho,
    dados_chave
):

    ide = SubElement(
        inf_nfe,
        "ide"
    )

    emitente = (
        rascunho.get(
            "emitente",
            {}
        )
    )

    _tag(
        ide,
        "cUF",
        dados_chave.get(
            "codigo_uf"
        )
    )

    _tag(
        ide,
        "cNF",
        dados_chave.get(
            "cNF"
        )
    )

    _tag(
        ide,
        "natOp",
        "VENDA"
    )

    _tag(
        ide,
        "mod",
        "55"
    )

    _tag(
        ide,
        "serie",
        rascunho.get(
            "serie"
        )
    )

    _tag(
        ide,
        "nNF",
        rascunho.get(
            "numero_sugerido"
        )
    )

    _tag(
        ide,
        "dhEmi",
        dados_chave.get(
            "dhEmi"
        )
    )

    _tag(
        ide,
        "tpNF",
        "1"
    )

    _tag(
        ide,
        "idDest",
        "1"
    )

    _tag(
        ide,
        "cMunFG",
        emitente.get(
            "codigo_municipio_ibge"
        )
    )

    _tag(
        ide,
        "tpImp",
        "1"
    )

    _tag(
        ide,
        "tpEmis",
        dados_chave.get(
            "tipo_emissao"
        )
    )

    _tag(
        ide,
        "cDV",
        dados_chave.get(
            "cDV"
        )
    )

    _tag(
        ide,
        "tpAmb",
        rascunho.get(
            "ambiente"
        )
    )

    _tag(
        ide,
        "finNFe",
        "1"
    )

    _tag(
        ide,
        "indFinal",
        "1"
    )

    _tag(
        ide,
        "indPres",
        "1"
    )

    _tag(
        ide,
        "procEmi",
        "0"
    )

    _tag(
        ide,
        "verProc",
        "ERP_VERDE_INFANCIA"
    )

    return ide


# ============================================================
# MONTAR EMITENTE
# ============================================================
def _montar_emitente(
    inf_nfe,
    rascunho
):

    dados = rascunho.get(
        "emitente",
        {}
    )

    emit = SubElement(
        inf_nfe,
        "emit"
    )

    _tag(
        emit,
        "CNPJ",
        dados.get(
            "cnpj"
        )
    )

    _tag(
        emit,
        "xNome",
        dados.get(
            "razao_social"
        )
    )

    _tag(
        emit,
        "xFant",
        dados.get(
            "nome_fantasia"
        )
    )

    ender_emit = SubElement(
        emit,
        "enderEmit"
    )

    _tag(
        ender_emit,
        "xLgr",
        dados.get(
            "logradouro"
        )
    )

    _tag(
        ender_emit,
        "nro",
        dados.get(
            "numero"
        )
    )

    _tag(
        ender_emit,
        "xCpl",
        dados.get(
            "complemento"
        )
    )

    _tag(
        ender_emit,
        "xBairro",
        dados.get(
            "bairro"
        )
    )

    _tag(
        ender_emit,
        "cMun",
        dados.get(
            "codigo_municipio_ibge"
        )
    )

    _tag(
        ender_emit,
        "xMun",
        dados.get(
            "cidade"
        )
    )

    _tag(
        ender_emit,
        "UF",
        dados.get(
            "uf"
        )
    )

    _tag(
        ender_emit,
        "CEP",
        dados.get(
            "cep"
        )
    )

    _tag(
        ender_emit,
        "cPais",
        dados.get(
            "codigo_pais"
        )
    )

    _tag(
        ender_emit,
        "xPais",
        dados.get(
            "pais"
        )
    )

    _tag(
        emit,
        "IE",
        dados.get(
            "inscricao_estadual"
        )
    )

    _tag(
        emit,
        "CRT",
        dados.get(
            "crt"
        )
    )

    return emit


# ============================================================
# MONTAR DESTINATÁRIO
# ============================================================
def _montar_destinatario(
    inf_nfe,
    rascunho
):

    resultado = rascunho.get(
        "destinatario",
        {}
    )

    dados = resultado.get(
        "dados"
    )

    if not dados:

        return None

    endereco = dados.get(
        "endereco",
        {}
    )

    if not isinstance(
        endereco,
        dict
    ):

        endereco = {}

    dest = SubElement(
        inf_nfe,
        "dest"
    )

    if dados.get(
        "cnpj"
    ):

        _tag(
            dest,
            "CNPJ",
            dados.get(
                "cnpj"
            )
        )

    elif dados.get(
        "cpf"
    ):

        _tag(
            dest,
            "CPF",
            dados.get(
                "cpf"
            )
        )

    ambiente = str(
        rascunho.get(
            "ambiente"
        )
    ).strip()

    if ambiente == "2":

        nome_destinatario = (
            XNOME_DESTINATARIO_HOMOLOGACAO
        )

    else:

        nome_destinatario = (
            dados.get(
                "nome"
            )
            or
            dados.get(
                "razao_social"
            )
        )

    _tag(
        dest,
        "xNome",
        nome_destinatario
    )

    ender_dest = SubElement(
        dest,
        "enderDest"
    )

    _tag(
        ender_dest,
        "xLgr",
        endereco.get(
            "logradouro"
        )
        or
        dados.get(
            "logradouro"
        )
    )

    _tag(
        ender_dest,
        "nro",
        endereco.get(
            "numero"
        )
        or
        dados.get(
            "numero"
        )
    )

    _tag(
        ender_dest,
        "xCpl",
        endereco.get(
            "complemento"
        )
        or
        dados.get(
            "complemento"
        )
    )

    _tag(
        ender_dest,
        "xBairro",
        endereco.get(
            "bairro"
        )
        or
        dados.get(
            "bairro"
        )
    )

    _tag(
        ender_dest,
        "cMun",
        endereco.get(
            "codigo_municipio_ibge"
        )
        or
        dados.get(
            "codigo_municipio_ibge"
        )
    )

    _tag(
        ender_dest,
        "xMun",
        endereco.get(
            "cidade"
        )
        or
        dados.get(
            "cidade"
        )
    )

    _tag(
        ender_dest,
        "UF",
        endereco.get(
            "uf"
        )
        or
        dados.get(
            "uf"
        )
    )

    _tag(
        ender_dest,
        "CEP",
        endereco.get(
            "cep"
        )
        or
        dados.get(
            "cep"
        )
    )

    _tag(
        ender_dest,
        "cPais",
        endereco.get(
            "codigo_pais"
        )
        or
        dados.get(
            "codigo_pais"
        )
    )

    _tag(
        ender_dest,
        "xPais",
        endereco.get(
            "pais"
        )
        or
        dados.get(
            "pais"
        )
    )

    _tag(
        dest,
        "indIEDest",
        dados.get(
            "indicador_ie"
        )
    )

    _tag(
        dest,
        "IE",
        dados.get(
            "inscricao_estadual"
        )
    )

    _tag(
        dest,
        "email",
        (
            dados.get(
                "email_fiscal"
            )
            or
            dados.get(
                "email"
            )
        )
    )

    return dest


# ============================================================
# MONTAR PIS
#
# CST 99:
# - usa PISOutr
# - para alíquota zero, utiliza a forma por quantidade zerada
#   compatível com a orientação histórica do Simples Nacional
# - para alíquota diferente de zero, utiliza base percentual
#
# Outros CSTs serão incorporados ao motor em etapa posterior.
# O gerador bloqueia CST ainda não implementado para não criar
# XML tributariamente ambíguo.
# ============================================================
def _montar_pis(
    imposto,
    item
):

    cst = _texto(
        item.get(
            "cst_pis"
        )
    )

    aliquota = _decimal(
        item.get(
            "aliquota_pis"
        ),
        Decimal("0")
    )

    base = _decimal(
        item.get(
            "subtotal"
        ),
        Decimal("0")
    )

    pis = SubElement(
        imposto,
        "PIS"
    )

    if cst == "99":

        pis_outr = SubElement(
            pis,
            "PISOutr"
        )

        _tag(
            pis_outr,
            "CST",
            cst
        )

        if aliquota == Decimal("0"):

            _tag(
                pis_outr,
                "qBCProd",
                "0.0000"
            )

            _tag(
                pis_outr,
                "vAliqProd",
                "0.0000"
            )

            _tag(
                pis_outr,
                "vPIS",
                "0.00"
            )

            return Decimal("0.00")

        valor_pis = _calcular_tributo_percentual(
            base,
            aliquota
        )

        _tag(
            pis_outr,
            "vBC",
            _formatar_valor(
                base
            )
        )

        _tag(
            pis_outr,
            "pPIS",
            _formatar_aliquota(
                aliquota
            )
        )

        _tag(
            pis_outr,
            "vPIS",
            _formatar_valor(
                valor_pis
            )
        )

        return valor_pis

    raise ValueError(
        (
            f"CST PIS {cst} ainda não está "
            "implementado no gerador XML."
        )
    )


# ============================================================
# MONTAR COFINS
# ============================================================
def _montar_cofins(
    imposto,
    item
):

    cst = _texto(
        item.get(
            "cst_cofins"
        )
    )

    aliquota = _decimal(
        item.get(
            "aliquota_cofins"
        ),
        Decimal("0")
    )

    base = _decimal(
        item.get(
            "subtotal"
        ),
        Decimal("0")
    )

    cofins = SubElement(
        imposto,
        "COFINS"
    )

    if cst == "99":

        cofins_outr = SubElement(
            cofins,
            "COFINSOutr"
        )

        _tag(
            cofins_outr,
            "CST",
            cst
        )

        if aliquota == Decimal("0"):

            _tag(
                cofins_outr,
                "qBCProd",
                "0.0000"
            )

            _tag(
                cofins_outr,
                "vAliqProd",
                "0.0000"
            )

            _tag(
                cofins_outr,
                "vCOFINS",
                "0.00"
            )

            return Decimal("0.00")

        valor_cofins = _calcular_tributo_percentual(
            base,
            aliquota
        )

        _tag(
            cofins_outr,
            "vBC",
            _formatar_valor(
                base
            )
        )

        _tag(
            cofins_outr,
            "pCOFINS",
            _formatar_aliquota(
                aliquota
            )
        )

        _tag(
            cofins_outr,
            "vCOFINS",
            _formatar_valor(
                valor_cofins
            )
        )

        return valor_cofins

    raise ValueError(
        (
            f"CST COFINS {cst} ainda não está "
            "implementado no gerador XML."
        )
    )
# ============================================================
# DISTRIBUIR DESCONTO ENTRE OS ITENS
#
# REGRA:
# soma(det/prod/vDesc) deve ser exatamente igual a
# total/ICMSTot/vDesc.
#
# O desconto é distribuído proporcionalmente ao subtotal.
# O último item absorve eventual diferença de arredondamento.
# ============================================================
def _distribuir_desconto_itens(
    itens,
    desconto_total
):

    itens = [
        dict(item)
        for item in (itens or [])
    ]

    if not itens:
        return itens

    desconto_total = _decimal(
        desconto_total,
        Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if desconto_total < Decimal("0.00"):

        raise ValueError(
            "Desconto total não pode ser negativo."
        )

    # --------------------------------------------------------
    # SEM DESCONTO
    # --------------------------------------------------------
    if desconto_total == Decimal("0.00"):

        for item in itens:

            item[
                "desconto_item"
            ] = Decimal("0.00")

        return itens

    # --------------------------------------------------------
    # SUBTOTAIS
    # --------------------------------------------------------
    subtotais = []

    for item in itens:

        subtotal = _decimal(
            item.get(
                "subtotal"
            ),
            Decimal("0.00")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        if subtotal < Decimal("0.00"):

            raise ValueError(
                "Subtotal de item não pode ser negativo."
            )

        subtotais.append(
            subtotal
        )

    soma_subtotais = sum(
        subtotais,
        Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if soma_subtotais <= Decimal("0.00"):

        raise ValueError(
            "Não é possível distribuir desconto "
            "quando o total dos itens é zero."
        )

    if desconto_total > soma_subtotais:

        raise ValueError(
            "Desconto total não pode ser maior "
            "que o valor total dos produtos."
        )

    # --------------------------------------------------------
    # DISTRIBUIÇÃO PROPORCIONAL
    # --------------------------------------------------------
    desconto_acumulado = Decimal("0.00")

    for indice, item in enumerate(
        itens
    ):

        ultimo_item = (
            indice
            ==
            len(itens) - 1
        )

        if ultimo_item:

            desconto_item = (
                desconto_total
                -
                desconto_acumulado
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

        else:

            desconto_item = (
                desconto_total
                *
                subtotais[indice]
                /
                soma_subtotais
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            desconto_acumulado += (
                desconto_item
            )

        if desconto_item < Decimal("0.00"):

            raise ValueError(
                "Distribuição do desconto gerou "
                "valor negativo."
            )

        if desconto_item > subtotais[indice]:

            raise ValueError(
                "Desconto do item não pode ser maior "
                "que o subtotal do próprio item."
            )

        item[
            "desconto_item"
        ] = desconto_item

    # --------------------------------------------------------
    # CONFERÊNCIA FINAL
    # --------------------------------------------------------
    soma_descontos = sum(
        (
            item.get(
                "desconto_item",
                Decimal("0.00")
            )
            for item in itens
        ),
        Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if soma_descontos != desconto_total:

        raise ValueError(
            "Falha na distribuição do desconto. "
            f"Esperado={desconto_total}; "
            f"itens={soma_descontos}."
        )

    return itens

# ============================================================
# MONTAR IBS / CBS DO ITEM
# Grupo criado somente quando ibs_cbs_calcular=True.
# ============================================================
def _montar_ibs_cbs_item(imposto, item):
    if not item.get("ibs_cbs_calcular"):
        return None

    cst = _texto(item.get("cst_ibs_cbs"))
    cclass = _texto(item.get("classificacao_tributaria"))
    if not cst or len(cst) != 3 or not cst.isdigit():
        raise ValueError("CST IBS/CBS inválido no item.")
    if not cclass or len(cclass) != 6 or not cclass.isdigit():
        raise ValueError("cClassTrib IBS/CBS inválido no item.")
    if cclass[:3] != cst:
        raise ValueError("cClassTrib incompatível com o CST IBS/CBS.")

    base = _decimal(item.get("base_calculo_ibs_cbs"), Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    puf = _decimal(item.get("aliquota_ibs_uf"), Decimal("0"))
    pmun = _decimal(item.get("aliquota_ibs_municipal"), Decimal("0"))
    pcbs = _decimal(item.get("aliquota_cbs"), Decimal("0"))
    vuf = _calcular_tributo_percentual(base, puf)
    vmun = _calcular_tributo_percentual(base, pmun)
    vibs = (vuf + vmun).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vcbs = _calcular_tributo_percentual(base, pcbs)

    # Valores já apurados pelo motor fiscal prevalecem quando informados.
    vibs = _decimal(item.get("valor_ibs"), vibs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vcbs = _decimal(item.get("valor_cbs"), vcbs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    ibscbs = SubElement(imposto, "IBSCBS")
    _tag(ibscbs, "CST", cst)
    _tag(ibscbs, "cClassTrib", cclass)
    g = SubElement(ibscbs, "gIBSCBS")
    _tag(g, "vBC", _formatar_valor(base))
    guf = SubElement(g, "gIBSUF")
    _tag(guf, "pIBSUF", _formatar_aliquota(puf))
    _tag(guf, "vIBSUF", _formatar_valor(vuf))
    gmun = SubElement(g, "gIBSMun")
    _tag(gmun, "pIBSMun", _formatar_aliquota(pmun))
    _tag(gmun, "vIBSMun", _formatar_valor(vmun))
    _tag(g, "vIBS", _formatar_valor(vibs))
    gcbs = SubElement(g, "gCBS")
    _tag(gcbs, "pCBS", _formatar_aliquota(pcbs))
    _tag(gcbs, "vCBS", _formatar_valor(vcbs))
    return {"vBCIBSCBS":base,"vIBSUF":vuf,"vIBSMun":vmun,"vIBS":vibs,"vCBS":vcbs}


# ============================================================
# MONTAR ITEM
# ============================================================
def _montar_item(
    inf_nfe,
    item
):

    det = SubElement(
        inf_nfe,
        "det",
        {
            "nItem":
                str(
                    item.get(
                        "numero_item"
                    )
                )
        }
    )

    prod = SubElement(
        det,
        "prod"
    )

    _tag(
        prod,
        "cProd",
        item.get(
            "produto_id"
        )
    )

    codigo_barras = _texto(
        item.get(
            "codigo_barras"
        )
    )

    _tag(
        prod,
        "cEAN",
        codigo_barras
        or
        "SEM GTIN"
    )

    _tag(
        prod,
        "xProd",
        item.get(
            "descricao"
        )
    )

    _tag(
        prod,
        "NCM",
        item.get(
            "ncm"
        )
    )

    _tag(
        prod,
        "CEST",
        item.get(
            "cest"
        )
    )

    _tag(
        prod,
        "CFOP",
        item.get(
            "cfop"
        )
    )

    _tag(
        prod,
        "uCom",
        "UN"
    )

    _tag(
        prod,
        "qCom",
        _formatar_quantidade(
            item.get(
                "quantidade"
            )
        )
    )

    _tag(
        prod,
        "vUnCom",
        _formatar_valor(
            item.get(
                "preco_unitario"
            )
        )
    )

    _tag(
        prod,
        "vProd",
        _formatar_valor(
            item.get(
                "subtotal"
            )
        )
    )

    _tag(
        prod,
        "cEANTrib",
        codigo_barras
        or
        "SEM GTIN"
    )

    _tag(
        prod,
        "uTrib",
        "UN"
    )

    _tag(
        prod,
        "qTrib",
        _formatar_quantidade(
            item.get(
                "quantidade"
            )
        )
    )

    _tag(
        prod,
        "vUnTrib",
        _formatar_valor(
            item.get(
                "preco_unitario"
            )
        )
    )

    # --------------------------------------------------------
    # DESCONTO DO ITEM
    #
    # A tag vDesc pertence ao grupo prod e deve aparecer
    # antes de indTot, respeitando a ordem do leiaute NF-e.
    # --------------------------------------------------------
    desconto_item = _decimal(
        item.get(
            "desconto_item"
        ),
        Decimal("0.00")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    if desconto_item > Decimal("0.00"):

        _tag(
            prod,
            "vDesc",
            _formatar_valor(
                desconto_item
            )
        )

    _tag(
        prod,
        "indTot",
        "1"
    )

    imposto = SubElement(
        det,
        "imposto"
    )

    # --------------------------------------------------------
    # ICMS
    # --------------------------------------------------------
    icms = SubElement(
        imposto,
        "ICMS"
    )

    icmssn102 = SubElement(
        icms,
        "ICMSSN102"
    )

    _tag(
        icmssn102,
        "orig",
        item.get(
            "origem_mercadoria"
        )
    )

    _tag(
        icmssn102,
        "CSOSN",
        item.get(
            "csosn"
        )
    )

    # --------------------------------------------------------
    # PIS
    # --------------------------------------------------------
    valor_pis = _montar_pis(
        imposto,
        item
    )

    # --------------------------------------------------------
    # COFINS
    # --------------------------------------------------------
    valor_cofins = _montar_cofins(
        imposto,
        item
    )

    resultado_ibs_cbs = _montar_ibs_cbs_item(
        imposto,
        item
    )

    return {
        "det":
            det,
        "valor_pis":
            valor_pis,
        "valor_cofins":
            valor_cofins,
        "ibs_cbs":
            resultado_ibs_cbs
    }


# ============================================================
# SOMAR PIS / COFINS DOS ITENS
# ============================================================
def _somar_tributos_itens(
    resultados_itens
):

    total_pis = Decimal(
        "0.00"
    )

    total_cofins = Decimal(
        "0.00"
    )

    for resultado in resultados_itens:

        total_pis += (
            _decimal(
                resultado.get(
                    "valor_pis"
                ),
                Decimal("0")
            )
        )

        total_cofins += (
            _decimal(
                resultado.get(
                    "valor_cofins"
                ),
                Decimal("0")
            )
        )

    return (
        total_pis.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        ),
        total_cofins.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
    )


# ============================================================
# SOMAR IBS / CBS DOS ITENS
# ============================================================
def _somar_ibs_cbs_itens(resultados_itens):
    totais = {k: Decimal("0.00") for k in ("vBCIBSCBS","vIBSUF","vIBSMun","vIBS","vCBS")}
    informar = False
    for resultado in resultados_itens:
        dados = resultado.get("ibs_cbs")
        if not dados:
            continue
        informar = True
        for chave in totais:
            totais[chave] += _decimal(dados.get(chave), Decimal("0"))
    for chave in totais:
        totais[chave] = totais[chave].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    totais["informar"] = informar
    return totais


# ============================================================
# MONTAR TOTAIS
# ============================================================
def _montar_totais(
    inf_nfe,
    rascunho,
    total_pis=Decimal("0.00"),
    total_cofins=Decimal("0.00"),
    totais_ibs_cbs=None
):

    total = SubElement(
        inf_nfe,
        "total"
    )

    icms_tot = SubElement(
        total,
        "ICMSTot"
    )

    dados = (
        rascunho.get(
            "totais",
            {}
        ).get(
            "dados",
            {}
        )
    )

    _tag(
        icms_tot,
        "vBC",
        "0.00"
    )

    _tag(
        icms_tot,
        "vICMS",
        "0.00"
    )

    _tag(
        icms_tot,
        "vICMSDeson",
        "0.00"
    )

    _tag(
        icms_tot,
        "vFCP",
        "0.00"
    )

    _tag(
        icms_tot,
        "vBCST",
        "0.00"
    )

    _tag(
        icms_tot,
        "vST",
        "0.00"
    )

    _tag(
        icms_tot,
        "vFCPST",
        "0.00"
    )

    _tag(
        icms_tot,
        "vFCPSTRet",
        "0.00"
    )

    _tag(
        icms_tot,
        "vProd",
        dados.get(
            "soma_itens"
        )
    )

    _tag(
        icms_tot,
        "vFrete",
        "0.00"
    )

    _tag(
        icms_tot,
        "vSeg",
        "0.00"
    )

    _tag(
        icms_tot,
        "vDesc",
        dados.get(
            "desconto"
        )
    )

    _tag(
        icms_tot,
        "vII",
        "0.00"
    )

    _tag(
        icms_tot,
        "vIPI",
        "0.00"
    )

    _tag(
        icms_tot,
        "vIPIDevol",
        "0.00"
    )

    _tag(
        icms_tot,
        "vPIS",
        _formatar_valor(
            total_pis
        )
    )

    _tag(
        icms_tot,
        "vCOFINS",
        _formatar_valor(
            total_cofins
        )
    )

    _tag(
        icms_tot,
        "vOutro",
        "0.00"
    )

    _tag(
        icms_tot,
        "vNF",
        dados.get(
            "valor_final"
        )
    )

    totais_ibs_cbs = totais_ibs_cbs or {}
    if totais_ibs_cbs.get("informar"):
        ibs_tot = SubElement(total, "IBSCBSTot")
        _tag(ibs_tot, "vBCIBSCBS", _formatar_valor(totais_ibs_cbs.get("vBCIBSCBS")))
        gibs = SubElement(ibs_tot, "gIBS")
        guf = SubElement(gibs, "gIBSUF")
        _tag(guf, "vDif", "0.00")
        _tag(guf, "vDevTrib", "0.00")
        _tag(guf, "vIBSUF", _formatar_valor(totais_ibs_cbs.get("vIBSUF")))
        gmun = SubElement(gibs, "gIBSMun")
        _tag(gmun, "vDif", "0.00")
        _tag(gmun, "vDevTrib", "0.00")
        _tag(gmun, "vIBSMun", _formatar_valor(totais_ibs_cbs.get("vIBSMun")))
        _tag(gibs, "vIBS", _formatar_valor(totais_ibs_cbs.get("vIBS")))
        _tag(gibs, "vCredPres", "0.00")
        _tag(gibs, "vCredPresCondSus", "0.00")
        gcbs = SubElement(ibs_tot, "gCBS")
        _tag(gcbs, "vDif", "0.00")
        _tag(gcbs, "vDevTrib", "0.00")
        _tag(gcbs, "vCBS", _formatar_valor(totais_ibs_cbs.get("vCBS")))
        _tag(gcbs, "vCredPres", "0.00")
        _tag(gcbs, "vCredPresCondSus", "0.00")

    return total


# ============================================================
# MONTAR TRANSPORTE
# ============================================================
def _montar_transporte(
    inf_nfe,
    rascunho
):

    transp = SubElement(
        inf_nfe,
        "transp"
    )

    modalidade_frete = _texto(
        rascunho.get(
            "mod_frete"
        )
    )

    if modalidade_frete is None:

        transporte = rascunho.get(
            "transporte",
            {}
        )

        if isinstance(
            transporte,
            dict
        ):

            modalidade_frete = _texto(
                transporte.get(
                    "mod_frete"
                )
            )

    if modalidade_frete is None:

        modalidade_frete = "9"

    _tag(
        transp,
        "modFrete",
        modalidade_frete
    )

    return transp


# ============================================================
# MONTAR PAGAMENTO
# ============================================================
def _montar_pagamento(
    inf_nfe,
    rascunho
):

    pag = SubElement(
        inf_nfe,
        "pag"
    )

    pagamento = (
        rascunho.get(
            "pagamento",
            {}
        ).get(
            "dados",
            {}
        )
    )

    det_pag = SubElement(
        pag,
        "detPag"
    )

    _tag(
        det_pag,
        "tPag",
        pagamento.get(
            "tPag"
        )
    )

    _tag(
        det_pag,
        "vPag",
        pagamento.get(
            "valor"
        )
    )

    return pag


# ============================================================
# GERAR XML NF-e
# ============================================================
def gerar_xml_nfe(
    rascunho
):

    validacao = validar_rascunho_para_xml(
        rascunho
    )

    if not validacao.get(
        "valido"
    ):

        return {
            "sucesso": False,
            "xml": None,
            "erros":
                validacao.get(
                    "erros",
                    []
                ),
            "avisos": []
        }

    try:

        dados_chave = _preparar_chave_acesso(
            rascunho
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml": None,
            "erros": [
                (
                    "Não foi possível gerar a chave "
                    f"de acesso da NF-e: {erro}"
                )
            ],
            "avisos": []
        }

    chave_acesso = dados_chave.get(
        "chave_acesso"
    )

    nfe = Element(
        "NFe",
        {
            "xmlns":
                NAMESPACE_NFE
        }
    )

    inf_nfe = SubElement(
        nfe,
        "infNFe",
        {
            "versao":
                VERSAO_NFE,

            "Id":
                (
                    "NFe"
                    +
                    chave_acesso
                )
        }
    )

    try:

        _montar_identificacao(
            inf_nfe,
            rascunho,
            dados_chave
        )

        _montar_emitente(
            inf_nfe,
            rascunho
        )

        _montar_destinatario(
            inf_nfe,
            rascunho
        )

        # ====================================================
        # DISTRIBUIR DESCONTO ENTRE OS ITENS
        # ====================================================
        dados_totais = (
            rascunho.get(
                "totais",
                {}
            ).get(
                "dados",
                {}
            )
        )

        itens_com_desconto = (
            _distribuir_desconto_itens(
                itens=rascunho.get(
                    "itens",
                    []
                ),
                desconto_total=dados_totais.get(
                    "desconto"
                )
            )
        )

        # ====================================================
        # MONTAR ITENS
        # ====================================================
        resultados_itens = []

        for item in itens_com_desconto:

            resultado_item = _montar_item(
                inf_nfe,
                item
            )

            resultados_itens.append(
                resultado_item
            )

        (
            total_pis,
            total_cofins
        ) = _somar_tributos_itens(
            resultados_itens
        )

        totais_ibs_cbs = _somar_ibs_cbs_itens(
            resultados_itens
        )

        _montar_totais(
            inf_nfe,
            rascunho,
            total_pis=total_pis,
            total_cofins=total_cofins,
            totais_ibs_cbs=totais_ibs_cbs
        )

        _montar_transporte(
            inf_nfe,
            rascunho
        )

        _montar_pagamento(
            inf_nfe,
            rascunho
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "xml": None,
            "chave_acesso":
                chave_acesso,
            "id_infnfe":
                (
                    "NFe"
                    +
                    chave_acesso
                ),
            "erros": [
                (
                    "Falha ao montar XML NF-e: "
                    f"{type(erro).__name__}: {erro}"
                )
            ],
            "avisos": []
        }

    xml_bytes = tostring(
        nfe,
        encoding="utf-8",
        xml_declaration=True
    )

    xml_texto = xml_bytes.decode(
        "utf-8"
    )

    return {
        "sucesso": True,

        "xml":
            xml_texto,

        "chave_acesso":
            chave_acesso,

        "id_infnfe":
            (
                "NFe"
                +
                chave_acesso
            ),

        "cNF":
            dados_chave.get(
                "cNF"
            ),

        "cDV":
            dados_chave.get(
                "cDV"
            ),

        "dhEmi":
            dados_chave.get(
                "dhEmi"
            ),

        "erros": [],

        "avisos": [
            (
                "XML estrutural gerado com grupos "
                "PIS e COFINS fornecidos pelo motor fiscal."
            ),
            (
                "XML ainda não possui assinatura digital."
            ),
            (
                "Nenhuma transmissão para SEFAZ foi realizada."
            ),
            (
                "O cNF ainda usa fallback temporário quando "
                "não é informado pelo rascunho."
            )
        ]
    }