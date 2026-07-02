from datetime import datetime
import pandas as pd

from database.connection import conectar

from database.finance_engine import (
    registrar_saida_caixa,
    registrar_saida_banco
)


# ==================================================
# NORMALIZAR TEXTO
# ==================================================
def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip().upper()


# ==================================================
# LISTAR CONTAS A PAGAR - SOMENTE PENDENTES
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
            WHERE UPPER(COALESCE(status, 'PENDENTE')) = 'PENDENTE'
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
        categoria = normalizar_texto(categoria) if categoria else None
        tipo = normalizar_texto(tipo) if tipo else None

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
        categoria = normalizar_texto(categoria) if categoria else None
        tipo = normalizar_texto(tipo) if tipo else None
        status = normalizar_texto(status) if status else "PENDENTE"

        cursor.execute("""
            UPDATE contas_pagar
            SET
                descricao = %s,
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
# PAGAR / BAIXAR CONTA
# ==================================================
def pagar_conta(
    conta_id,
    origem_financeira="CAIXA",
    conta_bancaria_id=None,
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
            FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise Exception("Conta a pagar não encontrada.")

        valor, descricao, status = conta

        status_atual = normalizar_texto(status)

        if status_atual in ["PAGO", "PAGA"]:
            raise Exception("Conta já está paga.")

        origem_normalizada = normalizar_texto(origem_financeira)

        # ==========================================
        # PAGAMENTO EM DINHEIRO / CAIXA
        # ==========================================
        if origem_normalizada in ["CAIXA", "DINHEIRO"]:

            sucesso = registrar_saida_caixa(
                valor=valor,
                descricao=f"Pagamento conta #{conta_id}: {descricao}",
                origem=origem_financeira,
                categoria="CONTAS_A_PAGAR",
                referencia_id=conta_id,
                referencia_tipo="CONTAS_PAGAR",
                usuario=usuario,
                conn_externa=conn
            )

            if not sucesso:
                raise Exception("Falha ao registrar saída do caixa.")

            conta_bancaria_id = None

        # ==========================================
        # PAGAMENTO VIA BANCO
        # ==========================================
        elif origem_normalizada in [
            "BANCO",
            "PIX",
            "BOLETO",
            "TRANSFERENCIA",
            "TRANSFERÊNCIA",
            "CARTAO",
            "CARTÃO",
            "DEBITO",
            "DÉBITO",
            "CARTAO DEBITO",
            "CARTÃO DÉBITO"
        ]:

            if conta_bancaria_id is None:
                conta_bancaria_id = buscar_primeira_conta_bancaria(conn)

            if conta_bancaria_id is None:
                raise Exception("Nenhuma conta bancária cadastrada.")

            sucesso = registrar_saida_banco(
                conta_bancaria_id=conta_bancaria_id,
                valor=valor,
                descricao=f"Pagamento conta #{conta_id}: {descricao}",
                origem=origem_financeira,
                categoria="CONTAS_A_PAGAR",
                referencia_id=conta_id,
                referencia_tipo="CONTAS_PAGAR",
                usuario=usuario,
                conn_externa=conn
            )

            if not sucesso:
                raise Exception("Falha ao registrar saída bancária.")

        else:
            raise Exception(f"Origem financeira inválida: {origem_financeira}")

        cursor.execute("""
            UPDATE contas_pagar
            SET
                status = 'PAGO',
                data_pagamento = %s,
                forma_pagamento = %s,
                origem_pagamento = %s,
                conta_bancaria_id = %s
            WHERE id = %s
        """, (
            datetime.now(),
            origem_financeira,
            origem_financeira,
            conta_bancaria_id,
            conta_id
        ))

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