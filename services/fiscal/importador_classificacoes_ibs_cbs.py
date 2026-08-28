from datetime import datetime

from database.connection import conectar


# ============================================================
# IMPORTADOR DE CLASSIFICAÇÕES IBS / CBS
#
# RESPONSABILIDADE:
# - Receber registros extraídos de fonte oficial
# - Validar formato básico
# - Validar relação CST x cClassTrib
# - Inserir ou atualizar registros no banco
# - Preservar versão e fonte
# - Preservar vigência
# - Preservar compatibilidade com NF-e / NFC-e
#
# IMPORTANTE:
# - NÃO define tributação de produto
# - NÃO altera produtos
# - NÃO altera vendas
# - NÃO transmite documento fiscal
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
# NORMALIZAR BOOLEANO
# ============================================================
def _normalizar_booleano(
    valor
):

    if valor is None:
        return None

    if isinstance(
        valor,
        bool
    ):

        return valor

    if isinstance(
        valor,
        int
    ):

        if valor == 1:
            return True

        if valor == 0:
            return False

    texto = str(
        valor
    ).strip().upper()

    if texto in (
        "TRUE",
        "T",
        "1",
        "SIM",
        "S",
        "YES",
        "Y"
    ):

        return True

    if texto in (
        "FALSE",
        "F",
        "0",
        "NAO",
        "NÃO",
        "N",
        "NO"
    ):

        return False

    return None


# ============================================================
# VALIDAR REGISTRO
# ============================================================
def _validar_registro(
    registro
):

    erros = []

    cst = _normalizar(
        registro.get(
            "cst"
        )
    )

    cclass_trib = _normalizar(
        registro.get(
            "cclass_trib"
        )
    )

    # --------------------------------------------------------
    # CST
    # --------------------------------------------------------
    if (
        cst is None
        or
        not cst.isdigit()
        or
        len(
            cst
        ) != 3
    ):

        erros.append(
            "CST IBS/CBS inválido."
        )

    # --------------------------------------------------------
    # cClassTrib
    # --------------------------------------------------------
    if (
        cclass_trib is None
        or
        not cclass_trib.isdigit()
        or
        len(
            cclass_trib
        ) != 6
    ):

        erros.append(
            "cClassTrib inválido."
        )

    # --------------------------------------------------------
    # RELAÇÃO CST x cClassTrib
    # --------------------------------------------------------
    if (
        not erros
        and
        cclass_trib[:3] != cst
    ):

        erros.append(
            (
                "Os três primeiros dígitos do "
                "cClassTrib não correspondem ao CST."
            )
        )

    return {
        "valido":
            len(
                erros
            ) == 0,

        "cst":
            cst,

        "cclass_trib":
            cclass_trib,

        "erros":
            erros
    }


# ============================================================
# IMPORTAR CLASSIFICAÇÕES
# ============================================================
def importar_classificacoes(
    registros,
    versao_fonte,
    fonte
):

    # --------------------------------------------------------
    # VALIDAR REGISTROS RECEBIDOS
    # --------------------------------------------------------
    if not registros:

        return {
            "sucesso": False,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": [
                "Nenhum registro informado."
            ]
        }

    # --------------------------------------------------------
    # NORMALIZAR FONTE
    # --------------------------------------------------------
    versao_fonte = _normalizar(
        versao_fonte
    )

    fonte = _normalizar(
        fonte
    )

    if not versao_fonte:

        return {
            "sucesso": False,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": [
                "Versão da fonte não informada."
            ]
        }

    if not fonte:

        return {
            "sucesso": False,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": [
                "Fonte não informada."
            ]
        }

    # --------------------------------------------------------
    # CONECTAR
    # --------------------------------------------------------
    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "inseridos": 0,
            "atualizados": 0,
            "ignorados": 0,
            "erros": [
                "Não foi possível conectar ao banco."
            ]
        }

    inseridos = 0
    atualizados = 0
    ignorados = 0
    erros = []

    try:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # PERCORRER REGISTROS
        # ----------------------------------------------------
        for numero, registro in enumerate(
            registros,
            start=1
        ):

            validacao = _validar_registro(
                registro
            )

            if not validacao.get(
                "valido"
            ):

                ignorados += 1

                erros.append(
                    {
                        "registro":
                            numero,

                        "erros":
                            validacao.get(
                                "erros",
                                []
                            )
                    }
                )

                continue

            # ------------------------------------------------
            # DADOS PRINCIPAIS
            # ------------------------------------------------
            cst = validacao.get(
                "cst"
            )

            cclass_trib = validacao.get(
                "cclass_trib"
            )

            descricao = _normalizar(
                registro.get(
                    "descricao"
                )
            )

            # ------------------------------------------------
            # VIGÊNCIA
            # ------------------------------------------------
            data_inicio_vigencia = (
                registro.get(
                    "data_inicio_vigencia"
                )
            )

            data_fim_vigencia = (
                registro.get(
                    "data_fim_vigencia"
                )
            )

            # ------------------------------------------------
            # ATIVO
            # ------------------------------------------------
            ativo = _normalizar_booleano(
                registro.get(
                    "ativo",
                    True
                )
            )

            if ativo is None:

                ativo = True

            # ------------------------------------------------
            # MODELOS DE DOCUMENTO
            # ------------------------------------------------
            ind_nfe = _normalizar_booleano(
                registro.get(
                    "ind_nfe"
                )
            )

            ind_nfce = _normalizar_booleano(
                registro.get(
                    "ind_nfce"
                )
            )

            # ------------------------------------------------
            # LOCALIZAR REGISTRO EXISTENTE
            # ------------------------------------------------
            cursor.execute(
                """
                SELECT
                    id
                FROM classificacoes_ibs_cbs
                WHERE cst = %s
                  AND cclass_trib = %s
                  AND versao_fonte = %s
                LIMIT 1
                """,
                (
                    cst,
                    cclass_trib,
                    versao_fonte
                )
            )

            existente = cursor.fetchone()

            # =================================================
            # ATUALIZAR
            # =================================================
            if existente:

                cursor.execute(
                    """
                    UPDATE classificacoes_ibs_cbs
                    SET
                        descricao = %s,
                        fonte = %s,
                        data_inicio_vigencia = %s,
                        data_fim_vigencia = %s,
                        ativo = %s,
                        ind_nfe = %s,
                        ind_nfce = %s,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        descricao,
                        fonte,
                        data_inicio_vigencia,
                        data_fim_vigencia,
                        ativo,
                        ind_nfe,
                        ind_nfce,
                        existente[0]
                    )
                )

                atualizados += 1

            # =================================================
            # INSERIR
            # =================================================
            else:

                cursor.execute(
                    """
                    INSERT INTO classificacoes_ibs_cbs (
                        cst,
                        cclass_trib,
                        descricao,
                        versao_fonte,
                        fonte,
                        data_inicio_vigencia,
                        data_fim_vigencia,
                        ativo,
                        ind_nfe,
                        ind_nfce
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        cst,
                        cclass_trib,
                        descricao,
                        versao_fonte,
                        fonte,
                        data_inicio_vigencia,
                        data_fim_vigencia,
                        ativo,
                        ind_nfe,
                        ind_nfce
                    )
                )

                inseridos += 1

        # ----------------------------------------------------
        # COMMIT ÚNICO
        # ----------------------------------------------------
        conn.commit()

        return {
            "sucesso": True,

            "inseridos":
                inseridos,

            "atualizados":
                atualizados,

            "ignorados":
                ignorados,

            "total_processados":
                (
                    inseridos
                    +
                    atualizados
                    +
                    ignorados
                ),

            "erros":
                erros,

            "processado_em":
                datetime.now()
        }

    except Exception as erro:

        conn.rollback()

        return {
            "sucesso": False,

            "inseridos":
                inseridos,

            "atualizados":
                atualizados,

            "ignorados":
                ignorados,

            "total_processados":
                (
                    inseridos
                    +
                    atualizados
                    +
                    ignorados
                ),

            "erros": [
                str(
                    erro
                )
            ]
        }

    finally:

        conn.close()