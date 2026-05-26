def pagar_conta(conta_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # Atualiza status da conta
        cursor.execute("""
            UPDATE contas_pagar
            SET 
                status = 'Pago',
                data_pagamento = NOW()
            WHERE id = %s
        """, (conta_id,))

        # Verifica se encontrou a conta
        if cursor.rowcount == 0:

            print("Conta não encontrada.")

            conn.rollback()

            return False

        conn.commit()

        print("Conta paga com sucesso.")

        return True

    except Exception as erro:

        conn.rollback()

        print(f"Erro ao pagar conta: {erro}")

        return False

    finally:

        cursor.close()
        conn.close()

def listar_contas():

    conn = conectar()

    if conn is None:
        return []

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                descricao,
                categoria,
                tipo,
                valor,
                vencimento,
                status,
                data_pagamento,
                observacoes
            FROM contas_pagar
            ORDER BY vencimento ASC
        """)

        dados = cursor.fetchall()

        return dados

    except Exception as erro:

        print(f"Erro ao listar contas: {erro}")

        return []

    finally:

        cursor.close()
        conn.close()

def excluir_conta(conta_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conn.commit()

        print("Conta excluída com sucesso.")

        return True

    except Exception as erro:

        conn.rollback()

        print(f"Erro ao excluir conta: {erro}")

        return False

    finally:

        cursor.close()
        conn.close()