from datetime import date

from database.classificacoes_ibs_cbs_db import (
    buscar_classificacao,
    buscar_classificacao_vigente
)


# ============================================================
# CLASSIFICAÇÃO IBS / CBS
#
# RESPONSABILIDADE:
# - Normalizar CST IBS/CBS
# - Normalizar cClassTrib
# - Validar formato
# - Validar relação CST x cClassTrib
# - Consultar tabela oficial carregada no banco
# - Validar vigência
# - Validar compatibilidade com NF-e 55 / NFC-e 65
#
# IMPORTANTE:
# - NÃO define automaticamente CST
# - NÃO define automaticamente cClassTrib
# - NÃO altera produto
# - NÃO altera banco
# - NÃO gera XML
# ============================================================


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar(
    valor
):

    if valor is None:
        return None

    texto = str(
        valor
    ).strip()

    if texto.upper() in (
        "",
        "NAN",
        "NONE",
        "NULL",
        "<NA>"
    ):

        return None

    return texto


# ============================================================
# SOMENTE NÚMEROS
# ============================================================
def _somente_numeros(
    valor
):

    texto = _normalizar(
        valor
    )

    if texto is None:
        return None

    if not texto.isdigit():
        return None

    return texto


# ============================================================
# VALIDAR CST IBS/CBS
# ============================================================
def validar_cst_ibs_cbs(
    cst
):

    erros = []

    codigo = _somente_numeros(
        cst
    )

    if codigo is None:

        return {
            "sucesso": False,
            "valido": False,
            "codigo": None,
            "erros": [
                "CST IBS/CBS não informado ou inválido."
            ],
            "avisos": []
        }

    if len(
        codigo
    ) != 3:

        erros.append(
            (
                "CST IBS/CBS deve possuir "
                "exatamente 3 dígitos."
            )
        )

    return {
        "sucesso":
            len(
                erros
            ) == 0,

        "valido":
            len(
                erros
            ) == 0,

        "codigo":
            codigo,

        "erros":
            erros,

        "avisos": []
    }


# ============================================================
# VALIDAR cClassTrib
# ============================================================
def validar_cclass_trib(
    classificacao
):

    erros = []

    codigo = _somente_numeros(
        classificacao
    )

    if codigo is None:

        return {
            "sucesso": False,
            "valido": False,
            "codigo": None,
            "erros": [
                (
                    "Classificação tributária IBS/CBS "
                    "não informada ou inválida."
                )
            ],
            "avisos": []
        }

    if len(
        codigo
    ) != 6:

        erros.append(
            (
                "cClassTrib deve possuir "
                "exatamente 6 dígitos."
            )
        )

    return {
        "sucesso":
            len(
                erros
            ) == 0,

        "valido":
            len(
                erros
            ) == 0,

        "codigo":
            codigo,

        "erros":
            erros,

        "avisos": []
    }


# ============================================================
# VALIDAR MODELO
# ============================================================
def _validar_modelo(
    modelo
):

    if modelo is None:

        return {
            "sucesso": True,
            "valido": True,
            "modelo": None,
            "erros": []
        }

    try:

        modelo = int(
            modelo
        )

    except Exception:

        return {
            "sucesso": False,
            "valido": False,
            "modelo": None,
            "erros": [
                "Modelo fiscal inválido."
            ]
        }

    if modelo not in (
        55,
        65
    ):

        return {
            "sucesso": False,
            "valido": False,
            "modelo": modelo,
            "erros": [
                "Modelo fiscal inválido. Use 55 ou 65."
            ]
        }

    return {
        "sucesso": True,
        "valido": True,
        "modelo": modelo,
        "erros": []
    }


# ============================================================
# VALIDAR RELAÇÃO ESTRUTURAL
# ============================================================
def _validar_relacao_cst_cclass(
    cst,
    cclass_trib
):

    if (
        cst is None
        or
        cclass_trib is None
    ):

        return False

    return (
        cclass_trib[:3]
        ==
        cst
    )


# ============================================================
# VALIDAR PAR USANDO TABELA EM MEMÓRIA
#
# Mantida para compatibilidade com testes anteriores.
# ============================================================
def validar_classificacao_ibs_cbs(
    cst,
    classificacao,
    tabela_classificacao=None
):

    erros = []
    avisos = []

    resultado_cst = validar_cst_ibs_cbs(
        cst
    )

    resultado_classificacao = (
        validar_cclass_trib(
            classificacao
        )
    )

    if not resultado_cst.get(
        "valido"
    ):

        erros.extend(
            resultado_cst.get(
                "erros",
                []
            )
        )

    if not resultado_classificacao.get(
        "valido"
    ):

        erros.extend(
            resultado_classificacao.get(
                "erros",
                []
            )
        )

    if erros:

        return {
            "sucesso": False,
            "valido": False,
            "cst":
                resultado_cst.get(
                    "codigo"
                ),
            "cclass_trib":
                resultado_classificacao.get(
                    "codigo"
                ),
            "descricao":
                None,
            "erros":
                erros,
            "avisos":
                avisos
        }

    cst_normalizado = resultado_cst.get(
        "codigo"
    )

    cclass_normalizado = (
        resultado_classificacao.get(
            "codigo"
        )
    )

    if not _validar_relacao_cst_cclass(
        cst_normalizado,
        cclass_normalizado
    ):

        return {
            "sucesso": False,
            "valido": False,
            "validado_na_tabela": False,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                None,
            "erros": [
                (
                    "Os três primeiros dígitos do "
                    "cClassTrib não correspondem ao CST."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # SEM TABELA EM MEMÓRIA
    # --------------------------------------------------------
    if tabela_classificacao is None:

        avisos.append(
            (
                "Formato de CST IBS/CBS e cClassTrib válido, "
                "mas esta função não realizou consulta ao banco."
            )
        )

        return {
            "sucesso": True,
            "valido": True,
            "validado_na_tabela": False,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                None,
            "erros": [],
            "avisos":
                avisos
        }

    registro = tabela_classificacao.get(
        cclass_normalizado
    )

    if registro is None:

        return {
            "sucesso": False,
            "valido": False,
            "validado_na_tabela": True,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                None,
            "erros": [
                (
                    "cClassTrib não encontrado na "
                    "tabela carregada."
                )
            ],
            "avisos": []
        }

    cst_tabela = _normalizar(
        registro.get(
            "cst"
        )
    )

    if cst_tabela != cst_normalizado:

        return {
            "sucesso": False,
            "valido": False,
            "validado_na_tabela": True,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                registro.get(
                    "descricao"
                ),
            "erros": [
                (
                    "CST IBS/CBS não corresponde ao "
                    "cClassTrib informado."
                )
            ],
            "avisos": []
        }

    return {
        "sucesso": True,
        "valido": True,
        "validado_na_tabela": True,
        "cst":
            cst_normalizado,
        "cclass_trib":
            cclass_normalizado,
        "descricao":
            registro.get(
                "descricao"
            ),
        "erros": [],
        "avisos": []
    }


# ============================================================
# VALIDAR CLASSIFICAÇÃO CONTRA O BANCO OFICIAL LOCAL
#
# modelo:
# - None -> não valida modelo
# - 55   -> valida NF-e
# - 65   -> valida NFC-e
# ============================================================
def validar_classificacao_oficial_ibs_cbs(
    cst,
    classificacao,
    data_referencia=None,
    modelo=None
):

    erros = []
    avisos = []

    # --------------------------------------------------------
    # FORMATO CST
    # --------------------------------------------------------
    resultado_cst = validar_cst_ibs_cbs(
        cst
    )

    # --------------------------------------------------------
    # FORMATO cClassTrib
    # --------------------------------------------------------
    resultado_classificacao = validar_cclass_trib(
        classificacao
    )

    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------
    resultado_modelo = _validar_modelo(
        modelo
    )

    if not resultado_cst.get(
        "valido"
    ):

        erros.extend(
            resultado_cst.get(
                "erros",
                []
            )
        )

    if not resultado_classificacao.get(
        "valido"
    ):

        erros.extend(
            resultado_classificacao.get(
                "erros",
                []
            )
        )

    if not resultado_modelo.get(
        "valido"
    ):

        erros.extend(
            resultado_modelo.get(
                "erros",
                []
            )
        )

    cst_normalizado = resultado_cst.get(
        "codigo"
    )

    cclass_normalizado = resultado_classificacao.get(
        "codigo"
    )

    modelo_normalizado = resultado_modelo.get(
        "modelo"
    )

    # --------------------------------------------------------
    # ERRO DE FORMATO / MODELO
    # --------------------------------------------------------
    if erros:

        return {
            "sucesso": False,
            "valido": False,
            "existe_na_tabela": False,
            "vigente": False,
            "permitido_modelo": False,
            "modelo":
                modelo_normalizado,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                None,
            "ind_nfe":
                None,
            "ind_nfce":
                None,
            "fonte":
                None,
            "versao_fonte":
                None,
            "data_referencia":
                data_referencia,
            "erros":
                erros,
            "avisos":
                avisos
        }

    # --------------------------------------------------------
    # RELAÇÃO CST x cClassTrib
    # --------------------------------------------------------
    if not _validar_relacao_cst_cclass(
        cst_normalizado,
        cclass_normalizado
    ):

        return {
            "sucesso": False,
            "valido": False,
            "existe_na_tabela": False,
            "vigente": False,
            "permitido_modelo": False,
            "modelo":
                modelo_normalizado,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                None,
            "ind_nfe":
                None,
            "ind_nfce":
                None,
            "fonte":
                None,
            "versao_fonte":
                None,
            "data_referencia":
                data_referencia,
            "erros": [
                (
                    "Os três primeiros dígitos do "
                    "cClassTrib não correspondem ao CST."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # VERIFICAR EXISTÊNCIA
    # --------------------------------------------------------
    registro = buscar_classificacao(
        cst=cst_normalizado,
        cclass_trib=cclass_normalizado
    )

    if registro is None:

        return {
            "sucesso": False,
            "valido": False,
            "existe_na_tabela": False,
            "vigente": False,
            "permitido_modelo": False,
            "modelo":
                modelo_normalizado,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                None,
            "ind_nfe":
                None,
            "ind_nfce":
                None,
            "fonte":
                None,
            "versao_fonte":
                None,
            "data_referencia":
                data_referencia,
            "erros": [
                (
                    "Combinação CST IBS/CBS + cClassTrib "
                    "não encontrada na tabela oficial "
                    "carregada no ERP."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # DATA DE REFERÊNCIA
    # --------------------------------------------------------
    if data_referencia is None:

        data_referencia = date.today()

    # --------------------------------------------------------
    # VERIFICAR VIGÊNCIA
    # --------------------------------------------------------
    registro_vigente = buscar_classificacao_vigente(
        cst=cst_normalizado,
        cclass_trib=cclass_normalizado,
        data_referencia=data_referencia
    )

    if registro_vigente is None:

        return {
            "sucesso": False,
            "valido": False,
            "existe_na_tabela": True,
            "vigente": False,
            "permitido_modelo": False,
            "modelo":
                modelo_normalizado,
            "cst":
                cst_normalizado,
            "cclass_trib":
                cclass_normalizado,
            "descricao":
                registro.get(
                    "descricao"
                ),
            "ind_nfe":
                registro.get(
                    "ind_nfe"
                ),
            "ind_nfce":
                registro.get(
                    "ind_nfce"
                ),
            "fonte":
                registro.get(
                    "fonte"
                ),
            "versao_fonte":
                registro.get(
                    "versao_fonte"
                ),
            "data_inicio_vigencia":
                registro.get(
                    "data_inicio_vigencia"
                ),
            "data_fim_vigencia":
                registro.get(
                    "data_fim_vigencia"
                ),
            "data_referencia":
                data_referencia,
            "erros": [
                (
                    "A classificação IBS/CBS existe, "
                    "mas não está vigente na data informada."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # VALIDAR MODELO
    # --------------------------------------------------------
    permitido_modelo = True

    if modelo_normalizado == 55:

        permitido_modelo = (
            registro_vigente.get(
                "ind_nfe"
            )
            is True
        )

        if not permitido_modelo:

            erros.append(
                (
                    "A classificação IBS/CBS informada "
                    "não é permitida para NF-e modelo 55."
                )
            )

    elif modelo_normalizado == 65:

        permitido_modelo = (
            registro_vigente.get(
                "ind_nfce"
            )
            is True
        )

        if not permitido_modelo:

            erros.append(
                (
                    "A classificação IBS/CBS informada "
                    "não é permitida para NFC-e modelo 65."
                )
            )

    # --------------------------------------------------------
    # RESULTADO FINAL
    # --------------------------------------------------------
    valido = (
        len(
            erros
        ) == 0
    )

    return {
        "sucesso":
            valido,

        "valido":
            valido,

        "existe_na_tabela":
            True,

        "vigente":
            True,

        "validado_na_tabela":
            True,

        "permitido_modelo":
            permitido_modelo,

        "modelo":
            modelo_normalizado,

        "cst":
            cst_normalizado,

        "cclass_trib":
            cclass_normalizado,

        "descricao":
            registro_vigente.get(
                "descricao"
            ),

        "ind_nfe":
            registro_vigente.get(
                "ind_nfe"
            ),

        "ind_nfce":
            registro_vigente.get(
                "ind_nfce"
            ),

        "fonte":
            registro_vigente.get(
                "fonte"
            ),

        "versao_fonte":
            registro_vigente.get(
                "versao_fonte"
            ),

        "data_inicio_vigencia":
            registro_vigente.get(
                "data_inicio_vigencia"
            ),

        "data_fim_vigencia":
            registro_vigente.get(
                "data_fim_vigencia"
            ),

        "data_referencia":
            data_referencia,

        "erros":
            erros,

        "avisos":
            avisos
    }