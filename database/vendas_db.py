# database/vendas_db.py

import pandas as pd
from database.connection import conectar


# ==================================================
# LISTAR CLIENTES
# ==================================================
def listar_clientes():

    conn = conectar()

    query = """
        SELECT id, nome
        FROM clientes
        ORDER BY nome
    """

    df = pd.read_sql(query, conn)

    conn.close()
    return df


# ==================================================
# LISTAR PRODUTOS
# ==================================================
def listar_produtos():

    conn = conectar()

    query = """
        SELECT *
        FROM produtos
        ORDER BY nome
    """

    df = pd.read_sql(query, conn)

    conn.close()
    return df


# ==================================================
# SALVAR VENDA
# ==================================================
def salvar_venda(cliente_id, valor_total, forma_pagamento, itens):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==========================================
        # INSERIR VENDA
        # ==========================================
        cursor.execute("""
            INSERT INTO vendas (cliente_id, valor_total, forma_pagamento)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (cliente_id, valor_total, forma_pagamento))

        venda_id = cursor.fetchone()[0]

        # ==========================================
        # ITENS + ESTOQUE
        # ==========================================
        for item in itens:

            cursor.execute("""
                INSERT INTO itens_venda (
                    venda_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                venda_id,
                item["produto_id"],
                item["quantidade"],
                item["preco"],
                item["subtotal"]
            ))

            cursor.execute("""
                UPDATE produtos
                SET estoque = estoque - %s
                WHERE id = %s
            """, (
                item["quantidade"],
                item["produto_id"]
            ))

        # ==========================================
        # CONTAS A PRAZO
        # ==========================================
        if forma_pagamento == "Prazo":

            cursor.execute("""
                INSERT INTO contas_receber (
                    cliente_id,
                    descricao,
                    valor,
                    vencimento,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    CURRENT_DATE + INTERVAL '30 days',
                    %s
                )
            """, (
                cliente_id,
                "Venda a prazo",
                valor_total,
                "Pendente"
            ))

        # ==========================================
        # VENDA À VISTA → MOVIMENTAÇÕES (NOVO PADRÃO)
        # ==========================================
        else:

            cursor.execute("""
                INSERT INTO movimentacoes (
                    tipo,
                    valor,
                    descricao,
                    origem
                )
                VALUES (%s, %s, %s, %s)
            """, (
                "entrada",
                valor_total,
                "Venda realizada",
                "Venda"
            ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao salvar venda:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# HISTÓRICO DE VENDAS
# ==================================================
def historico_vendas():

    conn = conectar()

    query = """
        SELECT
            v.id AS pedido,
            c.nome AS cliente,
            p.nome AS produto,
            iv.quantidade,
            iv.preco_unitario,
            iv.subtotal,
            v.valor_total,
            v.forma_pagamento,
            v.data_venda
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN itens_venda iv ON v.id = iv.venda_id
        LEFT JOIN produtos p ON iv.produto_id = p.id
        ORDER BY v.id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()
    return df