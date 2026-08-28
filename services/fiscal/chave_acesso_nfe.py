from datetime import datetime


# ============================================================
# CHAVE DE ACESSO NF-e
#
# RESPONSABILIDADE:
# - Normalizar os componentes da chave
# - Montar os 43 dígitos base
# - Calcular cDV pelo módulo 11
# - Gerar a chave final de 44 dígitos
#
# IMPORTANTE:
# - NÃO altera banco
# - NÃO consome numeração
# - NÃO gera XML
# - NÃO assina XML
# - NÃO transmite para SEFAZ
# ============================================================


# ============================================================
# SOMENTE NÚMEROS
# ============================================================
def _somente_numeros(
    valor
):

    if valor is None:
        return ""

    return "".join(
        caractere
        for caractere in str(
            valor
        )
        if caractere.isdigit()
    )


# ============================================================
# NORMALIZAR CAMPO NUMÉRICO
# ============================================================
def _normalizar_numerico(
    valor,
    tamanho,
    nome
):

    numeros = _somente_numeros(
        valor
    )

    if not numeros:

        raise ValueError(
            f"{nome} não informado."
        )

    if len(
        numeros
    ) > tamanho:

        raise ValueError(
            (
                f"{nome} possui mais de "
                f"{tamanho} dígitos."
            )
        )

    return numeros.zfill(
        tamanho
    )


# ============================================================
# NORMALIZAR DATA DE EMISSÃO
# ============================================================
def _normalizar_data_emissao(
    data_emissao
):

    if data_emissao is None:

        data_emissao = datetime.now()

    if isinstance(
        data_emissao,
        datetime
    ):

        return data_emissao

    try:

        return datetime.fromisoformat(
            str(
                data_emissao
            )
        )

    except Exception as erro:

        raise ValueError(
            "Data de emissão inválida."
        ) from erro


# ============================================================
# CALCULAR DÍGITO VERIFICADOR
#
# Módulo 11
#
# Pesos:
# 2 a 9, da direita para a esquerda.
#
# Se o resultado for 10 ou 11:
# DV = 0
# ============================================================
def calcular_dv_chave_acesso(
    chave_43
):

    chave = _somente_numeros(
        chave_43
    )

    if len(
        chave
    ) != 43:

        raise ValueError(
            (
                "A base da chave de acesso deve "
                "possuir exatamente 43 dígitos."
            )
        )

    peso = 2
    soma = 0

    for caractere in reversed(
        chave
    ):

        soma += (
            int(
                caractere
            )
            *
            peso
        )

        peso += 1

        if peso > 9:
            peso = 2

    resto = soma % 11

    dv = 11 - resto

    if dv >= 10:
        dv = 0

    return dv


# ============================================================
# GERAR CHAVE DE ACESSO
# ============================================================
def gerar_chave_acesso_nfe(
    codigo_uf,
    data_emissao,
    cnpj,
    modelo,
    serie,
    numero,
    tipo_emissao,
    codigo_numerico
):

    data_emissao = _normalizar_data_emissao(
        data_emissao
    )

    # --------------------------------------------------------
    # AAMM
    # --------------------------------------------------------
    aamm = data_emissao.strftime(
        "%y%m"
    )

    # --------------------------------------------------------
    # NORMALIZAÇÃO
    # --------------------------------------------------------
    codigo_uf = _normalizar_numerico(
        codigo_uf,
        2,
        "Código da UF"
    )

    cnpj = _normalizar_numerico(
        cnpj,
        14,
        "CNPJ"
    )

    modelo = _normalizar_numerico(
        modelo,
        2,
        "Modelo"
    )

    serie = _normalizar_numerico(
        serie,
        3,
        "Série"
    )

    numero = _normalizar_numerico(
        numero,
        9,
        "Número da NF-e"
    )

    tipo_emissao = _normalizar_numerico(
        tipo_emissao,
        1,
        "Tipo de emissão"
    )

    codigo_numerico = _normalizar_numerico(
        codigo_numerico,
        8,
        "Código numérico"
    )

    # --------------------------------------------------------
    # BASE DE 43 DÍGITOS
    # --------------------------------------------------------
    chave_43 = (
        codigo_uf
        +
        aamm
        +
        cnpj
        +
        modelo
        +
        serie
        +
        numero
        +
        tipo_emissao
        +
        codigo_numerico
    )

    if len(
        chave_43
    ) != 43:

        raise ValueError(
            (
                "Erro interno na montagem da chave: "
                f"foram gerados {len(chave_43)} dígitos."
            )
        )

    # --------------------------------------------------------
    # DÍGITO VERIFICADOR
    # --------------------------------------------------------
    dv = calcular_dv_chave_acesso(
        chave_43
    )

    chave_44 = (
        chave_43
        +
        str(
            dv
        )
    )

    return {
        "sucesso": True,

        "chave_acesso":
            chave_44,

        "chave_base":
            chave_43,

        "cDV":
            str(
                dv
            ),

        "cNF":
            codigo_numerico,

        "codigo_uf":
            codigo_uf,

        "aamm":
            aamm,

        "cnpj":
            cnpj,

        "modelo":
            modelo,

        "serie":
            serie,

        "numero":
            numero,

        "tipo_emissao":
            tipo_emissao
    }