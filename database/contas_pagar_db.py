from database.connection import conectar


def pagar_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ======================================
        # BUSCAR CONTA
        # ======================================
        cursor.execute("""
            SELECT descricao, valor
            FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        descricao, valor = conta

        # ======================================
        # MARCAR COMO PAGA
        # ======================================
        cursor.execute("""
            UPDATE contas_pagar
            SET status = 'Pago'
            WHERE id = %s
        """, (conta_id,))

        # ======================================
        # GERAR MOVIMENTAÇÃO (SAÍDA)
        # ======================================
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
        """, (descricao, valor))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao pagar conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()