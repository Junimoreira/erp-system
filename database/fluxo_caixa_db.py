import pandas as pd
from datetime import datetime

from database.connection import conectar


# ==================================================
# TRATAMENTO TEXTO
# ==================================================
def tratar_texto(valor):

    if valor is None:
        return ""

    return str(valor).strip()


# ==================================================
# REGISTRAR FLUXO DE CAIXA
# ==================================================
def registrar_fluxo_caixa(
    tipo,
    valor,
    descricao,
    origem,
    categoria_id=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        tipo = tratar_texto(tipo).lower()

        descricao = tratar_texto(descricao)

        origem = tratar_texto(origem)

        valor = float(valor)

        if valor <= 0:

            raise ValueError(
                "Valor inválido."
            )

        query = """
            INSERT INTO fluxo_caixa (

                tipo,
                valor,
                descricao,
                origem,
                categoria_id,
                data_lancamento

            )
            VALUES (

                %s,
                %s,
                %s,
                %s,
                %s,
                %s

            )
        """

        cursor.execute(query, (

            tipo,
            valor,
            descricao,
            origem,
            categoria_id,
            datetime.now()

        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao registrar fluxo caixa:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR FLUXO CAIXA
# ==================================================
def listar_fluxo_caixa():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT

                id,
                tipo,
                valor,
                descricao,
                origem,
                categoria_id,
                data_lancamento

            FROM fluxo_caixa

            ORDER BY data_lancamento DESC
        """

        df = pd.read_sql(
            query,
            conn
        )

        if df.empty:
            return pd.DataFrame()

        return df.fillna("")

    except Exception as erro:

        print(
            "Erro listar fluxo caixa:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# LISTAR FLUXO POR PERÍODO
# ==================================================
def listar_fluxo_por_periodo(
    data_inicio,
    data_fim
):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT

                id,
                tipo,
                valor,
                descricao,
                origem,
                categoria_id,
                data_lancamento

            FROM fluxo_caixa

            WHERE DATE(data_lancamento)
            BETWEEN %s AND %s

            ORDER BY data_lancamento DESC
        """

        df = pd.read_sql(
            query,
            conn,
            params=(
                data_inicio,
                data_fim
            )
        )

        if df.empty:
            return pd.DataFrame()

        return df.fillna("")

    except Exception as erro:

        print(
            "Erro listar fluxo período:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# RESUMO FLUXO CAIXA
# ==================================================
def resumo_fluxo_caixa():

    conn = conectar()

    if conn is None:

        return {

            "entradas": 0,
            "saidas": 0,
            "saldo": 0

        }

    cursor = conn.cursor()

    try:

        # ==========================================
        # ENTRADAS
        # ==========================================
        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM fluxo_caixa

            WHERE LOWER(tipo) = 'entrada'

        """)

        entradas = float(
            cursor.fetchone()[0]
        )

        # ==========================================
        # SAÍDAS
        # ==========================================
        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM fluxo_caixa

            WHERE LOWER(tipo) = 'saida'

        """)

        saidas = float(
            cursor.fetchone()[0]
        )

        saldo = entradas - saidas

        return {

            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo

        }

    except Exception as erro:

        print(
            "Erro resumo fluxo caixa:",
            erro
        )

        return {

            "entradas": 0,
            "saidas": 0,
            "saldo": 0

        }

    finally:

        cursor.close()
        conn.close()


# ==================================================
# RESUMO FLUXO POR PERÍODO
# ==================================================
def resumo_fluxo_periodo(
    data_inicio,
    data_fim
):

    conn = conectar()

    if conn is None:

        return {

            "entradas": 0,
            "saidas": 0,
            "saldo": 0

        }

    cursor = conn.cursor()

    try:

        # ==========================================
        # ENTRADAS
        # ==========================================
        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM fluxo_caixa

            WHERE LOWER(tipo) = 'entrada'

            AND DATE(data_lancamento)
            BETWEEN %s AND %s

        """, (

            data_inicio,
            data_fim

        ))

        entradas = float(
            cursor.fetchone()[0]
        )

        # ==========================================
        # SAÍDAS
        # ==========================================
        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM fluxo_caixa

            WHERE LOWER(tipo) = 'saida'

            AND DATE(data_lancamento)
            BETWEEN %s AND %s

        """, (

            data_inicio,
            data_fim

        ))

        saidas = float(
            cursor.fetchone()[0]
        )

        saldo = entradas - saidas

        return {

            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo

        }

    except Exception as erro:

        print(
            "Erro resumo período:",
            erro
        )

        return {

            "entradas": 0,
            "saidas": 0,
            "saldo": 0

        }

    finally:

        cursor.close()
        conn.close()