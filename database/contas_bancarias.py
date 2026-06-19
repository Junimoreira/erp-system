import pandas as pd
from database.connection import conectar


# ==================================================
# LISTAR CONTAS
# ==================================================
def listar_contas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                banco,
                agencia,
                conta,
                tipo_conta,
                saldo
            FROM contas_bancarias
            ORDER BY banco
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        print("Erro ao listar contas:", erro)

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# CADASTRAR CONTA
# ==================================================
def cadastrar_conta(
    banco,
    agencia,
    conta,
    tipo_conta,
    saldo
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO contas_bancarias
            (
                banco,
                agencia,
                conta,
                tipo_conta,
                saldo
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            banco,
            agencia,
            conta,
            tipo_conta,
            float(saldo)
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro cadastrar conta:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CONTA
# ==================================================
def atualizar_conta(
    id,
    banco,
    agencia,
    conta,
    tipo_conta,
    saldo
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE contas_bancarias
            SET
                banco=%s,
                agencia=%s,
                conta=%s,
                tipo_conta=%s,
                saldo=%s
            WHERE id=%s
        """, (
            banco,
            agencia,
            conta,
            tipo_conta,
            float(saldo),
            int(id)
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro atualizar conta:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CONTA
# ==================================================
def excluir_conta(id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM contas_bancarias
            WHERE id=%s
            """,
            (
                int(id),
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro excluir conta:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ADICIONAR SALDO
# ==================================================
def adicionar_saldo(
    conta_id,
    valor
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE contas_bancarias
            SET saldo = COALESCE(saldo,0) + %s
            WHERE id = %s
        """, (
            float(valor),
            int(conta_id)
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro adicionar saldo:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()

# ==================================================
# REMOVER / DEBITAR SALDO
# ==================================================
def remover_saldo(
    conta_id,
    valor,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE contas_bancarias
            SET saldo = COALESCE(saldo, 0) - %s
            WHERE id = %s
        """, (
            float(valor),
            int(conta_id)
        ))

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro remover saldo:", erro)
        return False

    finally:
        cursor.close()

        if conn_externa is None:
            conn.close()