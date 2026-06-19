import pandas as pd
from database.connection import conectar


def listar_aniversariantes_mes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                id,
                nome,
                telefone,
                email,
                cidade,
                data_nascimento
            FROM clientes
            WHERE data_nascimento IS NOT NULL
              AND EXTRACT(MONTH FROM data_nascimento) = EXTRACT(MONTH FROM CURRENT_DATE)
            ORDER BY EXTRACT(DAY FROM data_nascimento), nome
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar_aniversariantes_mes:", erro)
        return pd.DataFrame()

    finally:
        conn.close()

def listar_clientes_inativos(dias=90):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                c.id,
                c.nome,
                c.telefone,
                c.email,
                c.cidade,
                MAX(v.data_venda) AS ultima_compra,
                CURRENT_DATE - DATE(MAX(v.data_venda)) AS dias_sem_comprar,
                COALESCE(SUM(v.valor_final), 0) AS total_comprado,
                COUNT(v.id) AS quantidade_compras
            FROM clientes c
            LEFT JOIN vendas v
                ON v.cliente_id = c.id
                AND UPPER(COALESCE(v.status, '')) <> 'CANCELADA'
            GROUP BY
                c.id,
                c.nome,
                c.telefone,
                c.email,
                c.cidade
            HAVING
                MAX(v.data_venda) IS NULL
                OR CURRENT_DATE - DATE(MAX(v.data_venda)) >= %s
            ORDER BY
                dias_sem_comprar DESC NULLS FIRST,
                c.nome
        """

        return pd.read_sql(query, conn, params=[dias])

    except Exception as erro:
        print("Erro listar_clientes_inativos:", erro)
        return pd.DataFrame()

    finally:
        conn.close()

def listar_top_clientes(limit=20):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                c.id,
                c.nome,
                c.telefone,
                c.email,
                c.cidade,
                COUNT(v.id) AS quantidade_compras,
                COALESCE(SUM(v.valor_final), 0) AS total_comprado,
                COALESCE(AVG(v.valor_final), 0) AS ticket_medio,
                MAX(v.data_venda) AS ultima_compra
            FROM clientes c
            INNER JOIN vendas v
                ON v.cliente_id = c.id
            WHERE UPPER(COALESCE(v.status, '')) <> 'CANCELADA'
            GROUP BY
                c.id,
                c.nome,
                c.telefone,
                c.email,
                c.cidade
            ORDER BY total_comprado DESC
            LIMIT %s
        """

        return pd.read_sql(query, conn, params=[limit])

    except Exception as erro:
        print("Erro listar_top_clientes:", erro)
        return pd.DataFrame()

    finally:
        conn.close()