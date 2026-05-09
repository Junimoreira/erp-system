from database.connection import conectar
import pandas as pd


# =====================================
# LISTAR PRODUTOS
# =====================================
def listar_produtos():

    conn = conectar()

    query = """
        SELECT
            id,
            nome,
            preco,
            estoque,
            criado_em
        FROM produtos
        ORDER BY id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# =====================================
# CADASTRAR PRODUTO
# =====================================
def cadastrar_produto(nome, preco, estoque):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        INSERT INTO produtos
        (nome, preco, estoque)
        VALUES (%s, %s, %s)
    """

    cursor.execute(query, (
        nome,
        preco,
        estoque
    ))

    conn.commit()

    cursor.close()
    conn.close()


# =====================================
# EXCLUIR PRODUTO
# =====================================
def excluir_produto(id_produto):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        DELETE FROM produtos
        WHERE id = %s
    """

    cursor.execute(query, (id_produto,))

    conn.commit()

    cursor.close()
    conn.close()


# =====================================
# ATUALIZAR PRODUTO
# =====================================
def atualizar_produto(id_produto, nome, preco, estoque):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        UPDATE produtos
        SET
            nome = %s,
            preco = %s,
            estoque = %s
        WHERE id = %s
    """

    cursor.execute(query, (
        nome,
        preco,
        estoque,
        id_produto
    ))

    conn.commit()

    cursor.close()
    conn.close()