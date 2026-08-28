import re


# ============================================================
# SOMENTE NÚMEROS
# ============================================================
def somente_numeros(valor):

    if valor is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor)
    )


# ============================================================
# VALIDAR CPF
# ============================================================
def validar_cpf(cpf):

    numeros = somente_numeros(
        cpf
    )

    if len(numeros) != 11:
        return False

    # Bloqueia sequências repetidas
    if numeros == numeros[0] * 11:
        return False

    # --------------------------------------------------------
    # PRIMEIRO DÍGITO VERIFICADOR
    # --------------------------------------------------------
    soma = 0

    for indice in range(9):

        soma += (
            int(numeros[indice])
            *
            (10 - indice)
        )

    resto = soma % 11

    primeiro_digito = (
        0
        if resto < 2
        else
        11 - resto
    )

    if primeiro_digito != int(
        numeros[9]
    ):
        return False

    # --------------------------------------------------------
    # SEGUNDO DÍGITO VERIFICADOR
    # --------------------------------------------------------
    soma = 0

    for indice in range(10):

        soma += (
            int(numeros[indice])
            *
            (11 - indice)
        )

    resto = soma % 11

    segundo_digito = (
        0
        if resto < 2
        else
        11 - resto
    )

    if segundo_digito != int(
        numeros[10]
    ):
        return False

    return True