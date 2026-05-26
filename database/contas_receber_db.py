from datetime import datetime
import pandas as pd

from database.connection import conectar
from database.caixa_db import verificar_caixa_aberto
from database.movimentacoes_db import registrar_movimentacao


# ==================================================
# TRATAMENTO TEXTO
# ==================================================
def tratar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


# ==================================================
# CADASTRAR CONTA A RECEBER
# ==================================================
def cadastrar_conta_receber(
    cliente_id,
    descricao,
    valor,
    vencimento,
    observacoes=""
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        descricao = tratar_texto(descricao)
        observacoes = tratar_texto(observacoes)

        valor = float(valor)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        cursor.execute("""
            INSERT INTO contas_receber (
                cliente_id,
                descricao,
                valor,
                vencimento,
                observacoes,
                status,
                criado_em
            )
            VALUES (
                %s, %s, %s, %s, %s,
                'Pendente',
                NOW()
            )
        """, (
            cliente_id,
            descricao,
            valor,
            vencimento,
            observacoes
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro cadastrar conta receber:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# LISTAR CONTAS A RECEBER
# ==================================================
def listar_contas_receber():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                cr.id,
                c.nome AS cliente,
                cr.cliente_id,
                cr.descricao,
                cr.valor,
                cr.vencimento,
                cr.status,
                cr.data_recebimento,
                cr.observacoes,
                cr.criado_em
            FROM contas_receber cr
            LEFT JOIN clientes c ON cr.cliente_id = c.id
            ORDER BY cr.vencimento ASC
        """

        df = pd.read_sql(query, conn)

        return df.fillna("") if not df.empty else pd.DataFrame()

    except Exception as erro:
        print("Erro listar contas receber:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RECEBER CONTA (APENAS DB - SEM REGRA FINANCEIRA)
# ==================================================
def receber_conta(conta_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE contas_receber
            SET status = 'Recebido',
                data_recebimento = NOW()
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao receber conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CONTA
# ==================================================
def atualizar_conta_receber(conta_id, descricao, valor, vencimento):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE contas_receber
            SET descricao = %s,
                valor = %s,
                vencimento = %s
            WHERE id = %s
        """, (
            descricao,
            valor,
            vencimento,
            conta_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro atualizar conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CONTA
# ==================================================
def excluir_conta_receber(conta_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        status = tratar_texto(conta[0]).lower()

        if status == "recebido":
            return "recebido"

        cursor.execute("""
            DELETE FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro excluir conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# RESUMO CONTAS A RECEBER
# ==================================================
def resumo_contas_receber():

    conn = conectar()

    if conn is None:
        return {"pendente": 0, "recebido": 0, "total": 0}

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_receber
            WHERE LOWER(status) = 'pendente'
        """)
        pendente = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_receber
            WHERE LOWER(status) = 'recebido'
        """)
        recebido = float(cursor.fetchone()[0])

        return {
            "pendente": pendente,
            "recebido": recebido,
            "total": pendente + recebido
        }

    except Exception as erro:
        print("Erro resumo contas receber:", erro)
        return {"pendente": 0, "recebido": 0, "total": 0}

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
                data_recebimento,
                observacoes
            FROM contas_receber
            ORDER BY vencimento ASC
        """)

        dados = cursor.fetchall()

        return dados

    except Exception as erro:

        print(f"Erro ao listar contas a receber: {erro}")

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
            DELETE FROM contas_receber
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