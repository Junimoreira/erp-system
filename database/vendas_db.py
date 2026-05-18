# database/vendas_db.py

import pandas as pd
from database.connection import conectar


# ==================================================
# LISTAR CLIENTES
# ==================================================
def listar_clientes():

    conn = conectar()

    query = """
        SELECT
            id,
            nome
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
        SELECT
            *
        FROM produtos
        ORDER BY nome
    """

    df = pd.read_sql(query, conn)

    conn.close()
    return df


# ==================================================
# SALVAR VENDA
# ==================================================
def salvar_venda(
    cliente_id,
    valor_total,
    desconto,
    valor_final,
    forma_pagamento,
    data_venda,
    itens
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==========================================
        # INSERIR VENDA
        # ==========================================
        cursor.execute("""
            INSERT INTO vendas (
                cliente_id,
                valor_total,
                desconto,
                valor_final,
                forma_pagamento,
                data_venda
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            cliente_id,
            valor_total,
            desconto,
            valor_final,
            forma_pagamento,
            data_venda
        ))

        venda_id = cursor.fetchone()[0]

        # ==========================================
        # ITENS DA VENDA
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

            # ======================================
            # BAIXA ESTOQUE
            # ======================================
            cursor.execute("""
                UPDATE produtos
                SET estoque = estoque - %s
                WHERE id = %s
            """, (
                item["quantidade"],
                item["produto_id"]
            ))

        # ==========================================
        # CONTAS A RECEBER
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
                f"Venda #{venda_id}",
                valor_final,
                "Pendente"
            ))

        # ==========================================
        # MOVIMENTAÇÃO FINANCEIRA
        # ==========================================
        else:

            cursor.execute("""
                INSERT INTO movimentacoes (
                    tipo,
                    valor,
                    descricao,
                    origem,
                    data_movimentacao
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                "entrada",
                valor_final,
                f"Venda #{venda_id}",
                "Venda",
                data_venda
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
            v.data_venda,

            c.nome AS cliente,

            p.nome AS produto,

            iv.quantidade,

            iv.preco_unitario AS valor_unitario,

            iv.subtotal,

            v.desconto,

            v.valor_final,

            v.forma_pagamento

        FROM vendas v

        LEFT JOIN clientes c
            ON v.cliente_id = c.id

        LEFT JOIN itens_venda iv
            ON v.id = iv.venda_id

        LEFT JOIN produtos p
            ON iv.produto_id = p.id

        ORDER BY v.id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df