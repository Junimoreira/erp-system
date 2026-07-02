import pandas as pd
from database.connection import conectar


def recalcular_inteligencia_estoque():

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM inteligencia_estoque;")

        cursor.execute("""
            INSERT INTO inteligencia_estoque (
                produto_id,
                ultima_compra,
                ultima_venda,
                dias_sem_venda,
                quantidade_vendida_ano,
                faturamento_ano,
                estoque_atual,
                custo_atual,
                preco_atual,
                capital_parado,
                margem_estimada,
                classificacao_giro,
                situacao,
                sugestao,
                score_saude,
                classificacao_saude,
                atualizado_em
            )
            WITH base AS (
                SELECT
                    p.id AS produto_id,
                    MAX(c.data_compra) AS ultima_compra,
                    MAX(v.data_venda) AS ultima_venda,

                    COALESCE(
                        CURRENT_DATE - COALESCE(MAX(v.data_venda)::date, p.data_cadastro::date),
                        0
                    ) AS dias_sem_venda,

                    COALESCE(SUM(
                        CASE
                            WHEN v.data_venda >= CURRENT_DATE - INTERVAL '365 days'
                                 AND UPPER(COALESCE(v.status, '')) <> 'CANCELADA'
                            THEN iv.quantidade
                            ELSE 0
                        END
                    ), 0) AS quantidade_vendida_ano,

                    COALESCE(SUM(
                        CASE
                            WHEN v.data_venda >= CURRENT_DATE - INTERVAL '365 days'
                                 AND UPPER(COALESCE(v.status, '')) <> 'CANCELADA'
                            THEN iv.subtotal
                            ELSE 0
                        END
                    ), 0) AS faturamento_ano,

                    COALESCE(p.estoque, 0) AS estoque_atual,
                    COALESCE(p.custo, 0) AS custo_atual,
                    COALESCE(p.preco, 0) AS preco_atual,
                    COALESCE(p.estoque, 0) * COALESCE(p.custo, 0) AS capital_parado,

                    CASE
                        WHEN COALESCE(p.custo, 0) > 0
                        THEN ROUND(
                            ((COALESCE(p.preco, 0) - COALESCE(p.custo, 0))
                            / COALESCE(p.custo, 0)) * 100,
                            2
                        )
                        ELSE 0
                    END AS margem_estimada

                FROM produtos p

                LEFT JOIN itens_compra ic
                    ON ic.produto_id = p.id

                LEFT JOIN compras c
                    ON c.id = ic.compra_id

                LEFT JOIN itens_venda iv
                    ON iv.produto_id = p.id

                LEFT JOIN vendas v
                    ON v.id = iv.venda_id

                WHERE COALESCE(p.ativo, true) = true

                GROUP BY
                    p.id,
                    p.data_cadastro,
                    p.estoque,
                    p.custo,
                    p.preco
            ),
            score AS (
                SELECT
                    *,

                    (
                        CASE
                            WHEN quantidade_vendida_ano >= 50 THEN 35
                            WHEN quantidade_vendida_ano >= 25 THEN 28
                            WHEN quantidade_vendida_ano >= 10 THEN 20
                            WHEN quantidade_vendida_ano >= 5 THEN 10
                            ELSE 0
                        END
                        +
                        CASE
                            WHEN dias_sem_venda <= 30 THEN 25
                            WHEN dias_sem_venda <= 90 THEN 18
                            WHEN dias_sem_venda <= 180 THEN 10
                            WHEN dias_sem_venda <= 365 THEN 5
                            ELSE 0
                        END
                        +
                        CASE
                            WHEN margem_estimada >= 80 THEN 20
                            WHEN margem_estimada >= 50 THEN 15
                            WHEN margem_estimada >= 30 THEN 10
                            WHEN margem_estimada >= 15 THEN 5
                            ELSE 0
                        END
                        +
                        CASE
                            WHEN faturamento_ano >= 5000 THEN 10
                            WHEN faturamento_ano >= 2000 THEN 7
                            WHEN faturamento_ano >= 500 THEN 4
                            WHEN faturamento_ano > 0 THEN 2
                            ELSE 0
                        END
                        +
                        CASE
                            WHEN capital_parado <= 100 THEN 10
                            WHEN capital_parado <= 500 THEN 7
                            WHEN capital_parado <= 1500 THEN 4
                            WHEN capital_parado <= 3000 THEN 2
                            ELSE 0
                        END
                    ) AS score_saude

                FROM base
            )
            SELECT
                produto_id,
                ultima_compra,
                ultima_venda,
                dias_sem_venda,
                quantidade_vendida_ano,
                faturamento_ano,
                estoque_atual,
                custo_atual,
                preco_atual,
                capital_parado,
                margem_estimada,

                CASE
                    WHEN score_saude >= 70 THEN 'ALTO GIRO'
                    WHEN score_saude >= 40 THEN 'MÉDIO GIRO'
                    ELSE 'BAIXO GIRO'
                END AS classificacao_giro,

                CASE
                    WHEN score_saude >= 85 THEN 'EXCELENTE'
                    WHEN score_saude >= 70 THEN 'SAUDÁVEL'
                    WHEN score_saude >= 50 THEN 'ATENÇÃO'
                    WHEN score_saude >= 30 THEN 'BAIXO DESEMPENHO'
                    ELSE 'CRÍTICO'
                END AS situacao,

                CASE
                    WHEN score_saude >= 85 THEN 'Produto excelente. Manter acompanhamento e evitar ruptura de estoque.'
                    WHEN score_saude >= 70 THEN 'Produto saudável. Avaliar reposição conforme estoque mínimo.'
                    WHEN score_saude >= 50 THEN 'Produto em atenção. Acompanhar vendas e exposição.'
                    WHEN score_saude >= 30 THEN 'Produto com baixo desempenho. Avaliar promoção leve ou divulgação.'
                    ELSE 'Produto crítico. Avaliar promoção forte, kit, vitrine ou campanha nas redes.'
                END AS sugestao,

                score_saude,

                CASE
                    WHEN score_saude >= 85 THEN '🟢 Excelente'
                    WHEN score_saude >= 70 THEN '🔵 Saudável'
                    WHEN score_saude >= 50 THEN '🟡 Atenção'
                    WHEN score_saude >= 30 THEN '🟠 Baixo desempenho'
                    ELSE '🔴 Crítico'
                END AS classificacao_saude,

                CURRENT_TIMESTAMP
            FROM score;
        """)

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro recalcular_inteligencia_estoque:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


def listar_inteligencia_estoque():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                ie.produto_id,
                p.nome AS produto,
                ie.classificacao_saude,
                ie.score_saude,
                ie.classificacao_giro,
                ie.situacao,
                ie.dias_sem_venda,
                ie.quantidade_vendida_ano,
                ie.faturamento_ano,
                ie.estoque_atual,
                ie.custo_atual,
                ie.preco_atual,
                ie.capital_parado,
                ie.margem_estimada,
                ie.sugestao,
                ie.ultima_compra,
                ie.ultima_venda,
                ie.atualizado_em
            FROM inteligencia_estoque ie
            INNER JOIN produtos p
                ON p.id = ie.produto_id
            ORDER BY
                ie.score_saude ASC,
                ie.capital_parado DESC,
                ie.dias_sem_venda DESC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar_inteligencia_estoque:", erro)
        return pd.DataFrame()

    finally:
        conn.close()