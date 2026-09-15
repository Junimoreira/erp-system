import pandas as pd

from database.connection import conectar


# ==========================================================
# LISTAR POSIÇÃO DE ESTOQUE
# ==========================================================
def listar_posicao_estoque(
    somente_ativos=True,
    categoria=None,
    situacao=None,
):
    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        filtros = []
        parametros = []

        if somente_ativos:
            filtros.append(
                "COALESCE(p.ativo, TRUE) = TRUE"
            )

        if categoria:
            filtros.append(
                "UPPER(COALESCE(p.categoria, '')) = UPPER(%s)"
            )
            parametros.append(categoria)

        where_sql = ""

        if filtros:
            where_sql = (
                "WHERE "
                + " AND ".join(filtros)
            )

        query = f"""
            SELECT
                p.id,
                p.nome,
                p.codigo_barras,
                p.sku,
                p.marca,
                p.categoria,
                p.tamanho,
                p.unidade,

                COALESCE(
                    p.estoque,
                    0
                ) AS estoque,

                COALESCE(
                    p.estoque_minimo,
                    0
                ) AS estoque_minimo,

                COALESCE(
                    p.custo,
                    0
                ) AS custo,

                COALESCE(
                    p.preco,
                    0
                ) AS preco,

                CASE
                    WHEN COALESCE(p.estoque, 0) > 0
                     AND COALESCE(p.custo, 0) > 0
                    THEN
                        COALESCE(p.estoque, 0)
                        * COALESCE(p.custo, 0)
                    ELSE 0
                END AS valor_estoque_custo,

                CASE
                    WHEN COALESCE(p.estoque, 0) > 0
                     AND COALESCE(p.preco, 0) > 0
                    THEN
                        COALESCE(p.estoque, 0)
                        * COALESCE(p.preco, 0)
                    ELSE 0
                END AS valor_estoque_venda,

                CASE
                    WHEN COALESCE(p.estoque, 0) <= 0
                    THEN 'SEM ESTOQUE'

                    WHEN COALESCE(p.estoque_minimo, 0) <= 0
                    THEN 'SEM MÍNIMO'

                    WHEN
                        COALESCE(p.estoque, 0)
                        < COALESCE(p.estoque_minimo, 0)
                    THEN 'ABAIXO DO MÍNIMO'

                    WHEN
                        COALESCE(p.estoque, 0)
                        = COALESCE(p.estoque_minimo, 0)
                    THEN 'NO MÍNIMO'

                    ELSE 'NORMAL'
                END AS situacao_estoque,

                CASE
                    WHEN p.custo IS NULL
                      OR p.custo <= 0
                    THEN FALSE
                    ELSE TRUE
                END AS custo_valido,

                CASE
                    WHEN p.preco IS NULL
                      OR p.preco <= 0
                    THEN FALSE
                    ELSE TRUE
                END AS preco_valido,

                p.localizacao,

                COALESCE(
                    p.ativo,
                    TRUE
                ) AS ativo

            FROM produtos p

            {where_sql}

            ORDER BY
                CASE
                    WHEN COALESCE(p.estoque, 0) <= 0
                    THEN 1

                    WHEN
                        COALESCE(p.estoque, 0) > 0
                        AND COALESCE(p.estoque_minimo, 0) > 0
                        AND COALESCE(p.estoque, 0)
                            < COALESCE(p.estoque_minimo, 0)
                    THEN 2

                    WHEN
                        COALESCE(p.estoque, 0) > 0
                        AND COALESCE(p.estoque_minimo, 0) > 0
                        AND COALESCE(p.estoque, 0)
                            = COALESCE(p.estoque_minimo, 0)
                    THEN 3

                    WHEN
                        COALESCE(p.estoque, 0) > 0
                        AND COALESCE(p.estoque_minimo, 0) <= 0
                    THEN 4

                    ELSE 5
                END,
                p.nome
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=parametros,
        )

        if (
            situacao
            and not df.empty
        ):
            df = df[
                df["situacao_estoque"]
                == situacao
            ].copy()

        return df.reset_index(
            drop=True
        )

    finally:
        conn.close()


# ==========================================================
# RESUMO DO ESTOQUE
# ==========================================================
def obter_resumo_estoque():

    conn = conectar()

    if conn is None:
        return {}

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                -- PRODUTOS ATIVOS
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                ),

                -- PRODUTOS INATIVOS
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = FALSE
                ),

                -- PRODUTOS COM ESTOQUE POSITIVO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                ),

                -- SEM ESTOQUE
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) <= 0
                ),

                -- ABAIXO DO MÍNIMO
                -- SOMENTE QUANDO AINDA EXISTE ESTOQUE
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) > 0
                      AND COALESCE(estoque, 0)
                          < COALESCE(estoque_minimo, 0)
                ),

                -- EXATAMENTE NO MÍNIMO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) > 0
                      AND COALESCE(estoque, 0)
                          = COALESCE(estoque_minimo, 0)
                ),

                -- COM ESTOQUE, MAS SEM MÍNIMO DEFINIDO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) <= 0
                ),

                -- ESTOQUE NORMAL
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) > 0
                      AND COALESCE(estoque, 0)
                          > COALESCE(estoque_minimo, 0)
                ),

                -- SEM CUSTO VÁLIDO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND (
                            custo IS NULL
                            OR custo <= 0
                      )
                ),

                -- SEM PREÇO VÁLIDO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND (
                            preco IS NULL
                            OR preco <= 0
                      )
                ),

                -- QUANTIDADE TOTAL EM ESTOQUE
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(ativo, TRUE) = TRUE
                             AND COALESCE(estoque, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR DO ESTOQUE A CUSTO CONHECIDO
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(ativo, TRUE) = TRUE
                             AND COALESCE(estoque, 0) > 0
                             AND COALESCE(custo, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(custo, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR POTENCIAL DE VENDA
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(ativo, TRUE) = TRUE
                             AND COALESCE(estoque, 0) > 0
                             AND COALESCE(preco, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(preco, 0)
                            ELSE 0
                        END
                    ),
                    0
                )

            FROM produtos
            """
        )

        linha = cursor.fetchone()

        return {
            "produtos_ativos": linha[0],
            "produtos_inativos": linha[1],
            "produtos_com_estoque": linha[2],
            "produtos_sem_estoque": linha[3],
            "produtos_abaixo_minimo": linha[4],
            "produtos_no_minimo": linha[5],
            "produtos_sem_minimo": linha[6],
            "produtos_normais": linha[7],
            "produtos_sem_custo": linha[8],
            "produtos_sem_preco": linha[9],
            "quantidade_total_estoque": linha[10],
            "valor_custo_conhecido": linha[11],
            "valor_potencial_venda": linha[12],
        }

    finally:
        conn.close()


# ==========================================================
# LISTAR CATEGORIAS
# ==========================================================
def listar_categorias_produtos():

    conn = conectar()

    if conn is None:
        return []

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT
                TRIM(categoria)

            FROM produtos

            WHERE COALESCE(ativo, TRUE) = TRUE
              AND categoria IS NOT NULL
              AND TRIM(categoria) <> ''

            ORDER BY
                TRIM(categoria)
            """
        )

        return [
            linha[0]
            for linha in cursor.fetchall()
        ]

    finally:
        conn.close()


# ==========================================================
# CONFERÊNCIA DO RELATÓRIO
# ==========================================================
def conferir_posicao_estoque():

    conn = conectar()

    if conn is None:
        return {}

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                -- QUANTIDADE DE PRODUTOS ATIVOS
                COUNT(*),

                -- QUANTIDADE TOTAL DE UNIDADES
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(estoque, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR A CUSTO CONHECIDO
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(estoque, 0) > 0
                             AND COALESCE(custo, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(custo, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR POTENCIAL DE VENDA
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(estoque, 0) > 0
                             AND COALESCE(preco, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(preco, 0)
                            ELSE 0
                        END
                    ),
                    0
                )

            FROM produtos

            WHERE COALESCE(ativo, TRUE) = TRUE
            """
        )

        (
            quantidade_produtos,
            quantidade_estoque,
            valor_custo,
            valor_venda,
        ) = cursor.fetchone()

        return {
            "quantidade_produtos": quantidade_produtos,
            "quantidade_estoque": quantidade_estoque,
            "valor_custo_conhecido": valor_custo,
            "valor_potencial_venda": valor_venda,
        }

    finally:
        conn.close()