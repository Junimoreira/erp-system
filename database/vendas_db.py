# database/vendas_db.py

import pandas as pd
from datetime import datetime

from database.connection import conectar

from database.caixa_db import (
    verificar_caixa_aberto,
    registrar_entrada_caixa
)

from database.contas_bancarias import (
    adicionar_saldo
)

from database.movimentacoes_bancarias_db import (
    registrar_movimentacao_bancaria
)

from database.contas_receber_db import (
    cadastrar_conta_receber
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

            cursor.execute("""
                UPDATE produtos
                SET estoque = COALESCE(estoque, 0) - %s
                WHERE id = %s
            """, (
                quantidade,
                produto_id
            ))

        # ==========================================
        # VERIFICA CAIXA
        # ==========================================
        caixa = verificar_caixa_aberto()

        caixa_id = None

        if caixa is not None:
            caixa_id = int(caixa[0])

        forma = str(forma_pagamento).upper().strip()

        # ==========================================
        # DINHEIRO -> CAIXA
        # ==========================================
        if forma == "DINHEIRO":

            if caixa_id:

                registrar_entrada_caixa(
                    caixa_id,
                    valor_final
                )

                try:

                    from database.movimentacoes_db import registrar_movimentacao

                    registrar_movimentacao(
                        caixa_id=caixa_id,
                        tipo="entrada",
                        valor=float(valor_final),
                        descricao=f"Venda #{venda_id}",
                        categoria="Venda",
                        origem="DINHEIRO",
                        data_movimentacao=datetime.now()
                    )

                except Exception as erro_mov:

                    print(
                        "Erro movimentação caixa:",
                        erro_mov
                    )

        # ==========================================
        # BANCO
        # PIX / DÉBITO / BOLETO / TRANSFERÊNCIA
        # ==========================================
        elif forma in [

            "PIX",
            "CARTÃO DÉBITO",
            "CARTAO DÉBITO",
            "CARTAO DEBITO",
            "TRANSFERÊNCIA",
            "TRANSFERENCIA",
            "BOLETO"

        ]:

            cursor.execute("""
                SELECT id
                FROM contas_bancarias
                ORDER BY id
                LIMIT 1
            """)

            conta = cursor.fetchone()

            if not conta:

                raise Exception(
                    "Nenhuma conta bancária cadastrada."
                )

            conta_bancaria_id = int(conta[0])

            adicionar_saldo(
                conta_bancaria_id,
                valor_final
            )

            registrar_movimentacao_bancaria(
                conta_id=conta_bancaria_id,
                tipo="entrada",
                valor=float(valor_final),
                descricao=f"Venda #{venda_id} - {forma}"
            )

        # ==========================================
        # CONTAS A RECEBER
        # CRÉDITO / PRAZO
        # ==========================================
        elif forma in [

            "CARTÃO CRÉDITO",
            "CARTAO CRÉDITO",
            "CARTAO CREDITO",
            "PRAZO"

        ]:

            cadastrar_conta_receber(
                cliente_id=cliente_id,
                descricao=f"Venda #{venda_id}",
                valor=float(valor_final),
                vencimento=data_venda,
                observacoes=f"Gerado automaticamente pela venda #{venda_id}"
            )

        # ==========================================
        # COMMIT
        # ==========================================
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

        return False

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

        print(
            "Erro no histórico de vendas:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()