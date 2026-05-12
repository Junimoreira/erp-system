from database.connection import conectar
import pandas as pd


# ==================================================
# LISTAR CONTAS
# ==================================================

def listar_contas():

    conn = conectar()

    query = """
        SELECT *
        FROM contas_bancarias
        ORDER BY id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


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

    cursor = conn.cursor()

    query = """
        INSERT INTO contas_bancarias
        (
            banco,
            agencia,
            conta,
            tipo_conta,
            saldo
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            banco,
            agencia,
            conta,
            tipo_conta,
            saldo
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# ATUALIZAR CONTA
# ==================================================

def atualizar_conta(
    conta_id,
    banco,
    agencia,
    conta,
    tipo_conta,
    saldo
):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        UPDATE contas_bancarias
        SET
            banco = %s,
            agencia = %s,
            conta = %s,
            tipo_conta = %s,
            saldo = %s
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            banco,
            agencia,
            conta,
            tipo_conta,
            saldo,
            conta_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# EXCLUIR CONTA
# ==================================================

def excluir_conta(conta_id):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        DELETE FROM contas_bancarias
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            conta_id,
        )
    )

    conn.commit()

    cursor.close()
    conn.close()