import pandas as pd

from database.connection import conectar


# ============================================================
# STATUS DE VENDA CONCLUÍDA
# ============================================================

STATUS_CONCLUIDOS = [
    "Concluída",
    "Concluida",
    "Conclu?da",
]


# ============================================================
# CLIENTES GENÉRICOS
#
# Estes registros representam vendas sem identificação
# individual do cliente.
#
# A venda continua contando normalmente.
# O cadastro genérico NÃO conta como:
# - cliente único
# - cliente recorrente
# - cliente novo
# ============================================================

CLIENTES_GENERICOS = [
    "CONSUMIDOR",
    "CONSUMIDOR FINAL",
    "CLIENTE",
    "CLIENTE AVULSO",
]


# ============================================================
# RESUMO MENSAL
# ============================================================

def obter_resumo_mensal(
    data_inicio,
    data_fim,
):
    """
    Retorna por mês:

    - quantidade de vendas/pedidos
    - clientes únicos identificados
    - vendas sem cliente identificado
    - faturamento
    - ticket médio

    IMPORTANTE:

    A unidade de venda é v.id.

    Uma venda com vários produtos continua sendo
    apenas UMA venda.

    Exemplo:

    Pedido 37
    - Agasalho
    - Bermuda
    - Calça

    Resultado:
    1 venda
    1 cliente
    3 itens
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                DATE_TRUNC(
                    'month',
                    v.data_venda
                ) AS mes,

                COUNT(
                    DISTINCT v.id
                ) AS quantidade_vendas,

                COUNT(
                    DISTINCT v.cliente_id
                ) FILTER (
                    WHERE
                        v.cliente_id IS NOT NULL

                        AND NOT (
                            UPPER(
                                TRIM(
                                    COALESCE(
                                        c.nome,
                                        ''
                                    )
                                )
                            ) = ANY(%s)
                        )
                ) AS clientes_unicos,

                COUNT(
                    DISTINCT v.id
                ) FILTER (
                    WHERE
                        v.cliente_id IS NULL

                        OR (
                            UPPER(
                                TRIM(
                                    COALESCE(
                                        c.nome,
                                        ''
                                    )
                                )
                            ) = ANY(%s)
                        )
                ) AS vendas_sem_cliente,

                SUM(
                    COALESCE(
                        v.valor_final,
                        0
                    )
                ) AS faturamento,

                CASE
                    WHEN COUNT(
                        DISTINCT v.id
                    ) > 0

                    THEN
                        SUM(
                            COALESCE(
                                v.valor_final,
                                0
                            )
                        )
                        /
                        COUNT(
                            DISTINCT v.id
                        )

                    ELSE 0
                END AS ticket_medio

            FROM vendas v

            LEFT JOIN clientes c
                ON c.id = v.cliente_id

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)

            GROUP BY
                DATE_TRUNC(
                    'month',
                    v.data_venda
                )

            ORDER BY
                mes
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                CLIENTES_GENERICOS,
                CLIENTES_GENERICOS,
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
            ),
        )

    except Exception as erro:

        print(
            "Erro ao obter resumo mensal:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# CLIENTES RECORRENTES
# ============================================================

def obter_clientes_recorrentes(
    data_inicio,
    data_fim,
):
    """
    Cliente recorrente:

    Cliente identificado que realizou mais de
    uma VENDA/PEDIDO diferente no período.

    Não contamos linhas de itens_venda.

    Exemplo:

    Pedido 37 com 3 produtos = 1 compra.

    Pedido 37 + Pedido 52 = 2 compras.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                v.cliente_id,

                c.nome AS cliente,

                COUNT(
                    DISTINCT v.id
                ) AS quantidade_compras,

                SUM(
                    COALESCE(
                        v.valor_final,
                        0
                    )
                ) AS total_gasto,

                CASE
                    WHEN COUNT(
                        DISTINCT v.id
                    ) > 0

                    THEN
                        SUM(
                            COALESCE(
                                v.valor_final,
                                0
                            )
                        )
                        /
                        COUNT(
                            DISTINCT v.id
                        )

                    ELSE 0
                END AS ticket_medio

            FROM vendas v

            INNER JOIN clientes c
                ON c.id = v.cliente_id

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s

                AND v.cliente_id IS NOT NULL

                AND NOT (
                    UPPER(
                        TRIM(
                            COALESCE(
                                c.nome,
                                ''
                            )
                        )
                    ) = ANY(%s)
                )

                AND v.status = ANY(%s)

            GROUP BY
                v.cliente_id,
                c.nome

            HAVING
                COUNT(
                    DISTINCT v.id
                ) > 1

            ORDER BY
                quantidade_compras DESC,
                total_gasto DESC,
                c.nome
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                data_inicio,
                data_fim,
                CLIENTES_GENERICOS,
                STATUS_CONCLUIDOS,
            ),
        )

    except Exception as erro:

        print(
            "Erro ao obter clientes recorrentes:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# NOVOS CLIENTES
# ============================================================

def obter_novos_clientes(
    data_inicio,
    data_fim,
):
    """
    Novo cliente:

    Cliente identificado cuja PRIMEIRA venda
    concluída registrada no ERP ocorreu dentro
    do período informado.

    Cadastros genéricos como CONSUMIDOR
    são desconsiderados.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            WITH primeira_compra AS (

                SELECT
                    v.cliente_id,

                    MIN(
                        v.data_venda
                    ) AS primeira_compra

                FROM vendas v

                INNER JOIN clientes c
                    ON c.id = v.cliente_id

                WHERE
                    v.cliente_id IS NOT NULL

                    AND NOT (
                        UPPER(
                            TRIM(
                                COALESCE(
                                    c.nome,
                                    ''
                                )
                            )
                        ) = ANY(%s)
                    )

                    AND v.status = ANY(%s)

                GROUP BY
                    v.cliente_id
            )

            SELECT
                pc.cliente_id,

                c.nome AS cliente,

                pc.primeira_compra

            FROM primeira_compra pc

            INNER JOIN clientes c
                ON c.id = pc.cliente_id

            WHERE
                pc.primeira_compra >= %s
                AND pc.primeira_compra < %s

            ORDER BY
                pc.primeira_compra,
                c.nome
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                CLIENTES_GENERICOS,
                STATUS_CONCLUIDOS,
                data_inicio,
                data_fim,
            ),
        )

    except Exception as erro:

        print(
            "Erro ao obter novos clientes:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# TOP PRODUTOS / SERVIÇOS
# ============================================================

def obter_top_produtos(
    data_inicio,
    data_fim,
    limite=3,
):
    """
    Retorna produtos/servi?os mais vendidos
    por volume (quantidade).

    Tamb?m calcula indicadores gerenciais
    de rentabilidade do produto.

    A margem l?quida gerencial estimada considera:

    - custo atual cadastrado do produto;
    - imposto padr?o configurado;
    - taxa de cart?o padr?o somente nas vendas
      realizadas em cart?o.

    O frete padr?o n?o ? abatido automaticamente
    e despesas fixas/operacionais n?o s?o rateadas.

    Portanto, este indicador n?o representa
    lucro l?quido cont?bil da empresa.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        # ==================================================
        # CONFIGURA??ES GERENCIAIS
        # ==================================================

        query_config = """
            SELECT
                COALESCE(
                    imposto_padrao,
                    0
                ) AS imposto_padrao,

                COALESCE(
                    taxa_cartao_padrao,
                    0
                ) AS taxa_cartao_padrao

            FROM configuracoes_financeiras

            ORDER BY id DESC

            LIMIT 1
        """

        df_config = pd.read_sql(
            query_config,
            conn,
        )

        imposto_percentual = 0.0
        taxa_cartao_percentual = 0.0

        if not df_config.empty:

            imposto_percentual = float(
                df_config.iloc[0][
                    "imposto_padrao"
                ]
                or 0
            )

            taxa_cartao_percentual = float(
                df_config.iloc[0][
                    "taxa_cartao_padrao"
                ]
                or 0
            )

        # ==================================================
        # PRODUTOS / VENDAS
        # ==================================================

        query = """
            WITH itens_base AS (

                SELECT
                    v.id AS venda_id,

                    v.forma_pagamento,

                    iv.produto_id,

                    iv.quantidade,

                    p.nome AS produto,

                    p.custo AS custo_atual,

                    CASE

                        WHEN
                            COALESCE(
                                iv.valor_final,
                                0
                            ) = 0

                            AND COALESCE(
                                iv.subtotal,
                                0
                            ) > 0

                            AND COALESCE(
                                iv.desconto,
                                0
                            ) = 0

                        THEN iv.subtotal

                        ELSE
                            COALESCE(
                                iv.valor_final,
                                iv.subtotal,
                                0
                            )

                    END AS valor_liquido_item

                FROM vendas v

                INNER JOIN itens_venda iv
                    ON iv.venda_id = v.id

                INNER JOIN produtos p
                    ON p.id = iv.produto_id

                WHERE
                    v.data_venda >= %s
                    AND v.data_venda < %s
                    AND v.status = ANY(%s)
            )

            SELECT
                produto_id,

                produto,

                SUM(
                    quantidade
                ) AS quantidade_vendida,

                COUNT(
                    DISTINCT venda_id
                ) AS quantidade_pedidos,

                SUM(
                    valor_liquido_item
                ) AS faturamento_produto,

                CASE
                    WHEN SUM(
                        quantidade
                    ) > 0

                    THEN
                        SUM(
                            valor_liquido_item
                        )
                        /
                        SUM(
                            quantidade
                        )

                    ELSE 0
                END AS preco_medio_praticado,

                CASE
                    WHEN COUNT(
                        DISTINCT venda_id
                    ) > 0

                    THEN
                        SUM(
                            valor_liquido_item
                        )
                        /
                        COUNT(
                            DISTINCT venda_id
                        )

                    ELSE 0
                END AS ticket_medio_produto_por_pedido,

                custo_atual,

                CASE
                    WHEN custo_atual IS NOT NULL
                    THEN
                        SUM(
                            quantidade
                            * custo_atual
                        )
                    ELSE 0
                END AS custo_total_estimado,

                CASE
                    WHEN custo_atual IS NOT NULL
                    THEN
                        SUM(
                            valor_liquido_item
                        )
                        -
                        SUM(
                            quantidade
                            * custo_atual
                        )
                    ELSE NULL
                END AS lucro_bruto_estimado,

                CASE
                    WHEN
                        SUM(
                            valor_liquido_item
                        ) > 0
                        AND custo_atual IS NOT NULL

                    THEN
                        (
                            (
                                SUM(
                                    valor_liquido_item
                                )
                                -
                                SUM(
                                    quantidade
                                    * custo_atual
                                )
                            )
                            /
                            SUM(
                                valor_liquido_item
                            )
                        ) * 100

                    ELSE NULL
                END AS margem_bruta_estimada_percentual,

                SUM(
                    CASE
                        WHEN
                            UPPER(
                                COALESCE(
                                    forma_pagamento,
                                    ''
                                )
                            ) LIKE '%%CART%%'

                            OR UPPER(
                                COALESCE(
                                    forma_pagamento,
                                    ''
                                )
                            ) LIKE '%%DEBITO%%'

                            OR UPPER(
                                COALESCE(
                                    forma_pagamento,
                                    ''
                                )
                            ) LIKE '%%D?BITO%%'

                            OR UPPER(
                                COALESCE(
                                    forma_pagamento,
                                    ''
                                )
                            ) LIKE '%%CREDITO%%'

                            OR UPPER(
                                COALESCE(
                                    forma_pagamento,
                                    ''
                                )
                            ) LIKE '%%CR?DITO%%'

                        THEN valor_liquido_item

                        ELSE 0
                    END
                ) AS receita_cartao

            FROM itens_base

            GROUP BY
                produto_id,
                produto,
                custo_atual

            ORDER BY
                quantidade_vendida DESC,
                faturamento_produto DESC,
                produto

            LIMIT %s
        """

        df = pd.read_sql(
            query,
            conn,
            params=(
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
                limite,
            ),
        )

        if df.empty:
            return df

        # ==================================================
        # C?LCULOS GERENCIAIS
        # ==================================================

        df[
            "imposto_percentual_utilizado"
        ] = imposto_percentual

        df[
            "taxa_cartao_percentual_utilizada"
        ] = taxa_cartao_percentual

        df[
            "imposto_estimado"
        ] = (
            df["faturamento_produto"]
            * imposto_percentual
            / 100
        )

        df[
            "taxa_cartao_estimada"
        ] = (
            df["receita_cartao"]
            * taxa_cartao_percentual
            / 100
        )

        df[
            "resultado_gerencial_estimado"
        ] = (
            df["faturamento_produto"]
            - df["custo_total_estimado"]
            - df["imposto_estimado"]
            - df["taxa_cartao_estimada"]
        )

        df[
            "margem_liquida_gerencial_estimada_percentual"
        ] = float("nan")

        mascara = (
            (df["faturamento_produto"] > 0)
            & df["custo_atual"].notna()
            & (df["custo_atual"] > 0)
        )

        df.loc[
            mascara,
            "margem_liquida_gerencial_estimada_percentual"
        ] = (
            df.loc[
                mascara,
                "resultado_gerencial_estimado"
            ]
            /
            df.loc[
                mascara,
                "faturamento_produto"
            ]
            * 100
        )

        return df

    except Exception as erro:

        print(
            "Erro ao obter top produtos:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================

def obter_resumo_geral(
    data_inicio,
    data_fim,
):
    """
    Resumo geral do período.

    A quantidade de clientes considera somente
    clientes efetivamente identificados.

    Cadastros genéricos são classificados como
    venda sem cliente identificado.
    """

    conn = conectar()

    if conn is None:
        return None

    try:

        query = """
            SELECT
                COUNT(
                    DISTINCT v.id
                ) AS quantidade_vendas,

                COUNT(
                    DISTINCT v.cliente_id
                ) FILTER (
                    WHERE
                        v.cliente_id IS NOT NULL

                        AND NOT (
                            UPPER(
                                TRIM(
                                    COALESCE(
                                        c.nome,
                                        ''
                                    )
                                )
                            ) = ANY(%s)
                        )
                ) AS clientes_unicos,

                COUNT(
                    DISTINCT v.id
                ) FILTER (
                    WHERE
                        v.cliente_id IS NULL

                        OR (
                            UPPER(
                                TRIM(
                                    COALESCE(
                                        c.nome,
                                        ''
                                    )
                                )
                            ) = ANY(%s)
                        )
                ) AS vendas_sem_cliente,

                SUM(
                    COALESCE(
                        v.valor_final,
                        0
                    )
                ) AS faturamento,

                CASE
                    WHEN COUNT(
                        DISTINCT v.id
                    ) > 0

                    THEN
                        SUM(
                            COALESCE(
                                v.valor_final,
                                0
                            )
                        )
                        /
                        COUNT(
                            DISTINCT v.id
                        )

                    ELSE 0
                END AS ticket_medio

            FROM vendas v

            LEFT JOIN clientes c
                ON c.id = v.cliente_id

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)
        """

        cursor = conn.cursor()

        cursor.execute(
            query,
            (
                CLIENTES_GENERICOS,
                CLIENTES_GENERICOS,
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
            ),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "quantidade_vendas":
                row[0] or 0,

            "clientes_unicos":
                row[1] or 0,

            "vendas_sem_cliente":
                row[2] or 0,

            "faturamento":
                row[3] or 0,

            "ticket_medio":
                row[4] or 0,
        }

    except Exception as erro:

        print(
            "Erro ao obter resumo geral:",
            erro,
        )

        return None

    finally:

        conn.close()