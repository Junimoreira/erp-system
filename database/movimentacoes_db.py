import pandas as pd
from database.connection import conectar


# ==================================================
# REGISTRAR MOVIMENTAÇÃO
# ==================================================
def registrar_movimentacao(
    tipo,
    valor,
    descricao,
    origem,
    data_movimentacao
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        query = """
            INSERT INTO movimentacoes (

                tipo,
                valor,
                descricao,
                origem,
                data_movimentacao

            )
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (

            tipo,
            valor,
            descricao,
            origem,
            data_movimentacao

        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao registrar movimentação:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR MOVIMENTAÇÕES
# ==================================================
def listar_movimentacoes():

    conn = conectar()

    query = """
        SELECT

            id,
            tipo,
            valor,
            descricao,
            origem,
            data_movimentacao

        FROM movimentacoes

        ORDER BY data_movimentacao DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# ATUALIZAR MOVIMENTAÇÃO
# ==================================================
def atualizar_movimentacao(
    id_movimentacao,
    tipo,
    valor,
    descricao,
    origem
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""

            UPDATE movimentacoes

            SET
                tipo = %s,
                valor = %s,
                descricao = %s,
                origem = %s

            WHERE id = %s

        """, (

            tipo,
            valor,
            descricao,
            origem,
            id_movimentacao

        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao atualizar movimentação:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR MOVIMENTAÇÃO
# ==================================================
def excluir_movimentacao(id_movimentacao):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""

            DELETE FROM movimentacoes

            WHERE id = %s

        """, (id_movimentacao,))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao excluir movimentação:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# RESUMO FINANCEIRO
# ==================================================
def resumo_movimentacoes():

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM movimentacoes

            WHERE tipo = 'entrada'

        """)

        entradas = float(cursor.fetchone()[0])

        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM movimentacoes

            WHERE tipo = 'saida'

        """)

        saidas = float(cursor.fetchone()[0])

        saldo = entradas - saidas

        return {

            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo

        }

    finally:

        cursor.close()
        conn.close()


# ==================================================
# RESUMO POR PERÍODO
# ==================================================
def resumo_por_periodo(data_inicio, data_fim):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM movimentacoes

            WHERE tipo = 'entrada'

            AND DATE(data_movimentacao)
            BETWEEN %s AND %s

        """, (

            data_inicio,
            data_fim

        ))

        entradas = float(cursor.fetchone()[0])

        cursor.execute("""

            SELECT COALESCE(SUM(valor), 0)

            FROM movimentacoes

            WHERE tipo = 'saida'

            AND DATE(data_movimentacao)
            BETWEEN %s AND %s

        """, (

            data_inicio,
            data_fim

        ))

        saidas = float(cursor.fetchone()[0])

        saldo = entradas - saidas

        return {

            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo

        }

    finally:

        cursor.close()
        conn.close()