from datetime import datetime
import pandas as pd

from database.connection import conectar

from database.finance_engine import (
    registrar_entrada_caixa,
    registrar_entrada_banco,
    buscar_caixa_aberto
)


# ==================================================
# NORMALIZAR TEXTO
# ==================================================
def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip().upper()


# ==================================================
# LISTAR CONTAS A RECEBER - SOMENTE PENDENTES
# ==================================================
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
                cr.data_pagamento,
                cr.forma_pagamento,
                cr.caixa_id,
                cr.origem,
                cr.conta_bancaria_id
            FROM contas_receber cr
            LEFT JOIN clientes c
                ON c.id = cr.cliente_id
            WHERE UPPER(COALESCE(cr.status, 'PENDENTE')) = 'PENDENTE'
            ORDER BY cr.vencimento ASC, cr.id ASC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar_contas_receber:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# CADASTRAR CONTA A RECEBER
# ==================================================
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
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
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


# ==================================================
# ATUALIZAR CONTA A RECEBER
# ==================================================
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
            SET
                cliente_id = %s,
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


# ==================================================
# BUSCAR PRIMEIRA CONTA BANCÁRIA
# ==================================================
def buscar_primeira_conta_bancaria(conn):

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM contas_bancarias
            ORDER BY id
            LIMIT 1
        """)

        conta = cursor.fetchone()

        return int(conta[0]) if conta else None

    finally:
        cursor.close()


# ==================================================
# RECEBER CONTA
# ==================================================
def receber_conta(
    conta_id,
    origem_financeira="CAIXA",
    conta_bancaria_id=None,
    caixa_id=None,
    usuario=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                valor,
                descricao,
                status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise Exception("Conta a receber não encontrada.")

        valor, descricao, status = conta

        status_atual = normalizar_texto(status)

        if status_atual in ["RECEBIDO", "PAGO", "PAGA"]:
            raise Exception("Conta já está recebida.")

        origem_normalizada = normalizar_texto(origem_financeira)

        if origem_normalizada in ["CAIXA", "DINHEIRO"]:

            caixa_id = buscar_caixa_aberto(conn)

            if caixa_id is None:
                raise Exception("Recebimento em dinheiro exige caixa aberto.")

            sucesso = registrar_entrada_caixa(
                valor=valor,
                descricao=f"Recebimento conta #{conta_id}: {descricao}",
                origem=origem_financeira,
                categoria="CONTAS_A_RECEBER",
                referencia_id=conta_id,
                referencia_tipo="CONTAS_RECEBER",
                usuario=usuario,
                conn_externa=conn
            )

            if not sucesso:
                raise Exception("Falha ao registrar entrada no caixa.")

            conta_bancaria_id = None

        elif origem_normalizada in [
            "BANCO",
            "PIX",
            "DEBITO",
            "CARTAO DEBITO",
            "TRANSFERENCIA",
            "BOLETO"
        ]:

            if conta_bancaria_id is None:
                conta_bancaria_id = buscar_primeira_conta_bancaria(conn)

            if conta_bancaria_id is None:
                raise Exception("Nenhuma conta bancária cadastrada.")

            sucesso = registrar_entrada_banco(
                conta_bancaria_id=conta_bancaria_id,
                valor=valor,
                descricao=f"Recebimento conta #{conta_id}: {descricao}",
                origem=origem_financeira,
                categoria="CONTAS_A_RECEBER",
                referencia_id=conta_id,
                referencia_tipo="CONTAS_RECEBER",
                usuario=usuario,
                conn_externa=conn
            )

            if not sucesso:
                raise Exception("Falha ao registrar entrada bancária.")

            caixa_id = None

        else:
            raise Exception(f"Origem financeira inválida: {origem_financeira}")

        cursor.execute("""
            UPDATE contas_receber
            SET
                status = 'RECEBIDO',
                data_recebimento = %s,
                data_pagamento = %s,
                origem = %s,
                forma_pagamento = %s,
                conta_bancaria_id = %s,
                caixa_id = %s
            WHERE id = %s
        """, (
            datetime.now(),
            datetime.now(),
            origem_financeira,
            origem_financeira,
            conta_bancaria_id,
            caixa_id,
            conta_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro receber_conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CONTA A RECEBER
# ==================================================
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