import pandas as pd
from datetime import datetime
from database.connection import conectar


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
                saldo_final,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            usuario,
            datetime.now(),
            float(saldo_inicial),
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


def calcular_saldo_caixa(cursor, caixa_id):

    try:
        cursor.execute("""
            SELECT COALESCE(saldo_inicial, 0)
            FROM caixa
            WHERE id = %s
        """, (caixa_id,))

        resultado = cursor.fetchone()

        if not resultado:
            return 0.0

        saldo_inicial = float(resultado[0] or 0)

        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE
                        WHEN LOWER(tipo) = 'entrada'
                        THEN valor
                        ELSE 0
                    END
                ), 0) AS entradas,

                COALESCE(SUM(
                    CASE
                        WHEN LOWER(tipo) = 'saida'
                        THEN valor
                        ELSE 0
                    END
                ), 0) AS saidas
            FROM movimentacoes
            WHERE caixa_id = %s
        """, (caixa_id,))

        resumo = cursor.fetchone()

        entradas = float(resumo[0] or 0)
        saidas = float(resumo[1] or 0)

        return saldo_inicial + entradas - saidas

    except Exception as erro:
        print("Erro calcular_saldo_caixa:", erro)
        return 0.0


def fechar_caixa(caixa_id, valor_conferido, saldo_final=None):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        if saldo_final is None:
            saldo_final = calcular_saldo_caixa(cursor, caixa_id)

        diferenca = float(valor_conferido) - float(saldo_final)

        cursor.execute("""
            UPDATE caixa
            SET
                status = 'FECHADO',
                valor_conferido = %s,
                saldo_final = %s,
                diferenca = %s,
                data_fechamento = NOW()
            WHERE id = %s
        """, (
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


def saldo_caixa_atual(caixa_id):

    conn = conectar()
    if conn is None:
        return 0.0

    cursor = conn.cursor()

    try:
        return calcular_saldo_caixa(cursor, caixa_id)

    except Exception as erro:
        print("Erro saldo_caixa_atual:", erro)
        return 0.0

    finally:
        cursor.close()
        conn.close()