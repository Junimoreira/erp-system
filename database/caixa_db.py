import pandas as pd
from datetime import datetime

from database.connection import conectar


# ==================================================
# ABRIR CAIXA
# ==================================================
def abrir_caixa(usuario, saldo_inicial):

    conn = conectar()

    if conn is None:
        return False

    try:

        cursor = conn.cursor()

        # ==========================================
        # VERIFICA SE JÁ EXISTE CAIXA ABERTO
        # ==========================================
        cursor.execute("""
            SELECT id
            FROM caixa
            WHERE status = 'ABERTO'
            LIMIT 1
        """)

        if cursor.fetchone():

            print("Já existe caixa aberto.")

            return False

        # ==========================================
        # ABRIR CAIXA
        # ==========================================
        cursor.execute("""
            INSERT INTO caixa (
                usuario,
                data_abertura,
                saldo_inicial,
                entradas,
                saidas,
                saldo_final,
                saldo_real,
                diferenca,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario,
            datetime.now(),
            float(saldo_inicial),
            0,
            0,
            float(saldo_inicial),
            float(saldo_inicial),
            0,
            "ABERTO"
        ))

        conn.commit()

        return True

    except Exception as erro:

        print("Erro abrir_caixa:", erro)

        return False

    finally:

        conn.close()


# ==================================================
# VERIFICAR CAIXA ABERTO
# ==================================================
def verificar_caixa_aberto():

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM caixa
            WHERE status = 'ABERTO'
            ORDER BY id DESC
            LIMIT 1
        """)

        return cursor.fetchone()

    except Exception as erro:

        print("Erro verificar_caixa:", erro)

        return None

    finally:

        conn.close()


# ==================================================
# FECHAR CAIXA
# ==================================================
def fechar_caixa(id_caixa, saldo_real):

    conn = conectar()

    if conn is None:
        return False

    try:

        cursor = conn.cursor()

        # ==========================================
        # BUSCA SALDO FINAL
        # ==========================================
        cursor.execute("""
            SELECT saldo_final
            FROM caixa
            WHERE id = ?
        """, (id_caixa,))

        resultado = cursor.fetchone()

        if resultado is None:

            return False

        saldo_final = float(resultado[0])

        diferenca = float(saldo_real) - saldo_final

        # ==========================================
        # FECHAR CAIXA
        # ==========================================
        cursor.execute("""
            UPDATE caixa
            SET
                data_fechamento = ?,
                saldo_real = ?,
                diferenca = ?,
                status = ?
            WHERE id = ?
        """, (
            datetime.now(),
            float(saldo_real),
            float(diferenca),
            "FECHADO",
            id_caixa
        ))

        conn.commit()

        return True

    except Exception as erro:

        print("Erro fechar_caixa:", erro)

        return False

    finally:

        conn.close()


# ==================================================
# LISTAR HISTÓRICO CAIXA
# ==================================================
def listar_historico_caixa():

    conn = conectar()

    if conn is None:

        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                usuario,
                data_abertura,
                data_fechamento,
                saldo_inicial,
                entradas,
                saidas,
                saldo_final,
                saldo_real,
                diferenca,
                status
            FROM caixa
            ORDER BY id DESC
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        print("Erro listar_historico_caixa:", erro)

        return pd.DataFrame()

    finally:

        conn.close()