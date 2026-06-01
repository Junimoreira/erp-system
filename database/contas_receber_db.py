from datetime import datetime
import pandas as pd

from database.connection import conectar
from database.caixa_db import verificar_caixa_aberto
from database.movimentacoes_db import registrar_movimentacao
from database.contas_bancarias import listar_contas as listar_bancos


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
def listar_contas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                cliente_id,
                descricao,
                valor,
                vencimento,
                status,
                observacoes,
                criado_em,
                forma_pagamento,
                data_recebimento,
                data_pagamento
            FROM contas_receber
            ORDER BY vencimento ASC
        """

        df = pd.read_sql(query, conn)
        return df.fillna("")

    except Exception as erro:
        print("Erro listar contas receber:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RECEBER CONTA (VERSÃO CORRIGIDA FUTURA)
# ==================================================
def receber_conta(conta_id, origem_financeira="CAIXA", conta_bancaria_id=None):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT descricao, valor, status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise ValueError("Conta não encontrada.")

        descricao = tratar_texto(conta[0])
        valor = float(conta[1])
        status = tratar_texto(conta[2]).lower()

        if status == "recebido":
            raise ValueError("Conta já recebida.")

        # ==========================================
        # CAIXA
        # ==========================================
        if origem_financeira.upper() == "CAIXA":

            caixa = verificar_caixa_aberto()

            if caixa is None:
                raise ValueError("Nenhum caixa aberto.")

            caixa_id = caixa[0]

            registrar_movimentacao(
                caixa_id=caixa_id,
                tipo="entrada",
                valor=valor,
                descricao=descricao,
                categoria="recebimento",
                origem="contas_receber",
                data_movimentacao=datetime.now()
            )

        # ==========================================
        # BANCO
        # ==========================================
        elif origem_financeira.upper() == "BANCO":

            if conta_bancaria_id is None:
                raise ValueError("Conta bancária não informada.")

            cursor.execute("""
                UPDATE contas_bancarias
                SET saldo = saldo + %s
                WHERE id = %s
            """, (valor, conta_bancaria_id))

        else:
            raise ValueError("Origem inválida.")

        # ==========================================
        # ATUALIZA CONTA
        # ==========================================
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
        print("Erro receber conta:", erro)
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
            float(valor),
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

        if tratar_texto(conta[0]).lower() == "recebido":
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