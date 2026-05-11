from database.connection import conectar
import pandas as pd


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
        SELECT id, nome, preco, estoque
        FROM produtos
        ORDER BY nome
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# CRIAR VENDA
# ==================================================

def criar_venda(cliente_id, total):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        INSERT INTO vendas (cliente_id, total)
        VALUES (%s, %s)
        RETURNING id
    """

    cursor.execute(
        query,
        (
            int(cliente_id),
            float(total)
        )
    )

    venda_id = cursor.fetchone()[0]

    conn.commit()

    cursor.close()
    conn.close()

    return venda_id


# ==================================================
# ADICIONAR ITEM VENDA
# ==================================================

def adicionar_item_venda(
    venda_id,
    produto_id,
    quantidade,
    preco_unitario,
    subtotal
):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        INSERT INTO itens_venda (
            venda_id,
            produto_id,
            quantidade,
            preco_unitario,
            subtotal
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            venda_id,
            produto_id,
            quantidade,
            preco_unitario,
            subtotal
        )
    )

    # ==========================================
    # BAIXAR ESTOQUE
    # ==========================================

    query_estoque = """
        UPDATE produtos
        SET estoque = estoque - %s
        WHERE id = %s
    """

    cursor.execute(
        query_estoque,
        (
            quantidade,
            produto_id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# LANÇAR FINANCEIRO
# ==================================================

def lancar_financeiro_venda(total):

    conn = conectar()

    cursor = conn.cursor()

    query = """
        INSERT INTO financeiro (
            descricao,
            valor,
            tipo,
            categoria,
            data_lancamento
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            CURRENT_DATE
        )
    """

    cursor.execute(
        query,
        (
            "Venda realizada",
            total,
            "Entrada",
            "Vendas"
        )
    )

    conn.commit()

    cursor.close()
    conn.close()


# ==================================================
# LISTAR VENDAS
# ==================================================

def listar_vendas():

    conn = conectar()

    query = """
        SELECT
            vendas.id,
            clientes.nome AS cliente,
            vendas.total,
            vendas.data
        FROM vendas
        LEFT JOIN clientes
            ON vendas.cliente_id = clientes.id
        ORDER BY vendas.id DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df