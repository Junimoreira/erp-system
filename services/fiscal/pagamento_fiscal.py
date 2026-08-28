from decimal import Decimal, InvalidOperation


# ============================================================
# PAGAMENTO FISCAL
#
# RESPONSABILIDADE:
# - Receber a forma de pagamento utilizada no ERP
# - Converter para o código fiscal tPag
# - Validar o valor pago
# - Informar se serão necessários dados adicionais
#
# IMPORTANTE:
# - NÃO gera XML
# - NÃO transmite para SEFAZ
# - NÃO altera vendas
# - NÃO altera financeiro
# ============================================================


# ============================================================
# TABELA INTERNA DE MEIOS DE PAGAMENTO
#
# Códigos baseados na Tabela de Meios de Pagamento
# do Portal Nacional da NF-e.
# ============================================================
MEIOS_PAGAMENTO = {

    "DINHEIRO": {
        "tPag": "01",
        "descricao": "Dinheiro",
        "exige_dados_transacao": False
    },

    "CARTAO_CREDITO": {
        "tPag": "03",
        "descricao": "Cartão de Crédito",
        "exige_dados_transacao": True
    },

    "CARTAO_DEBITO": {
        "tPag": "04",
        "descricao": "Cartão de Débito",
        "exige_dados_transacao": True
    },

    "BOLETO": {
        "tPag": "15",
        "descricao": "Boleto Bancário",
        "exige_dados_transacao": False
    },

    "PIX": {
        "tPag": "17",
        "descricao": "Pagamento Instantâneo (PIX)",
        "exige_dados_transacao": True
    },

    "TRANSFERENCIA": {
        "tPag": "18",
        "descricao": "Transferência Bancária",
        "exige_dados_transacao": False
    }
}


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar(
    valor
):

    if valor is None:
        return ""

    texto = str(
        valor
    ).strip().upper()

    texto = (
        texto
        .replace("Á", "A")
        .replace("À", "A")
        .replace("Ã", "A")
        .replace("Â", "A")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ô", "O")
        .replace("Õ", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
    )

    return texto


# ============================================================
# NORMALIZAR VALOR
# ============================================================
def _normalizar_valor(
    valor
):

    if valor is None:
        return None

    try:

        return Decimal(
            str(
                valor
            )
        ).quantize(
            Decimal("0.01")
        )

    except (
        InvalidOperation,
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# IDENTIFICAR FORMA DO ERP
# ============================================================
def identificar_meio_pagamento(
    forma_pagamento
):

    forma = _normalizar(
        forma_pagamento
    )

    # --------------------------------------------------------
    # DINHEIRO
    # --------------------------------------------------------
    if forma in (
        "DINHEIRO",
        "ESPECIE"
    ):

        return "DINHEIRO"

    # --------------------------------------------------------
    # PIX
    # --------------------------------------------------------
    if forma in (
        "PIX",
        "PAGAMENTO PIX"
    ):

        return "PIX"

    # --------------------------------------------------------
    # CARTÃO DE DÉBITO
    # --------------------------------------------------------
    if forma in (
        "CARTAO DEBITO",
        "CARTAO DE DEBITO",
        "DEBITO",
        "CARTAO DEBITO"
    ):

        return "CARTAO_DEBITO"

    # --------------------------------------------------------
    # CARTÃO DE CRÉDITO
    # --------------------------------------------------------
    if forma in (
        "CARTAO CREDITO",
        "CARTAO DE CREDITO",
        "CREDITO"
    ):

        return "CARTAO_CREDITO"

    # --------------------------------------------------------
    # TRANSFERÊNCIA
    # --------------------------------------------------------
    if forma in (
        "TRANSFERENCIA",
        "TRANSFERENCIA BANCARIA",
        "TED",
        "DOC"
    ):

        return "TRANSFERENCIA"

    # --------------------------------------------------------
    # BOLETO
    # --------------------------------------------------------
    if forma in (
        "BOLETO",
        "BOLETO BANCARIO"
    ):

        return "BOLETO"

    return None


# ============================================================
# MONTAR PAGAMENTO FISCAL
# ============================================================
def montar_pagamento_fiscal(
    forma_pagamento,
    valor_pago,
    autorizacao_cartao=None
):

    erros = []
    avisos = []

    meio = identificar_meio_pagamento(
        forma_pagamento
    )

    if meio is None:

        return {
            "sucesso": False,
            "pagamento": None,
            "erros": [
                (
                    "Forma de pagamento não mapeada "
                    "para o padrão fiscal."
                )
            ],
            "avisos": []
        }

    configuracao = MEIOS_PAGAMENTO.get(
        meio
    )

    valor = _normalizar_valor(
        valor_pago
    )

    if valor is None:

        erros.append(
            "Valor do pagamento inválido."
        )

    elif valor <= 0:

        erros.append(
            "Valor do pagamento deve ser maior que zero."
        )

    # --------------------------------------------------------
    # DADOS DE TRANSAÇÃO
    #
    # Cartão e PIX podem exigir informações adicionais
    # no XML final. Nesta etapa apenas sinalizamos.
    # --------------------------------------------------------
    exige_dados_transacao = configuracao.get(
        "exige_dados_transacao"
    )

    if exige_dados_transacao:

        if meio in (
            "CARTAO_CREDITO",
            "CARTAO_DEBITO"
        ):

            if not autorizacao_cartao:

                avisos.append(
                    (
                        "Pagamento com cartão identificado. "
                        "Dados da transação/adquirente deverão "
                        "ser tratados antes da transmissão."
                    )
                )

        elif meio == "PIX":

            avisos.append(
                (
                    "Pagamento PIX identificado. "
                    "Os dados da transação deverão ser "
                    "avaliados antes da transmissão."
                )
            )

    pagamento = {
        "meio_erp":
            forma_pagamento,

        "tipo_interno":
            meio,

        "tPag":
            configuracao.get(
                "tPag"
            ),

        "descricao":
            configuracao.get(
                "descricao"
            ),

        "valor":
            valor,

        "exige_dados_transacao":
            exige_dados_transacao,

        "autorizacao_cartao":
            autorizacao_cartao
    }

    return {
        "sucesso":
            len(
                erros
            ) == 0,

        "pagamento":
            pagamento,

        "erros":
            erros,

        "avisos":
            avisos
    }