from datetime import datetime
import pandas as pd

from database.connection import conectar
from database.finance_engine import registrar_movimentacao_financeira
from database.contas_bancarias import remover_saldo


# ==================================================
# LISTAR CONTAS A PAGAR
# ==================================================
def listar_contas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                id,
                descricao,
                valor,
                vencimento,
                categoria,
                tipo,
                status,
                observacoes,
                data_pagamento,
                origem_pagamento,
                conta_bancaria_id,
                criado_em
            FROM contas_pagar
            ORDER BY vencimento ASC, id ASC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar_contas_pagar:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# CADASTRAR CONTA A PAGAR
# categoria = FIXA ou VARIAVEL
# tipo = ALUGUEL, SALARIO, FORNECEDOR etc.
# ==================================================
def cadastrar_conta(
    descricao,
    valor,
    vencimento,
    categoria=None,
    tipo=None,
    observacoes=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        categoria = str(categoria).upper().strip() if categoria else None
        tipo = str(tipo).upper().strip() if tipo else None

        cursor.execute("""
            INSERT INTO contas_pagar (
                descricao,
                valor,
                vencimento,
                categoria,
                tipo,
                status,
                observacoes,
                criado_em
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            descricao,
            float(valor),
            vencimento,
            categoria,
            tipo,
            "PENDENTE",
            observacoes,
            datetime.now()
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro cadastrar_conta_pagar:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CONTA A PAGAR
# ==================================================
def atualizar_conta(
    conta_id,
    descricao,
    valor,
    vencimento,
    categoria=None,
    tipo=None,
    status="PENDENTE",
    observacoes=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        categoria = str(categoria).upper().strip() if categoria else None
        tipo = str(tipo).upper().strip() if tipo else None

        cursor.execute("""
            UPDATE contas_pagar
            SET descricao = %s,
                valor = %s,
                vencimento = %s,
                categoria = %s,
                tipo = %s,
                status = %s,
                observacoes = %s
            WHERE id = %s
        """, (
            descricao,
            float(valor),
            vencimento,
            categoria,
            tipo,
            status,
            observacoes,
            conta_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro atualizar_conta_pagar:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# PAGAR / BAIXAR CONTA
# ==================================================
def pagar_conta(
    conta_id,
    origem_financeira="CAIXA",
    conta_bancaria_id=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT valor, descricao, status
            FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        valor, descricao, status = conta

        if str(status).upper().strip() == "PAGO":
            print("Conta já está paga.")
            return False

        origem_financeira = str(origem_financeira).upper().strip()

        formas_banco = [
            "BANCO",
            "PIX",
            "BOLETO",
            "TRANSFERÊNCIA",
            "TRANSFERENCIA",
            "CARTÃO",
            "CARTAO",
            "DÉBITO",
            "DEBITO",
            "CARTÃO DÉBITO",
            "CARTAO DEBITO"
        ]

        if origem_financeira in formas_banco:

            if conta_bancaria_id is None:
                print("Conta bancária não informada para pagamento via banco.")
                conn.rollback()
                return False

            sucesso_banco = remover_saldo(
                conta_id=conta_bancaria_id,
                valor=valor,
                conn_externa=conn
            )

            if not sucesso_banco:
                conn.rollback()
                return False

            meio = "BANCO"

        else:
            meio = "CAIXA"

        cursor.execute("""
            UPDATE contas_pagar
            SET status = 'PAGO',
                data_pagamento = %s,
                origem_pagamento = %s,
                conta_bancaria_id = %s
            WHERE id = %s
        """, (
            datetime.now(),
            origem_financeira,
            conta_bancaria_id,
            conta_id
        ))

        sucesso = registrar_movimentacao_financeira(
            tipo="SAIDA",
            valor=valor,
            descricao=f"Pagamento conta: {descricao}",
            origem=origem_financeira,
            categoria="CONTAS_A_PAGAR",
            referencia_id=conta_id,
            referencia_tipo="CONTAS_PAGAR",
            conta_bancaria_id=conta_bancaria_id,
            meio=meio,
            caixa_id=None,
            conn_externa=conn
        )

        if not sucesso:
            conn.rollback()
            return False

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro pagar_conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CONTA A PAGAR
# ==================================================
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
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro excluir_conta_pagar:", erro)
        return False

    finally:
        cursor.close()
        conn.close()