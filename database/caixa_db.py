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

    cursor = conn.cursor()

    try:

        # ==========================================
        # VERIFICA SE EXISTE CAIXA ABERTO
        # ==========================================
        cursor.execute("""
            SELECT id
            FROM caixa
            WHERE LOWER(status) = 'aberto'
            LIMIT 1
        """)

        caixa_aberto = cursor.fetchone()

        if caixa_aberto:
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
                total_entradas,
                total_saidas,
                saldo_final,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
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

        print("Caixa aberto com sucesso.")
        return True

    except Exception as erro:

        conn.rollback()

        print(
            f"Erro abrir_caixa: {erro}"
        )

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

        caixa = cursor.fetchone()

        print("CAIXA ABERTO:", caixa)

        return caixa

    except Exception as erro:

        print(
            f"Erro verificar_caixa: {erro}"
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ==================================================
# FECHAR CAIXA
# ==================================================
def fechar_caixa(caixa_id, valor_conferido):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                saldo_inicial,
                total_entradas,
                total_saidas
            FROM caixa
            WHERE id = %s
        """, (caixa_id,))

        caixa = cursor.fetchone()

        if not caixa:
            return False

        saldo_inicial = float(caixa[0] or 0)
        entradas = float(caixa[1] or 0)
        saidas = float(caixa[2] or 0)

        saldo_final = (
            saldo_inicial +
            entradas -
            saidas
        )

        cursor.execute("""
            UPDATE caixa
            SET
                status = 'FECHADO',
                valor_conferido = %s,
                saldo_final = %s,
                data_fechamento = NOW()
            WHERE id = %s
        """, (
            float(valor_conferido),
            saldo_final,
            caixa_id
        ))

        conn.commit()

        print(
            f"Caixa {caixa_id} fechado."
        )

        return True

    except Exception as erro:

        conn.rollback()

        print(
            f"Erro fechar_caixa: {erro}"
        )

        return False

    finally:

        cursor.close()
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
                total_entradas,
                total_saidas,
                saldo_final,
                status
            FROM caixa
            ORDER BY id DESC
        """

        df = pd.read_sql(
            query,
            conn
        )

        return df

    except Exception as erro:

        print(
            f"Erro listar_historico_caixa: {erro}"
        )

        return pd.DataFrame()

    finally:

        conn.close()
