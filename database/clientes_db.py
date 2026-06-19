from database.connection import conectar
import pandas as pd


# ==================================================
# LISTAR CLIENTES
# ==================================================
def listar_clientes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                id,
                nome,
                telefone,
                email,
                cidade,
                data_nascimento
            FROM clientes
            ORDER BY id DESC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar clientes:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# CADASTRAR CLIENTE
# ==================================================
def cadastrar_cliente(
    nome,
    telefone,
    email,
    cidade,
    data_nascimento=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO clientes (
                nome,
                telefone,
                email,
                cidade,
                data_nascimento
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            nome,
            telefone,
            email,
            cidade,
            data_nascimento
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro cadastrar cliente:", erro)
        return False

    finally:
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
    cidade,
    data_nascimento=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE clientes
            SET
                nome = %s,
                telefone = %s,
                email = %s,
                cidade = %s,
                data_nascimento = %s
            WHERE id = %s
        """, (
            nome,
            telefone,
            email,
            cidade,
            data_nascimento,
            cliente_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro atualizar cliente:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CLIENTE
# ==================================================
def excluir_cliente(cliente_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM vendas
            WHERE cliente_id = %s
        """, (cliente_id,))

        total_vendas = cursor.fetchone()[0]

        if total_vendas > 0:
            return "possui_vendas"

        cursor.execute("""
            DELETE FROM clientes
            WHERE id = %s
        """, (cliente_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao excluir cliente:", erro)
        return False

    finally:
        cursor.close()
        conn.close()