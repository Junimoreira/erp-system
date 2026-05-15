from database.connection import conectar
import pandas as pd


# ==================================================
# LISTAR DESPESAS
# ==================================================

def listar_despesas():

    conn = conectar()

    query = """
        SELECT
            id,
            descricao,
            tipo,
            valor,
            vencimento,
            status,
            observacoes,
            criado_em
        FROM despesas
        ORDER BY vencimento ASC
    """

    df = pd.read_sql(
        query,
        conn
    )

    conn.close()

    return df


# ==================================================
# CADASTRAR DESPESA
# ==================================================

def cadastrar_despesa(
    descricao,
    tipo,
    valor,
    vencimento,
    observacoes
):

    conn = conectar()

    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO despesas (
                descricao,
                tipo,
                valor,
                vencimento,
                observacoes,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                'Pendente'
            )
        """, (
            descricao,
            tipo,
            valor,
            vencimento,
            observacoes
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao cadastrar despesa:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR DESPESA
# ==================================================

def atualizar_despesa(
    despesa_id,
    descricao,
    tipo,
    valor,
    vencimento,
    observacoes
):

    conn = conectar()

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE despesas
            SET
                descricao = %s,
                tipo = %s,
                valor = %s,
                vencimento = %s,
                observacoes = %s
            WHERE id = %s
        """, (
            descricao,
            tipo,
            valor,
            vencimento,
            observacoes,
            despesa_id
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao atualizar despesa:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR DESPESA
# ==================================================

def excluir_despesa(despesa_id):

    conn = conectar()

    cursor = conn.cursor()

    try:

        # ==========================================
        # VERIFICA STATUS
        # ==========================================

        cursor.execute("""
            SELECT status
            FROM despesas
            WHERE id = %s
        """, (despesa_id,))

        despesa = cursor.fetchone()

        if not despesa:

            return False

        status = despesa[0]

        # ==========================================
        # NÃO EXCLUI SE PAGA
        # ==========================================

        if status == "Pago":

            return "pago"

        # ==========================================
        # EXCLUI
        # ==========================================

        cursor.execute("""
            DELETE FROM despesas
            WHERE id = %s
        """, (despesa_id,))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao excluir despesa:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# PAGAR DESPESA
# ==================================================

def pagar_despesa(despesa_id):

    conn = conectar()

    cursor = conn.cursor()

    try:

        # ==========================================
        # BUSCAR DESPESA
        # ==========================================

        cursor.execute("""
            SELECT
                descricao,
                valor
            FROM despesas
            WHERE id = %s
        """, (despesa_id,))

        despesa = cursor.fetchone()

        if not despesa:

            return False

        descricao, valor = despesa

        # ==========================================
        # ATUALIZA STATUS
        # ==========================================

        cursor.execute("""
            UPDATE despesas
            SET status = 'Pago'
            WHERE id = %s
        """, (despesa_id,))

        # ==========================================
        # GERA MOVIMENTAÇÃO
        # ==========================================

        cursor.execute("""
            INSERT INTO movimentacoes (
                tipo,
                descricao,
                valor
            )
            VALUES (
                'saida',
                %s,
                %s
            )
        """, (
            f"Despesa: {descricao}",
            valor
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao pagar despesa:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()