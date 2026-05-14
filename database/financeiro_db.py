import pandas as pd

from database.connection import conectar


# ==================================================
# LISTAR CONTAS A RECEBER
# ==================================================

def listar_contas_receber():

    conn = conectar()

    query = """
        SELECT

            cr.id,

            c.nome AS cliente,

            cr.descricao,

            cr.valor,

            cr.vencimento,

            cr.status

        FROM contas_receber cr

        LEFT JOIN clientes c
            ON cr.cliente_id = c.id

        ORDER BY cr.vencimento
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# RECEBER CONTA
# ==================================================

def receber_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==========================================
        # BUSCAR CONTA
        # ==========================================

        query_busca = """
            SELECT

                valor,
                descricao

            FROM contas_receber

            WHERE id = %s
        """

        cursor.execute(
            query_busca,
            (conta_id,)
        )

        conta = cursor.fetchone()

        valor = conta[0]
        descricao = conta[1]

        # ==========================================
        # ATUALIZAR STATUS
        # ==========================================

        query_update = """
            UPDATE contas_receber
            SET status = 'Pago'
            WHERE id = %s
        """

        cursor.execute(
            query_update,
            (conta_id,)
        )

        # ==========================================
        # LANÇAR NO FLUXO CAIXA
        # ==========================================

        query_fluxo = """
            INSERT INTO fluxo_caixa (

                tipo,
                descricao,
                valor,
                origem

            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query_fluxo,
            (
                "Entrada",
                descricao,
                valor,
                "Recebimento"
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao receber conta:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()