import pandas as pd
from datetime import datetime
from database.connection import conectar


# ==================================================
# ABRIR CAIXA
# ==================================================
def abrir_caixa(usuario, saldo_inicial=0):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM caixa
            WHERE LOWER(status) = 'aberto'
            LIMIT 1
        """)

        if cursor.fetchone():
            print("Já existe caixa aberto.")
            return False

        cursor.execute("""
            INSERT INTO caixa (
                usuario,
                data_abertura,
                saldo_inicial,
                total_entradas,
                total_saidas,
                saldo_final,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            usuario,
            datetime.now(),
            float(saldo_inicial),
            0,
            0,
            float(saldo_inicial),
            "ABERTO"
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro abrir_caixa:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# VERIFICAR CAIXA ABERTO
# ==================================================
def verificar_caixa_aberto():

    conn = conectar()
    if conn is None:
        return None

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM caixa
            WHERE LOWER(status) = 'aberto'
            ORDER BY id DESC
            LIMIT 1
        """)

        return cursor.fetchone()

    except Exception as erro:
        print("Erro verificar_caixa:", erro)
        return None

    finally:
        cursor.close()
        conn.close()


# ==================================================
# OBTER ID DO CAIXA ABERTO
# ==================================================
def obter_caixa_aberto_id(conn_externa=None):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM caixa
            WHERE LOWER(status) = 'aberto'
            ORDER BY id DESC
            LIMIT 1
        """)

        resultado = cursor.fetchone()

        return resultado[0] if resultado else None

    except Exception as erro:
        print("Erro obter_caixa_aberto_id:", erro)
        return None

    finally:
        cursor.close()

        if conn_externa is None:
            conn.close()


# ==================================================
# CALCULAR RESUMO DO CAIXA
# ==================================================
def calcular_resumo_caixa(cursor, caixa_id):

    cursor.execute("""
        SELECT COALESCE(saldo_inicial, 0)
        FROM caixa
        WHERE id = %s
    """, (caixa_id,))

    resultado = cursor.fetchone()

    if not resultado:
        return {
            "saldo_inicial": 0,
            "entradas": 0,
            "saidas": 0,
            "saldo": 0
        }

    saldo_inicial = float(resultado[0] or 0)

    cursor.execute("""
        SELECT
            COALESCE(SUM(
                CASE
                    WHEN LOWER(tipo) = 'entrada'
                    THEN valor
                    ELSE 0
                END
            ), 0),

            COALESCE(SUM(
                CASE
                    WHEN LOWER(tipo) = 'saida'
                    THEN valor
                    ELSE 0
                END
            ), 0)
        FROM movimentacoes
        WHERE caixa_id = %s
          AND UPPER(COALESCE(meio, 'CAIXA')) = 'CAIXA'
    """, (caixa_id,))

    entradas, saidas = cursor.fetchone()

    entradas = float(entradas or 0)
    saidas = float(saidas or 0)

    return {
        "saldo_inicial": saldo_inicial,
        "entradas": entradas,
        "saidas": saidas,
        "saldo": saldo_inicial + entradas - saidas
    }


# ==================================================
# COMPATIBILIDADE
# ==================================================
def calcular_saldo_caixa(cursor, caixa_id):

    try:
        resumo = calcular_resumo_caixa(cursor, caixa_id)
        return resumo["saldo"]

    except Exception as erro:
        print("Erro calcular_saldo_caixa:", erro)
        return 0.0


# ==================================================
# FECHAR CAIXA
# ==================================================
def fechar_caixa(caixa_id, valor_conferido, saldo_final=None):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        resumo = calcular_resumo_caixa(cursor, caixa_id)

        total_entradas = resumo["entradas"]
        total_saidas = resumo["saidas"]

        if saldo_final is None:
            saldo_final = resumo["saldo"]

        diferenca = float(valor_conferido) - float(saldo_final)

        cursor.execute("""
            UPDATE caixa
            SET
                status = 'FECHADO',
                total_entradas = %s,
                total_saidas = %s,
                valor_conferido = %s,
                saldo_final = %s,
                diferenca = %s,
                data_fechamento = NOW()
            WHERE id = %s
        """, (
            total_entradas,
            total_saidas,
            float(valor_conferido),
            float(saldo_final),
            float(diferenca),
            caixa_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro fechar_caixa:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# HISTÓRICO DO CAIXA
# ==================================================
def listar_historico_caixa():

    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("""
            SELECT
                id,
                usuario,
                data_abertura,
                data_fechamento,
                saldo_inicial,
                total_entradas,
                total_saidas,
                status,
                valor_conferido,
                saldo_final,
                diferenca
            FROM caixa
            ORDER BY id DESC
        """, conn)

    except Exception as erro:
        print("Erro historico_caixa:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# SALDO DO CAIXA ATUAL
# ==================================================
def saldo_caixa_atual(caixa_id):

    conn = conectar()
    if conn is None:
        return 0.0

    cursor = conn.cursor()

    try:
        resumo = calcular_resumo_caixa(cursor, caixa_id)
        return resumo["saldo"]

    except Exception as erro:
        print("Erro saldo_caixa_atual:", erro)
        return 0.0

    finally:
        cursor.close()
        conn.close()


# ==================================================
# RESUMO DO CAIXA ATUAL
# ==================================================
def resumo_caixa_atual(caixa_id):

    conn = conectar()
    if conn is None:
        return {
            "saldo_inicial": 0,
            "entradas": 0,
            "saidas": 0,
            "saldo": 0
        }

    cursor = conn.cursor()

    try:
        return calcular_resumo_caixa(cursor, caixa_id)

    except Exception as erro:
        print("Erro resumo_caixa_atual:", erro)
        return {
            "saldo_inicial": 0,
            "entradas": 0,
            "saidas": 0,
            "saldo": 0
        }

    finally:
        cursor.close()
        conn.close()