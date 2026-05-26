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
            WHERE status = 'ABERTO'
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

        print(f"Erro abrir_caixa: {erro}")

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
            WHERE status = 'ABERTO'
            ORDER BY id DESC
            LIMIT 1
        """)

        return cursor.fetchone()

    except Exception as erro:

        print(f"Erro verificar_caixa: {erro}")

        return None

    finally:

        cursor.close()
        conn.close()


# ==================================================
# FECHAR CAIXA
# ==================================================
def fechar_caixa(id_caixa):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE caixa
            SET

                data_fechamento = %s,
                status = %s

            WHERE id = %s
        """, (

            datetime.now(),
            "FECHADO",
            id_caixa

        ))

        conn.commit()

        print("Caixa fechado com sucesso.")

        return True

    except Exception as erro:

        conn.rollback()

        print(f"Erro fechar_caixa: {erro}")

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

        print(f"Erro listar_historico_caixa: {erro}")

        return pd.DataFrame()

    finally:

        conn.close()