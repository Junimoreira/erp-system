from datetime import datetime, date
import pandas as pd

from database.connection import conectar

from database.finance_engine import (
    registrar_saida_caixa,
    registrar_saida_banco
)


def normalizar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip().upper()


def normalizar_data_pagamento(data_pagamento=None):
    if data_pagamento is None:
        return datetime.now()

    if isinstance(data_pagamento, datetime):
        return data_pagamento

    if isinstance(data_pagamento, date):
        agora = datetime.now()
        return datetime.combine(data_pagamento, agora.time())

    return datetime.now()


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


def pagar_conta(
    conta_id,
    origem_financeira="CAIXA",
    conta_bancaria_id=None,
    usuario=None,
    data_pagamento=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        data_pagamento = normalizar_data_pagamento(data_pagamento)

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
            UPDATE movimentacoes
            SET data_movimentacao = %s
            WHERE id = (
                SELECT id
                FROM movimentacoes
                WHERE referencia_tipo = 'CONTAS_PAGAR'
                  AND referencia_id = %s
                ORDER BY id DESC
                LIMIT 1
            )
        """, (
            data_pagamento,
            conta_id
        ))

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
            data_pagamento,
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