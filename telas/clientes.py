from database.connection import conectar
import pandas as pd


# ==================================================
# LISTAR CLIENTES
# ==================================================

def listar_clientes():

    conn = conectar()

    query = """
        SELECT *
        FROM clientes
        ORDER BY id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# CADASTRAR CLIENTE
# ==================================================

def cadastrar_cliente(
    nome,
    telefone,
    email,
    cidade
):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        INSERT INTO clientes
        (
            nome,
            telefone,
            email,
            cidade
        )
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            nome,
            telefone,
            email,
            cidade
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# ATUALIZAR CLIENTE
# ==================================================

def atualizar_cliente(
    cliente_id,
    nome,
    telefone,
    email,
    cidade
):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        UPDATE clientes
        SET
            nome = %s,
            telefone = %s,
            email = %s,
            cidade = %s
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            nome,
            telefone,
            email,
            cidade,
            cliente_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# EXCLUIR CLIENTE
# ==================================================

def excluir_cliente(cliente_id):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        DELETE FROM clientes
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            cliente_id,
        )
    )

    conn.commit()

    cursor.close()
    conn.close()