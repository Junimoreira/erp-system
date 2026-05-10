from database.connection import conectar
import pandas as pd


# =========================================
# LISTAR
# =========================================
def listar_movimentacoes():

    conn = conectar()

    query = """
        SELECT
            id,
            descricao,
            valor,
            tipo,
            categoria,
            data_lancamento
        FROM financeiro
        ORDER BY id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# =========================================
# CADASTRAR
# =========================================
def cadastrar_movimentacao(
    descricao,
    valor,
    tipo,
    categoria,
    data_lancamento
):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        INSERT INTO financeiro
        (
            descricao,
            valor,
            tipo,
            categoria,
            data_lancamento
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        descricao,
        valor,
        tipo,
        categoria,
        data_lancamento
    ))

    conn.commit()

    cursor.close()
    conn.close()


# =========================================
# EXCLUIR
# =========================================
def excluir_movimentacao(id_mov):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        DELETE FROM financeiro
        WHERE id = %s
    """

    cursor.execute(query, (id_mov,))

    conn.commit()

    cursor.close()
    conn.close()


# =========================================
# ATUALIZAR
# =========================================
def atualizar_movimentacao(
    id_mov,
    descricao,
    valor,
    tipo,
    categoria,
    data_lancamento
):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        UPDATE financeiro
        SET
            descricao = %s,
            valor = %s,
            tipo = %s,
            categoria = %s,
            data_lancamento = %s
        WHERE id = %s
    """

    cursor.execute(query, (
        descricao,
        valor,
        tipo,
        categoria,
        data_lancamento,
        id_mov
    ))

    conn.commit()

    cursor.close()
    conn.close()