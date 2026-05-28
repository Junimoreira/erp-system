import pandas as pd

from database.connection import conectar
from services.finance_service import processar_saida_financeira

def pagar_conta(conta_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT descricao, valor, categoria, status
            FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise ValueError("Conta não encontrada.")

        descricao = tratar_texto(conta[0])
        valor = float(conta[1])
        categoria = tratar_texto(conta[2])
        status = tratar_texto(conta[3]).lower()

        if status == "pago":
            raise ValueError("Conta já está paga.")

        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        # ==========================================
        # ATUALIZA CONTA
        # ==========================================
        cursor.execute("""
            UPDATE contas_pagar
            SET status = 'Pago',
                data_pagamento = NOW()
            WHERE id = %s
        """, (conta_id,))

        # ==========================================
        # REGISTRA MOVIMENTAÇÃO
        # ==========================================
        sucesso_mov = registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="saida",
            valor=valor,
            descricao=descricao,
            categoria=categoria if categoria else "despesa",
            origem="contas_pagar",
            data_movimentacao=datetime.now()
        )

        if not sucesso_mov:
            raise ValueError("Erro ao gerar movimentação.")

        # ==========================================
        # REGISTRA FLUXO CAIXA
        # ==========================================
        sucesso_fluxo = registrar_fluxo_caixa(
            tipo="saida",
            valor=valor,
            descricao=descricao,
            origem="contas_pagar"
        )

        if not sucesso_fluxo:
            raise ValueError("Erro ao registrar fluxo caixa.")

        # ✔ SÓ AQUI CONFIRMA TUDO
        conn.commit()

        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao pagar conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()

def listar_contas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT *
            FROM contas_pagar
            ORDER BY vencimento ASC
        """

        df = pd.read_sql(query, conn)
        return df

    except Exception as erro:
        print(f"Erro listar_contas: {erro}")
        return pd.DataFrame()

    finally:
        conn.close()


def excluir_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print(f"Erro excluir_conta: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()