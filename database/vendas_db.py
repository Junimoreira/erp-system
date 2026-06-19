import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

from database.connection import conectar

from database.caixa_db import obter_caixa_aberto_id
from database.finance_engine import (
    registrar_entrada_caixa,
    registrar_movimentacao_financeira
)
from database.contas_receber_db import cadastrar_conta_receber
from database.contas_bancarias import adicionar_saldo


# ==================================================
# CLIENTES
# ==================================================
def listar_clientes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("""
            SELECT
                id,
                nome
            FROM clientes
            ORDER BY nome
        """, conn)

    finally:
        conn.close()


# ==================================================
# PRODUTOS
# ==================================================
def listar_produtos():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("""
            SELECT
                id,
                nome,
                preco,
                estoque,
                codigo_barras
            FROM produtos
            ORDER BY nome
        """, conn)

    finally:
        conn.close()


# ==================================================
# NORMALIZAR FORMA DE PAGAMENTO
# ==================================================
def normalizar_forma_pagamento(forma_pagamento):

    forma = str(forma_pagamento).upper().strip()

    substituicoes = {
        "Á": "A",
        "Ã": "A",
        "É": "E",
        "Ê": "E",
        "Í": "I",
        "Ó": "O",
        "Õ": "O",
        "Ú": "U",
        "Ç": "C"
    }

    for antigo, novo in substituicoes.items():
        forma = forma.replace(antigo, novo)

    return forma


# ==================================================
# GERAR PARCELAS
# ==================================================
def gerar_parcelas(valor_total, numero_parcelas):

    numero_parcelas = int(numero_parcelas)

    if numero_parcelas <= 0:
        numero_parcelas = 1

    valor_total = round(float(valor_total), 2)

    valor_base = round(valor_total / numero_parcelas, 2)

    parcelas = []

    acumulado = 0

    for parcela in range(1, numero_parcelas + 1):

        if parcela < numero_parcelas:
            valor_parcela = valor_base
            acumulado += valor_parcela
        else:
            valor_parcela = round(valor_total - acumulado, 2)

        parcelas.append(valor_parcela)

    return parcelas


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
    itens,
    conta_bancaria_id=None,
    numero_parcelas=1
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        forma_normalizada = normalizar_forma_pagamento(forma_pagamento)

        cursor.execute("""
            INSERT INTO vendas(
                cliente_id,
                valor_total,
                desconto,
                valor_final,
                forma_pagamento,
                data_venda,
                status
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """, (
            cliente_id,
            float(valor_total),
            float(desconto),
            float(valor_final),
            forma_pagamento,
            data_venda,
            "Concluída"
        ))

        venda_id = int(cursor.fetchone()[0])

        for item in itens:

            quantidade = int(item["quantidade"])
            preco = float(item["preco"])
            subtotal = float(item["subtotal"])

            cursor.execute("""
                INSERT INTO itens_venda(
                    venda_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    subtotal
                )
                VALUES(%s,%s,%s,%s,%s)
            """, (
                venda_id,
                item["produto_id"],
                quantidade,
                preco,
                subtotal
            ))

            cursor.execute("""
                UPDATE produtos
                SET estoque = COALESCE(estoque,0) - %s
                WHERE id = %s
            """, (
                quantidade,
                item["produto_id"]
            ))

        # ==========================================
        # DINHEIRO / CAIXA
        # ==========================================
        if forma_normalizada in ["DINHEIRO", "CAIXA"]:

            caixa_id = obter_caixa_aberto_id(conn_externa=conn)

            if caixa_id is None:
                raise Exception("Venda em dinheiro exige caixa aberto.")

            sucesso_caixa = registrar_entrada_caixa(
                caixa_id=caixa_id,
                valor=valor_final,
                descricao=f"Venda #{venda_id} ({forma_pagamento})",
                origem=forma_pagamento,
                categoria="VENDA",
                referencia_id=venda_id,
                referencia_tipo="VENDA",
                conn_externa=conn
            )

            if not sucesso_caixa:
                raise Exception("Falha ao registrar entrada no caixa.")

        # ==========================================
        # BANCO / PIX / DÉBITO / TRANSFERÊNCIA
        # ==========================================
        elif forma_normalizada in [
            "PIX",
            "DEBITO",
            "CARTAO DEBITO",
            "TRANSFERENCIA",
            "BOLETO",
            "BANCO"
        ]:

            if conta_bancaria_id is not None:

                sucesso_banco = adicionar_saldo(
                    conta_id=conta_bancaria_id,
                    valor=valor_final
                )

                if not sucesso_banco:
                    raise Exception("Falha ao adicionar saldo na conta bancária.")

            sucesso_mov = registrar_movimentacao_financeira(
                tipo="ENTRADA",
                valor=valor_final,
                descricao=f"Venda #{venda_id} ({forma_pagamento})",
                origem=forma_pagamento,
                categoria="VENDA",
                referencia_id=venda_id,
                referencia_tipo="VENDA",
                conta_bancaria_id=conta_bancaria_id,
                meio="BANCO",
                caixa_id=None,
                conn_externa=conn
            )

            if not sucesso_mov:
                raise Exception("Falha ao registrar movimentação bancária.")

        # ==========================================
        # CRÉDITO / PRAZO / FIADO PARCELADO
        # ==========================================
        elif forma_normalizada in [
            "CREDITO",
            "CARTAO CREDITO",
            "PRAZO",
            "FIADO"
        ]:

            numero_parcelas = int(numero_parcelas)

            if numero_parcelas < 1:
                numero_parcelas = 1

            parcelas = gerar_parcelas(
                valor_total=valor_final,
                numero_parcelas=numero_parcelas
            )

            data_base = data_venda

            if isinstance(data_base, datetime):
                data_base = data_base.date()

            for indice, valor_parcela in enumerate(parcelas, start=1):

                vencimento = data_base + relativedelta(months=indice)

                sucesso_receber = cadastrar_conta_receber(
                    cliente_id=cliente_id,
                    descricao=f"Venda #{venda_id} - Parcela {indice}/{numero_parcelas}",
                    valor=valor_parcela,
                    vencimento=vencimento,
                    observacoes=f"Gerado automaticamente pela venda #{venda_id}",
                    forma_pagamento=forma_pagamento
                )

                if not sucesso_receber:
                    raise Exception(f"Falha ao gerar parcela {indice}/{numero_parcelas} em contas a receber.")

            sucesso_mov = registrar_movimentacao_financeira(
                tipo="ENTRADA",
                valor=valor_final,
                descricao=f"Venda #{venda_id} ({forma_pagamento}) - A RECEBER {numero_parcelas}x",
                origem=forma_pagamento,
                categoria="VENDA_A_RECEBER",
                referencia_id=venda_id,
                referencia_tipo="VENDA",
                conta_bancaria_id=None,
                meio="A_RECEBER",
                caixa_id=None,
                conn_externa=conn
            )

            if not sucesso_mov:
                raise Exception("Falha ao registrar movimentação a receber.")

        # ==========================================
        # OUTRAS FORMAS
        # ==========================================
        else:
            sucesso_mov = registrar_movimentacao_financeira(
                tipo="ENTRADA",
                valor=valor_final,
                descricao=f"Venda #{venda_id} ({forma_pagamento})",
                origem=forma_pagamento,
                categoria="VENDA",
                referencia_id=venda_id,
                referencia_tipo="VENDA",
                conta_bancaria_id=conta_bancaria_id,
                meio="OUTROS",
                caixa_id=None,
                conn_externa=conn
            )

            if not sucesso_mov:
                raise Exception("Falha ao registrar movimentação da venda.")

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("ERRO AO SALVAR VENDA")
        print(erro)
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
        return pd.read_sql("""
            SELECT
                v.id AS pedido,
                c.nome AS cliente,
                p.nome AS produto,
                i.quantidade,
                i.preco_unitario AS valor_unitario,
                i.subtotal,
                v.desconto,
                v.valor_final,
                v.forma_pagamento,
                v.data_venda,
                v.status
            FROM vendas v
            LEFT JOIN clientes c
                ON c.id = v.cliente_id
            LEFT JOIN itens_venda i
                ON i.venda_id = v.id
            LEFT JOIN produtos p
                ON p.id = i.produto_id
            ORDER BY
                v.id DESC,
                p.nome
        """, conn)

    except Exception as erro:
        print("ERRO AO CONSULTAR HISTÓRICO DE VENDAS")
        print(erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# BUSCAR VENDA POR ID
# ==================================================
def buscar_venda_por_id(venda_id):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT *
            FROM vendas
            WHERE id = %s
        """, (venda_id,))

        return cursor.fetchone()

    finally:
        cursor.close()
        conn.close()


# ==================================================
# LISTAR ITENS DA VENDA
# ==================================================
def listar_itens_venda(venda_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql("""
            SELECT
                p.nome,
                i.quantidade,
                i.preco_unitario,
                i.subtotal
            FROM itens_venda i
            INNER JOIN produtos p
                ON p.id = i.produto_id
            WHERE i.venda_id = %s
            ORDER BY p.nome
        """, conn, params=(venda_id,))

    finally:
        conn.close()


# ==================================================
# RESUMO DE VENDAS
# ==================================================
def resumo_vendas():

    conn = conectar()

    if conn is None:
        return {}

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                COUNT(*),
                COALESCE(SUM(valor_final),0),
                COALESCE(AVG(valor_final),0)
            FROM vendas
            WHERE DATE(data_venda)=CURRENT_DATE
              AND COALESCE(status, '') <> 'Cancelada'
        """)

        qtd, total, ticket = cursor.fetchone()

        return {
            "quantidade": qtd,
            "total": float(total),
            "ticket_medio": float(ticket)
        }

    finally:
        cursor.close()
        conn.close()


# ==================================================
# CANCELAR VENDA
# ==================================================
def cancelar_venda(venda_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                produto_id,
                quantidade
            FROM itens_venda
            WHERE venda_id = %s
        """, (venda_id,))

        itens = cursor.fetchall()

        for produto_id, quantidade in itens:

            cursor.execute("""
                UPDATE produtos
                SET estoque = COALESCE(estoque,0) + %s
                WHERE id = %s
            """, (
                quantidade,
                produto_id
            ))

        cursor.execute("""
            UPDATE vendas
            SET status = 'Cancelada'
            WHERE id = %s
        """, (venda_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print(erro)
        return False

    finally:
        cursor.close()
        conn.close()