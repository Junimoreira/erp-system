# database/vendas_db.py

import pandas as pd
from datetime import datetime

from database.connection import conectar

from database.caixa_db import (
    verificar_caixa_aberto
)


# ==================================================
# LISTAR CLIENTES
# ==================================================
def listar_clientes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                nome
            FROM clientes
            ORDER BY nome
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        print("Erro ao listar clientes:", erro)

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# LISTAR PRODUTOS
# ==================================================
def listar_produtos():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                *
            FROM produtos
            ORDER BY nome
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        print("Erro ao listar produtos:", erro)

        return pd.DataFrame()

    finally:

        conn.close()


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

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        valor_total = float(valor_total)
        desconto = float(desconto)
        valor_final = float(valor_final)

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

        venda_id = int(cursor.fetchone()[0])

        # ==========================================
        # ITENS DA VENDA
        # ==========================================
        for item in itens:

            quantidade = float(item["quantidade"])

            preco = float(item["preco"])

            subtotal = float(item["subtotal"])

            produto_id = int(item["produto_id"])

            # ======================================
            # ITEM VENDA
            # ======================================
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
                produto_id,
                quantidade,
                preco,
                subtotal

            ))

            # ======================================
            # BAIXA ESTOQUE
            # ======================================
            cursor.execute("""
                UPDATE produtos

                SET estoque = estoque - %s

                WHERE id = %s
            """, (

                quantidade,
                produto_id

            ))

        # ==========================================
        # VENDA A PRAZO
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
        # DINHEIRO = ENTRA NO CAIXA
        # ==========================================
        elif forma_pagamento == "Dinheiro":

            caixa = verificar_caixa_aberto()

            if caixa is None:

                raise ValueError(
                    "Não existe caixa aberto para receber venda em dinheiro."
                )

            caixa_id = int(caixa[0])

            cursor.execute("""
                INSERT INTO movimentacoes (

                    caixa_id,
                    tipo,
                    valor,
                    descricao,
                    categoria,
                    origem,
                    data_movimentacao

                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (

                caixa_id,
                "entrada",
                valor_final,
                f"Venda Dinheiro #{venda_id}",
                "Venda",
                "Caixa",
                datetime.now()

            )
        # ==========================================
        # PIX = CONTA BANCÁRIA
        # ==========================================
        elif forma_pagamento == "PIX":

            cursor.execute("""
                INSERT INTO movimentacoes (

                    tipo,
                    valor,
                    descricao,
                    categoria,
                    origem,
                    data_movimentacao

                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (

                "entrada",
                valor_final,
                f"Venda PIX #{venda_id}",
                "Venda",
                "Banco PIX",
                datetime.now()

            ))

        # ==========================================
        # CARTÃO = CONTA BANCÁRIA
        # ==========================================
        elif forma_pagamento == "Cartão":

            cursor.execute("""
                INSERT INTO movimentacoes (

                    tipo,
                    valor,
                    descricao,
                    categoria,
                    origem,
                    data_movimentacao

                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (

                "entrada",
                valor_final,
                f"Venda Cartão #{venda_id}",
                "Venda",
                "Cartão",
                datetime.now()

            ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        import traceback

        print("\n" + "=" * 80)
        print("ERRO AO SALVAR VENDA")
        print("TIPO:", type(erro))
        print("MENSAGEM:", str(erro))
        traceback.print_exc()
        print("=" * 80)

        raise

    finally:

        cursor.close()
        conn.close()


# ==================================================
# HISTÓRICO DE VENDAS
# ==================================================
def historico_vendas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

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

        return df

    except Exception as erro:

        print("Erro no histórico:", erro)

        return pd.DataFrame()

    finally:

        conn.close()