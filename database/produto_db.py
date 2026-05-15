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

def cadastrar_produto(
    nome,
    preco,
    estoque
):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        INSERT INTO produtos
        (
            nome,
            preco,
            estoque
        )
        VALUES (%s, %s, %s)
    """

    cursor.execute(
        query,
        (
            nome,
            preco,
            estoque
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# EXCLUIR PRODUTO
# ==================================================

def excluir_produto(produto_id):

    conn = conectar()

    cursor = conn.cursor()

    try:

        # ==========================================
        # VERIFICA SE PRODUTO POSSUI VENDAS
        # ==========================================

        cursor.execute("""
            SELECT COUNT(*)
            FROM itens_venda
            WHERE produto_id = %s
        """, (produto_id,))

        total_vendas = cursor.fetchone()[0]

        # ==========================================
        # BLOQUEIA EXCLUSÃO
        # ==========================================

        if total_vendas > 0:

            return "possui_vendas"

        # ==========================================
        # EXCLUI PRODUTO
        # ==========================================

        cursor.execute("""
            DELETE FROM produtos
            WHERE id = %s
        """, (produto_id,))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao excluir produto:",
            erro
        )

        return False

    finally:

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