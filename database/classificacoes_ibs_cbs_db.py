from datetime import date

import pandas as pd

from database.connection import conectar


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
# NORMALIZAR DATA
# ============================================================
def _normalizar_data(
    valor
):

    if valor is None:
        return date.today()

    if isinstance(
        valor,
        date
    ):

        return valor

    try:

        return date.fromisoformat(
            str(
                valor
            ).strip()
        )

    except Exception:

        return None


# ============================================================
# LISTAR CLASSIFICAÇÕES ATIVAS
# ============================================================
def listar_classificacoes_ativas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                cst,
                cclass_trib,
                descricao,
                versao_fonte,
                fonte,
                data_inicio_vigencia,
                data_fim_vigencia,
                ativo,
                ind_nfe,
                ind_nfce,
                criado_em,
                atualizado_em
            FROM classificacoes_ibs_cbs
            WHERE ativo = TRUE
            ORDER BY
                cst,
                cclass_trib
        """

        return pd.read_sql(
            query,
            conn
        )

    except Exception as erro:

        print(
            "Erro ao listar classificações IBS/CBS:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# BUSCAR CLASSIFICAÇÃO PELO cClassTrib
# ============================================================
def buscar_por_cclass_trib(
    cclass_trib
):

    codigo = _normalizar(
        cclass_trib
    )

    if codigo is None:
        return None

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                cst,
                cclass_trib,
                descricao,
                versao_fonte,
                fonte,
                data_inicio_vigencia,
                data_fim_vigencia,
                ativo,
                ind_nfe,
                ind_nfce,
                criado_em,
                atualizado_em
            FROM classificacoes_ibs_cbs
            WHERE cclass_trib = %s
              AND ativo = TRUE
            ORDER BY
                data_inicio_vigencia DESC NULLS LAST,
                id DESC
            LIMIT 1
            """,
            (
                codigo,
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "cst",
            "cclass_trib",
            "descricao",
            "versao_fonte",
            "fonte",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "ativo",
            "ind_nfe",
            "ind_nfce",
            "criado_em",
            "atualizado_em"
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar cClassTrib:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# BUSCAR PAR CST + cClassTrib
# ============================================================
def buscar_classificacao(
    cst,
    cclass_trib
):

    cst = _normalizar(
        cst
    )

    cclass_trib = _normalizar(
        cclass_trib
    )

    if (
        cst is None
        or
        cclass_trib is None
    ):

        return None

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                cst,
                cclass_trib,
                descricao,
                versao_fonte,
                fonte,
                data_inicio_vigencia,
                data_fim_vigencia,
                ativo,
                ind_nfe,
                ind_nfce,
                criado_em,
                atualizado_em
            FROM classificacoes_ibs_cbs
            WHERE cst = %s
              AND cclass_trib = %s
              AND ativo = TRUE
            ORDER BY
                data_inicio_vigencia DESC NULLS LAST,
                id DESC
            LIMIT 1
            """,
            (
                cst,
                cclass_trib
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "cst",
            "cclass_trib",
            "descricao",
            "versao_fonte",
            "fonte",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "ativo",
            "ind_nfe",
            "ind_nfce",
            "criado_em",
            "atualizado_em"
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar classificação IBS/CBS:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# BUSCAR CLASSIFICAÇÃO OFICIAL VIGENTE
#
# Verifica:
# - CST
# - cClassTrib
# - ativo
# - data de início de vigência
# - data de fim de vigência
# ============================================================
def buscar_classificacao_vigente(
    cst,
    cclass_trib,
    data_referencia=None
):

    cst = _normalizar(
        cst
    )

    cclass_trib = _normalizar(
        cclass_trib
    )

    data_referencia = _normalizar_data(
        data_referencia
    )

    if (
        cst is None
        or
        cclass_trib is None
        or
        data_referencia is None
    ):

        return None

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                cst,
                cclass_trib,
                descricao,
                versao_fonte,
                fonte,
                data_inicio_vigencia,
                data_fim_vigencia,
                ativo,
                ind_nfe,
                ind_nfce,
                criado_em,
                atualizado_em
            FROM classificacoes_ibs_cbs
            WHERE cst = %s
              AND cclass_trib = %s
              AND ativo = TRUE

              AND (
                    data_inicio_vigencia IS NULL
                    OR
                    data_inicio_vigencia <= %s
                  )

              AND (
                    data_fim_vigencia IS NULL
                    OR
                    data_fim_vigencia >= %s
                  )

            ORDER BY
                data_inicio_vigencia DESC NULLS LAST,
                id DESC
            LIMIT 1
            """,
            (
                cst,
                cclass_trib,
                data_referencia,
                data_referencia
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "cst",
            "cclass_trib",
            "descricao",
            "versao_fonte",
            "fonte",
            "data_inicio_vigencia",
            "data_fim_vigencia",
            "ativo",
            "ind_nfe",
            "ind_nfce",
            "criado_em",
            "atualizado_em"
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar classificação IBS/CBS vigente:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# LISTAR CLASSIFICAÇÕES POR CST
# ============================================================
def listar_por_cst(
    cst
):

    codigo = _normalizar(
        cst
    )

    if codigo is None:
        return pd.DataFrame()

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
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
            FROM classificacoes_ibs_cbs
            WHERE cst = %s
              AND ativo = TRUE
            ORDER BY
                cclass_trib
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                codigo,
            )
        )

    except Exception as erro:

        print(
            "Erro ao listar classificações por CST:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# VERIFICAR SE PAR EXISTE
# ============================================================
def classificacao_existe(
    cst,
    cclass_trib
):

    registro = buscar_classificacao(
        cst=cst,
        cclass_trib=cclass_trib
    )

    return registro is not None


# ============================================================
# VERIFICAR SE PAR ESTÁ VIGENTE
# ============================================================
def classificacao_vigente(
    cst,
    cclass_trib,
    data_referencia=None
):

    registro = buscar_classificacao_vigente(
        cst=cst,
        cclass_trib=cclass_trib,
        data_referencia=data_referencia
    )

    return registro is not None


# ============================================================
# VERIFICAR COMPATIBILIDADE COM MODELO
#
# modelo:
# 55 = NF-e
# 65 = NFC-e
# ============================================================
def classificacao_permite_modelo(
    cst,
    cclass_trib,
    modelo,
    data_referencia=None
):

    registro = buscar_classificacao_vigente(
        cst=cst,
        cclass_trib=cclass_trib,
        data_referencia=data_referencia
    )

    if registro is None:
        return False

    if modelo == 55:

        return (
            registro.get(
                "ind_nfe"
            )
            is True
        )

    if modelo == 65:

        return (
            registro.get(
                "ind_nfce"
            )
            is True
        )

    return False


# ============================================================
# CONTAR CLASSIFICAÇÕES ATIVAS
# ============================================================
def contar_classificacoes_ativas():

    conn = conectar()

    if conn is None:
        return 0

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM classificacoes_ibs_cbs
            WHERE ativo = TRUE
            """
        )

        registro = cursor.fetchone()

        if registro is None:
            return 0

        return int(
            registro[0]
        )

    except Exception as erro:

        print(
            "Erro ao contar classificações IBS/CBS:",
            erro
        )

        return 0

    finally:

        conn.close()