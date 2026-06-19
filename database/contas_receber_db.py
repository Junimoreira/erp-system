from datetime import datetime
import pandas as pd

from database.connection import conectar
from database.finance_engine import registrar_movimentacao_financeira


def listar_contas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                cr.id,
                cr.cliente_id,
                COALESCE(c.nome, cr.cliente, 'Sem cliente') AS cliente,
                cr.descricao,
                cr.valor,
                cr.vencimento,
                cr.status,
                cr.observacoes,
                cr.criado_em,
                cr.data_recebimento,
                cr.forma_pagamento,
                cr.caixa_id,
                cr.origem,
                cr.conta_bancaria_id
            FROM contas_receber cr
            LEFT JOIN clientes c ON c.id = cr.cliente_id
            ORDER BY cr.vencimento ASC, cr.id ASC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar_contas_receber:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


def cadastrar_conta(
    descricao,
    valor,
    vencimento,
    cliente_id=None,
    cliente=None,
    observacoes=None,
    forma_pagamento=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO contas_receber (
                cliente_id,
                cliente,
                descricao,
                valor,
                vencimento,
                status,
                observacoes,
                forma_pagamento,
                criado_em
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cliente_id,
            cliente,
            descricao,
            float(valor),
            vencimento,
            "PENDENTE",
            observacoes,
            forma_pagamento,
            datetime.now()
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro cadastrar_conta_receber:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


def atualizar_conta(
    conta_id,
    descricao,
    valor,
    vencimento,
    cliente_id=None,
    cliente=None,
    status="PENDENTE",
    observacoes=None,
    forma_pagamento=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE contas_receber
            SET cliente_id = %s,
                cliente = %s,
                descricao = %s,
                valor = %s,
                vencimento = %s,
                status = %s,
                observacoes = %s,
                forma_pagamento = %s
            WHERE id = %s
        """, (
            cliente_id,
            cliente,
            descricao,
            float(valor),
            vencimento,
            status,
            observacoes,
            forma_pagamento,
            conta_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro atualizar_conta_receber:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


def receber_conta(
    conta_id,
    origem_financeira="CAIXA",
    conta_bancaria_id=None,
    caixa_id=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT valor, descricao, status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        valor, descricao, status = conta

        if status == "RECEBIDO":
            print("Conta já está recebida.")
            return False

        cursor.execute("""
            UPDATE contas_receber
            SET status = 'RECEBIDO',
                data_recebimento = %s,
                origem = %s,
                forma_pagamento = %s,
                conta_bancaria_id = %s,
                caixa_id = %s
            WHERE id = %s
        """, (
            datetime.now(),
            origem_financeira,
            origem_financeira,
            conta_bancaria_id,
            caixa_id,
            conta_id
        ))

        sucesso = registrar_movimentacao_financeira(
            tipo="ENTRADA",
            valor=valor,
            descricao=f"Recebimento conta: {descricao}",
            origem=origem_financeira,
            categoria="CONTAS_A_RECEBER",
            referencia_id=conta_id,
            referencia_tipo="CONTAS_RECEBER",
            conta_bancaria_id=conta_bancaria_id,
            meio=origem_financeira,
            caixa_id=caixa_id,
            conn_externa=conn
        )

        if not sucesso:
            conn.rollback()
            return False

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro receber_conta:", erro)
        return False

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
            DELETE FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro excluir_conta_receber:", erro)
        return False

    finally:
        cursor.close()
        conn.close()

# ==================================================
# COMPATIBILIDADE COM MÓDULOS ANTIGOS
# ==================================================

def cadastrar_conta_receber(
    cliente_id,
    descricao,
    valor,
    vencimento,
    observacoes=None,
    cliente=None,
    forma_pagamento=None
):
    return cadastrar_conta(
        descricao=descricao,
        valor=valor,
        vencimento=vencimento,
        cliente_id=cliente_id,
        cliente=cliente,
        observacoes=observacoes,
        forma_pagamento=forma_pagamento
    )