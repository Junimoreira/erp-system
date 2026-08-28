from database.connection import conectar


# ============================================================
# CONVERTER REGISTRO EM DICT
# ============================================================
def _registro_para_dict(
    registro
):

    if registro is None:
        return None

    colunas = [
        "id",
        "nome",
        "tipo_operacao",
        "finalidade",
        "uf_origem",
        "uf_destino",
        "interestadual",
        "cfop_origem",
        "cfop_destino",
        "ncm_prefixo",
        "cest",
        "cst_origem",
        "csosn_destino",
        "cst_destino",
        "cst_ibs_cbs",
        "classificacao_tributaria",
        "prioridade",
        "confianca",
        "requer_revisao",
        "observacao"
    ]

    return dict(
        zip(
            colunas,
            registro
        )
    )


# ============================================================
# CARREGAR TODAS AS REGRAS FISCAIS ATIVAS
# ============================================================
def carregar_regras_fiscais_ativas():

    conn = conectar()

    if conn is None:
        return []

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                tipo_operacao,
                finalidade,
                uf_origem,
                uf_destino,
                interestadual,
                cfop_origem,
                cfop_destino,
                ncm_prefixo,
                cest,
                cst_origem,
                csosn_destino,
                cst_destino,
                cst_ibs_cbs,
                classificacao_tributaria,
                prioridade,
                confianca,
                requer_revisao,
                observacao
            FROM regras_fiscais
            WHERE ativo = TRUE
            ORDER BY
                prioridade ASC,
                id ASC
            """
        )

        registros = (
            cursor.fetchall()
        )

        return [
            _registro_para_dict(
                registro
            )
            for registro in registros
        ]

    except Exception as erro:

        print(
            "Erro ao carregar regras fiscais:",
            erro
        )

        return []

    finally:

        conn.close()


# ============================================================
# BUSCAR REGRA FISCAL
# CONSULTA DIRETA AO BANCO
#
# Mantida para consultas isoladas.
# ============================================================
def buscar_regra_fiscal(
    tipo_operacao,
    finalidade,
    cfop_origem,
    interestadual,
    ncm=None,
    cest=None
):

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                tipo_operacao,
                finalidade,
                uf_origem,
                uf_destino,
                interestadual,
                cfop_origem,
                cfop_destino,
                ncm_prefixo,
                cest,
                cst_origem,
                csosn_destino,
                cst_destino,
                cst_ibs_cbs,
                classificacao_tributaria,
                prioridade,
                confianca,
                requer_revisao,
                observacao
            FROM regras_fiscais
            WHERE ativo = TRUE
              AND tipo_operacao = %s
              AND finalidade = %s
              AND cfop_origem = %s
              AND interestadual = %s

              AND (
                    uf_origem IS NULL
                    OR uf_origem = ''
                  )

              AND (
                    uf_destino IS NULL
                    OR uf_destino = ''
                  )

              AND (
                    ncm_prefixo IS NULL
                    OR ncm_prefixo = ''
                    OR %s LIKE ncm_prefixo || '%%'
                  )

              AND (
                    cest IS NULL
                    OR cest = ''
                    OR cest = %s
                  )

            ORDER BY

                CASE
                    WHEN cest IS NOT NULL
                         AND cest <> ''
                    THEN 1
                    ELSE 2
                END,

                CASE
                    WHEN ncm_prefixo IS NOT NULL
                         AND ncm_prefixo <> ''
                    THEN 1
                    ELSE 2
                END,

                prioridade ASC,

                id ASC

            LIMIT 1
            """,
            (
                tipo_operacao,
                finalidade,
                cfop_origem,
                interestadual,
                ncm,
                cest
            )
        )

        registro = (
            cursor.fetchone()
        )

        return _registro_para_dict(
            registro
        )

    except Exception as erro:

        print(
            "Erro ao buscar regra fiscal:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# LISTAR REGRAS FISCAIS
# ============================================================
def listar_regras_fiscais():

    conn = conectar()

    if conn is None:
        return []

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                tipo_operacao,
                finalidade,
                interestadual,
                cfop_origem,
                cfop_destino,
                prioridade,
                confianca,
                requer_revisao,
                ativo
            FROM regras_fiscais
            ORDER BY
                prioridade ASC,
                id ASC
            """
        )

        return cursor.fetchall()

    except Exception as erro:

        print(
            "Erro ao listar regras fiscais:",
            erro
        )

        return []

    finally:

        conn.close()