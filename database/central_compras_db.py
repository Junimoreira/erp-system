import pandas as pd
from database.connection import conectar


def produtos_parados(dias=180):
    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                p.id,
                p.nome,
                p.estoque,
                p.custo,
                COALESCE(p.estoque, 0) * COALESCE(p.custo, 0) AS capital_parado,
                MAX(v.data_venda) AS ultima_venda,
                CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) AS dias_sem_venda
            FROM produtos p
            LEFT JOIN itens_venda iv ON iv.produto_id = p.id
            LEFT JOIN vendas v ON v.id = iv.venda_id
            WHERE COALESCE(p.estoque, 0) > 0
            GROUP BY p.id, p.nome, p.estoque, p.custo, p.data_cadastro
            HAVING CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) >= %s
            ORDER BY dias_sem_venda DESC
        """

        return pd.read_sql(query, conn, params=(dias,))

    except Exception as erro:
        print("Erro produtos_parados:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


def resumo_idade_estoque():
    conn = conectar()
    if conn is None:
        return {
            "90": 0,
            "180": 0,
            "270": 0,
            "365": 0
        }

    cursor = conn.cursor()

    try:
        cursor.execute("""
            WITH base AS (
                SELECT
                    p.id,
                    CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) AS dias_sem_venda
                FROM produtos p
                LEFT JOIN itens_venda iv ON iv.produto_id = p.id
                LEFT JOIN vendas v ON v.id = iv.venda_id
                WHERE COALESCE(p.estoque, 0) > 0
                GROUP BY p.id, p.data_cadastro
            )
            SELECT
                COUNT(*) FILTER (WHERE dias_sem_venda >= 90),
                COUNT(*) FILTER (WHERE dias_sem_venda >= 180),
                COUNT(*) FILTER (WHERE dias_sem_venda >= 270),
                COUNT(*) FILTER (WHERE dias_sem_venda >= 365)
            FROM base
        """)

        resultado = cursor.fetchone()

        return {
            "90": int(resultado[0] or 0),
            "180": int(resultado[1] or 0),
            "270": int(resultado[2] or 0),
            "365": int(resultado[3] or 0)
        }

    except Exception as erro:
        print("Erro resumo_idade_estoque:", erro)
        return {
            "90": 0,
            "180": 0,
            "270": 0,
            "365": 0
        }

    finally:
        cursor.close()
        conn.close()


def capital_parado_total():
    conn = conectar()
    if conn is None:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(COALESCE(estoque, 0) * COALESCE(custo, 0)), 0)
            FROM produtos
            WHERE COALESCE(estoque, 0) > 0
        """)

        resultado = cursor.fetchone()
        return float(resultado[0] or 0)

    except Exception as erro:
        print("Erro capital_parado_total:", erro)
        return 0

    finally:
        cursor.close()
        conn.close()


def produtos_mais_vendidos(limite=20):
    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                p.id,
                p.nome,
                SUM(iv.quantidade) AS quantidade_vendida,
                SUM(iv.subtotal) AS faturamento
            FROM itens_venda iv
            INNER JOIN vendas v ON v.id = iv.venda_id
            INNER JOIN produtos p ON p.id = iv.produto_id
            WHERE UPPER(COALESCE(v.status, '')) <> 'CANCELADA'
            GROUP BY p.id, p.nome
            ORDER BY quantidade_vendida DESC
            LIMIT %s
        """

        return pd.read_sql(query, conn, params=(limite,))

    except Exception as erro:
        print("Erro produtos_mais_vendidos:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


def produtos_menor_giro(limite=20):
    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                p.id,
                p.nome,
                COALESCE(p.estoque, 0) AS estoque,
                COALESCE(SUM(iv.quantidade), 0) AS quantidade_vendida,
                COALESCE(p.custo, 0) AS custo,
                COALESCE(p.estoque, 0) * COALESCE(p.custo, 0) AS capital_parado
            FROM produtos p
            LEFT JOIN itens_venda iv ON iv.produto_id = p.id
            LEFT JOIN vendas v ON v.id = iv.venda_id
                AND UPPER(COALESCE(v.status, '')) <> 'CANCELADA'
            WHERE COALESCE(p.estoque, 0) > 0
            GROUP BY p.id, p.nome, p.estoque, p.custo
            ORDER BY quantidade_vendida ASC, capital_parado DESC
            LIMIT %s
        """

        return pd.read_sql(query, conn, params=(limite,))

    except Exception as erro:
        print("Erro produtos_menor_giro:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


def sugestoes_promocao(dias=365):
    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                p.id,
                p.nome,
                COALESCE(p.estoque, 0) AS estoque,
                COALESCE(p.custo, 0) AS custo,
                COALESCE(p.preco, 0) AS preco_atual,
                COALESCE(p.estoque, 0) * COALESCE(p.custo, 0) AS capital_parado,
                MAX(v.data_venda) AS ultima_venda,
                CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) AS dias_sem_venda,
                CASE
                    WHEN CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) >= 365
                        THEN 'Promoção forte / campanha imediata'
                    WHEN CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) >= 270
                        THEN 'Divulgar nas redes e vitrine'
                    WHEN CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) >= 180
                        THEN 'Melhorar exposição na loja'
                    ELSE 'Acompanhar'
                END AS sugestao
            FROM produtos p
            LEFT JOIN itens_venda iv ON iv.produto_id = p.id
            LEFT JOIN vendas v ON v.id = iv.venda_id
            WHERE COALESCE(p.estoque, 0) > 0
            GROUP BY p.id, p.nome, p.estoque, p.custo, p.preco, p.data_cadastro
            HAVING CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date) >= %s
            ORDER BY dias_sem_venda DESC, capital_parado DESC
        """

        return pd.read_sql(query, conn, params=(dias,))

    except Exception as erro:
        print("Erro sugestoes_promocao:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


def historico_custos_produtos(limite=100):
    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                hc.id,
                p.nome AS produto,
                f.razao_social AS fornecedor,
                hc.data_compra,
                hc.custo_anterior,
                hc.custo_novo,
                hc.quantidade,
                hc.numero_nfe
            FROM historico_custos hc
            LEFT JOIN produtos p ON p.id = hc.produto_id
            LEFT JOIN fornecedores f ON f.id = hc.fornecedor_id
            ORDER BY hc.data_compra DESC
            LIMIT %s
        """

        return pd.read_sql(query, conn, params=(limite,))

    except Exception as erro:
        print("Erro historico_custos_produtos:", erro)
        return pd.DataFrame()

    finally:
        conn.close()