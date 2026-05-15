# database/movimentacoes_db.py

import pandas as pd
from database.connection import conectar


# ==================================================
# REGISTRAR MOVIMENTAÇÃO
# ==================================================

def registrar_movimentacao(tipo, valor, descricao, origem):
    """
    tipo: 'entrada' ou 'saida'
    valor: float
    descricao: texto explicativo
    origem: venda, compra, recebimento, ajuste etc.
    """

    conn = conectar()
    cursor = conn.cursor()

    try:
        query = """
            INSERT INTO movimentacoes (
                tipo,
                valor,
                descricao,
                origem
            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(query, (
            tipo,
            valor,
            descricao,
            origem
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao registrar movimentação:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# LISTAR MOVIMENTAÇÕES
# ==================================================

def listar_movimentacoes():

    conn = conectar()

    query = """
        SELECT
            id,
            tipo,
            valor,
            descricao,
            origem,
            data
        FROM movimentacoes
        ORDER BY id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# RESUMO FINANCEIRO (USADO NO DASHBOARD)
# ==================================================

def resumo_movimentacoes():

    conn = conectar()
    cursor = conn.cursor()

    try:
        # ENTRADAS
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'entrada'
        """)
        entradas = float(cursor.fetchone()[0])

        # SAÍDAS
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'saida'
        """)
        saidas = float(cursor.fetchone()[0])

        saldo = entradas - saidas

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo
        }

    finally:
        cursor.close()
        conn.close()