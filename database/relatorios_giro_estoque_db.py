import pandas as pd

from database.connection import conectar


STATUS_CONCLUIDOS = [
    "Concluída",
    "Concluida",
    "Conclu?da",
]


# ============================================================
# LISTAR GIRO E INTELIGENCIA DE ESTOQUE
# ============================================================

def listar_giro_estoque():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            WITH vendas_validas AS (
                SELECT
                    v.id AS venda_id,
                    v.data_venda,

                    COALESCE(
                        v.valor_final,
                        v.valor_total,
                        0
                    ) AS valor_final_venda,

                    COALESCE(
                        SUM(
                            COALESCE(
                                iv.subtotal,
                                0
                            )
                        ),
                        0
                    ) AS subtotal_venda

                FROM vendas v

                INNER JOIN itens_venda iv
                    ON iv.venda_id = v.id

                WHERE v.status = ANY(%s)

                GROUP BY
                    v.id,
                    v.data_venda,
                    v.valor_final,
                    v.valor_total
            ),

            periodo_historico AS (
                SELECT
                    MIN(data_venda)::date
                        AS inicio_historico,

                    MAX(data_venda)::date
                        AS fim_historico

                FROM vendas_validas
            ),

            itens_rateados AS (
                SELECT
                    iv.id AS item_id,
                    iv.produto_id,
                    iv.venda_id,
                    vv.data_venda,

                    COALESCE(
                        iv.quantidade,
                        0
                    ) AS quantidade,

                    COALESCE(
                        iv.subtotal,
                        0
                    ) AS faturamento_bruto_item,

                    CASE
                        WHEN COALESCE(
                            vv.subtotal_venda,
                            0
                        ) > 0
                        THEN
                            (
                                COALESCE(
                                    iv.subtotal,
                                    0
                                )
                                /
                                vv.subtotal_venda
                            )
                            *
                            vv.valor_final_venda

                        ELSE 0
                    END AS faturamento_liquido_rateado

                FROM itens_venda iv

                INNER JOIN vendas_validas vv
                    ON vv.venda_id = iv.venda_id
            ),

            itens_com_desconto AS (
                SELECT
                    item_id,
                    produto_id,
                    venda_id,
                    data_venda,
                    quantidade,
                    faturamento_bruto_item,
                    faturamento_liquido_rateado,

                    (
                        faturamento_bruto_item
                        -
                        faturamento_liquido_rateado
                    ) AS desconto_rateado

                FROM itens_rateados
            ),

            resumo_vendas AS (
                SELECT
                    produto_id,

                    MIN(data_venda)
                        AS primeira_venda,

                    MAX(data_venda)
                        AS ultima_venda,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '30 days'
                                THEN quantidade

                                ELSE 0
                            END
                        ),
                        0
                    ) AS vendas_30_dias,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '90 days'
                                THEN quantidade

                                ELSE 0
                            END
                        ),
                        0
                    ) AS vendas_90_dias,

                    COALESCE(
                        SUM(quantidade),
                        0
                    ) AS vendas_historico,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '30 days'
                                THEN faturamento_bruto_item

                                ELSE 0
                            END
                        ),
                        0
                    ) AS faturamento_bruto_30_dias,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '90 days'
                                THEN faturamento_bruto_item

                                ELSE 0
                            END
                        ),
                        0
                    ) AS faturamento_bruto_90_dias,

                    COALESCE(
                        SUM(
                            faturamento_bruto_item
                        ),
                        0
                    ) AS faturamento_bruto_historico,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '30 days'
                                THEN desconto_rateado

                                ELSE 0
                            END
                        ),
                        0
                    ) AS desconto_30_dias,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '90 days'
                                THEN desconto_rateado

                                ELSE 0
                            END
                        ),
                        0
                    ) AS desconto_90_dias,

                    COALESCE(
                        SUM(
                            desconto_rateado
                        ),
                        0
                    ) AS desconto_historico,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '30 days'
                                THEN faturamento_liquido_rateado

                                ELSE 0
                            END
                        ),
                        0
                    ) AS faturamento_30_dias,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN data_venda
                                    >= CURRENT_DATE
                                    - INTERVAL '90 days'
                                THEN faturamento_liquido_rateado

                                ELSE 0
                            END
                        ),
                        0
                    ) AS faturamento_90_dias,

                    COALESCE(
                        SUM(
                            faturamento_liquido_rateado
                        ),
                        0
                    ) AS faturamento_historico

                FROM itens_com_desconto

                GROUP BY produto_id
            ),

            base AS (
                SELECT
                    p.id AS produto_id,
                    p.codigo_barras,
                    p.sku,
                    p.nome AS produto,
                    p.categoria,
                    p.marca,
                    p.tamanho,

                    COALESCE(
                        p.estoque,
                        0
                    ) AS estoque_atual,

                    COALESCE(
                        p.estoque_minimo,
                        0
                    ) AS estoque_minimo,

                    COALESCE(
                        p.custo,
                        0
                    ) AS custo_atual,

                    COALESCE(
                        p.preco,
                        0
                    ) AS preco_atual,

                    CASE
                        WHEN COALESCE(
                            p.custo,
                            0
                        ) > 0
                        THEN TRUE

                        ELSE FALSE
                    END AS custo_conhecido,

                    CASE
                        WHEN COALESCE(
                            p.estoque_minimo,
                            0
                        ) > 0
                        THEN TRUE

                        ELSE FALSE
                    END AS minimo_cadastrado,

                    CASE
                        WHEN COALESCE(
                            p.custo,
                            0
                        ) > 0
                        AND COALESCE(
                            p.estoque,
                            0
                        ) > 0
                        THEN
                            p.custo
                            *
                            p.estoque

                        ELSE 0
                    END AS valor_estoque_custo,

                    CASE
                        WHEN COALESCE(
                            p.preco,
                            0
                        ) > 0
                        AND COALESCE(
                            p.estoque,
                            0
                        ) > 0
                        THEN
                            p.preco
                            *
                            p.estoque

                        ELSE 0
                    END AS valor_estoque_venda,

                    CASE
                        WHEN COALESCE(
                            p.preco,
                            0
                        ) > 0
                        AND COALESCE(
                            p.custo,
                            0
                        ) > 0
                        THEN
                            ROUND(
                                (
                                    (
                                        p.preco
                                        -
                                        p.custo
                                    )
                                    /
                                    p.preco
                                )
                                * 100,
                                2
                            )

                        ELSE NULL
                    END AS margem_bruta_percentual,

                    ph.inicio_historico,
                    ph.fim_historico,

                    rv.primeira_venda,
                    rv.ultima_venda,

                    CASE
                        WHEN
                            p.data_cadastro IS NOT NULL
                            AND ph.inicio_historico IS NOT NULL
                        THEN
                            GREATEST(
                                p.data_cadastro::date,
                                ph.inicio_historico
                            )

                        WHEN p.data_cadastro IS NOT NULL
                        THEN
                            p.data_cadastro::date

                        ELSE
                            ph.inicio_historico
                    END AS data_inicio_observacao,

                    CASE
                        WHEN rv.ultima_venda IS NOT NULL
                        THEN
                            CURRENT_DATE
                            -
                            rv.ultima_venda::date

                        WHEN ph.inicio_historico IS NOT NULL
                        THEN
                            CURRENT_DATE
                            -
                            GREATEST(
                                COALESCE(
                                    p.data_cadastro::date,
                                    ph.inicio_historico
                                ),
                                ph.inicio_historico
                            )

                        ELSE NULL
                    END AS dias_sem_venda,

                    COALESCE(
                        rv.vendas_30_dias,
                        0
                    ) AS vendas_30_dias,

                    COALESCE(
                        rv.vendas_90_dias,
                        0
                    ) AS vendas_90_dias,

                    COALESCE(
                        rv.vendas_historico,
                        0
                    ) AS vendas_historico,

                    COALESCE(
                        rv.faturamento_bruto_30_dias,
                        0
                    ) AS faturamento_bruto_30_dias,

                    COALESCE(
                        rv.faturamento_bruto_90_dias,
                        0
                    ) AS faturamento_bruto_90_dias,

                    COALESCE(
                        rv.faturamento_bruto_historico,
                        0
                    ) AS faturamento_bruto_historico,

                    COALESCE(
                        rv.desconto_30_dias,
                        0
                    ) AS desconto_30_dias,

                    COALESCE(
                        rv.desconto_90_dias,
                        0
                    ) AS desconto_90_dias,

                    COALESCE(
                        rv.desconto_historico,
                        0
                    ) AS desconto_historico,

                    COALESCE(
                        rv.faturamento_30_dias,
                        0
                    ) AS faturamento_30_dias,

                    COALESCE(
                        rv.faturamento_90_dias,
                        0
                    ) AS faturamento_90_dias,

                    COALESCE(
                        rv.faturamento_historico,
                        0
                    ) AS faturamento_historico,

                    CASE
                        WHEN COALESCE(
                            rv.faturamento_bruto_30_dias,
                            0
                        ) > 0
                        THEN
                            ROUND(
                                (
                                    COALESCE(
                                        rv.desconto_30_dias,
                                        0
                                    )
                                    /
                                    rv.faturamento_bruto_30_dias
                                )
                                * 100,
                                2
                            )

                        ELSE 0
                    END AS percentual_desconto_30_dias,

                    CASE
                        WHEN COALESCE(
                            rv.faturamento_bruto_90_dias,
                            0
                        ) > 0
                        THEN
                            ROUND(
                                (
                                    COALESCE(
                                        rv.desconto_90_dias,
                                        0
                                    )
                                    /
                                    rv.faturamento_bruto_90_dias
                                )
                                * 100,
                                2
                            )

                        ELSE 0
                    END AS percentual_desconto_90_dias,

                    CASE
                        WHEN COALESCE(
                            rv.faturamento_bruto_historico,
                            0
                        ) > 0
                        THEN
                            ROUND(
                                (
                                    COALESCE(
                                        rv.desconto_historico,
                                        0
                                    )
                                    /
                                    rv.faturamento_bruto_historico
                                )
                                * 100,
                                2
                            )

                        ELSE 0
                    END AS percentual_desconto_historico,

                    ROUND(
                        COALESCE(
                            rv.vendas_90_dias,
                            0
                        )
                        / 3.0,
                        2
                    ) AS media_mensal_90_dias,

                    CASE
                        WHEN COALESCE(
                            rv.vendas_90_dias,
                            0
                        ) > 0
                        THEN
                            ROUND(
                                COALESCE(
                                    p.estoque,
                                    0
                                )
                                /
                                (
                                    COALESCE(
                                        rv.vendas_90_dias,
                                        0
                                    )
                                    / 3.0
                                ),
                                2
                            )

                        ELSE NULL
                    END AS cobertura_meses

                FROM produtos p

                CROSS JOIN periodo_historico ph

                LEFT JOIN resumo_vendas rv
                    ON rv.produto_id = p.id

                WHERE COALESCE(
                    p.ativo,
                    TRUE
                ) = TRUE
            ),

            classificacao AS (
                SELECT
                    *,

                    CASE
                        WHEN vendas_90_dias >= 12
                        THEN 'ALTO GIRO'

                        WHEN vendas_90_dias >= 3
                        THEN 'MÉDIO GIRO'

                        WHEN vendas_90_dias >= 1
                        THEN 'BAIXO GIRO'

                        ELSE 'SEM GIRO'
                    END AS classificacao_giro,

                    CASE
                        WHEN
                            estoque_atual <= 0
                            AND vendas_90_dias > 0
                        THEN 'RUPTURA'

                        WHEN estoque_atual <= 0
                        THEN 'SEM ESTOQUE'

                        WHEN
                            estoque_minimo > 0
                            AND estoque_atual < estoque_minimo
                        THEN 'ABAIXO DO MÍNIMO'

                        WHEN
                            vendas_90_dias = 0
                            AND COALESCE(
                                dias_sem_venda,
                                0
                            ) >= 90
                        THEN 'ESTOQUE PARADO'

                        WHEN
                            cobertura_meses IS NOT NULL
                            AND cobertura_meses > 12
                        THEN 'POSSÍVEL EXCESSO'

                        ELSE 'ESTOQUE NORMAL'
                    END AS situacao_estoque,

                    CASE
                        WHEN estoque_minimo > 0
                        THEN 'CADASTRADO'

                        ELSE 'NÃO CADASTRADO'
                    END AS situacao_estoque_minimo,

                    CASE
                        WHEN faturamento_bruto_90_dias <= 0
                        THEN 'SEM VENDAS NO PERÍODO'

                        WHEN percentual_desconto_90_dias >= 30
                        THEN 'DESCONTO MUITO ELEVADO'

                        WHEN percentual_desconto_90_dias >= 20
                        THEN 'DESCONTO ELEVADO'

                        WHEN percentual_desconto_90_dias >= 10
                        THEN 'DESCONTO MODERADO'

                        WHEN percentual_desconto_90_dias > 0
                        THEN 'DESCONTO BAIXO'

                        ELSE 'SEM DESCONTO'
                    END AS alerta_desconto

                FROM base
            )

            SELECT
                *,

                CASE
                    WHEN
                        estoque_atual <= 0
                        AND vendas_90_dias >= 12
                    THEN
                        'Produto de alto giro sem estoque. Priorizar reposição.'

                    WHEN
                        estoque_atual <= 0
                        AND vendas_90_dias >= 3
                    THEN
                        'Produto com giro e sem estoque. Avaliar reposição.'

                    WHEN
                        estoque_atual <= 0
                        AND vendas_90_dias >= 1
                    THEN
                        'Produto vendido recentemente e sem estoque. Avaliar reposição.'

                    WHEN estoque_atual <= 0
                    THEN
                        'Produto sem estoque e sem venda recente. Avaliar necessidade antes de comprar.'

                    WHEN
                        estoque_minimo > 0
                        AND estoque_atual < estoque_minimo
                    THEN
                        'Estoque abaixo do mínimo cadastrado. Avaliar reposição.'

                    WHEN
                        vendas_90_dias = 0
                        AND COALESCE(
                            dias_sem_venda,
                            0
                        ) >= 180
                    THEN
                        'Produto parado há longo período. Avaliar promoção, exposição, kit ou campanha.'

                    WHEN
                        vendas_90_dias = 0
                        AND COALESCE(
                            dias_sem_venda,
                            0
                        ) >= 90
                    THEN
                        'Produto sem giro recente com estoque. Avaliar exposição e estratégia de venda.'

                    WHEN
                        cobertura_meses IS NOT NULL
                        AND cobertura_meses > 12
                    THEN
                        'Cobertura elevada. Evitar novas compras e estimular vendas.'

                    WHEN
                        percentual_desconto_90_dias >= 30
                        AND vendas_90_dias >= 3
                    THEN
                        'Produto com giro e desconto muito elevado. Revisar preço, promoção ou política de desconto.'

                    WHEN
                        percentual_desconto_90_dias >= 20
                        AND vendas_90_dias >= 3
                    THEN
                        'Produto com giro e desconto elevado. Avaliar impacto na margem.'

                    WHEN
                        estoque_minimo <= 0
                        AND vendas_90_dias >= 12
                    THEN
                        'Produto de alto giro. Definir estoque mínimo e monitorar reposição.'

                    WHEN
                        estoque_minimo <= 0
                    THEN
                        'Estoque mínimo não cadastrado. Avaliar definição para melhorar o planejamento.'

                    WHEN vendas_90_dias >= 12
                    THEN
                        'Produto de alto giro. Monitorar para evitar ruptura.'

                    WHEN vendas_90_dias >= 3
                    THEN
                        'Giro regular. Manter acompanhamento.'

                    WHEN vendas_90_dias >= 1
                    THEN
                        'Baixo giro. Acompanhar antes de novas compras.'

                    ELSE
                        'Sem giro recente. Manter acompanhamento.'
                END AS sugestao

            FROM classificacao

            ORDER BY
                CASE
                    WHEN
                        estoque_atual <= 0
                        AND vendas_90_dias > 0
                    THEN 1

                    WHEN
                        estoque_minimo > 0
                        AND estoque_atual < estoque_minimo
                    THEN 2

                    WHEN
                        vendas_90_dias = 0
                        AND COALESCE(
                            dias_sem_venda,
                            0
                        ) >= 180
                    THEN 3

                    WHEN
                        vendas_90_dias = 0
                        AND COALESCE(
                            dias_sem_venda,
                            0
                        ) >= 90
                    THEN 4

                    WHEN
                        cobertura_meses IS NOT NULL
                        AND cobertura_meses > 12
                    THEN 5

                    WHEN percentual_desconto_90_dias >= 30
                    THEN 6

                    WHEN percentual_desconto_90_dias >= 20
                    THEN 7

                    WHEN estoque_atual <= 0
                    THEN 8

                    ELSE 9
                END,

                vendas_90_dias DESC,
                valor_estoque_custo DESC,
                produto,
                tamanho NULLS LAST
        """

        return pd.read_sql_query(
            query,
            conn,
            params=(STATUS_CONCLUIDOS,)
        )

    except Exception as erro:

        print(
            "Erro listar_giro_estoque:",
            erro
        )

        return pd.DataFrame()

    finally:
        conn.close()


# ============================================================
# RESUMO DO GIRO DE ESTOQUE
# ============================================================

def obter_resumo_giro_estoque():

    df = listar_giro_estoque()

    if df.empty:
        return {
            "produtos_ativos": 0,
            "alto_giro": 0,
            "medio_giro": 0,
            "baixo_giro": 0,
            "sem_giro": 0,
            "ruptura": 0,
            "sem_estoque": 0,
            "abaixo_minimo": 0,
            "estoque_parado": 0,
            "possivel_excesso": 0,
            "sem_minimo": 0,
            "sem_custo": 0,
            "desconto_elevado": 0,
            "desconto_muito_elevado": 0,
            "capital_estoque_conhecido": 0.0,
            "faturamento_bruto_historico": 0.0,
            "desconto_historico": 0.0,
            "faturamento_historico": 0.0,
            "percentual_desconto_historico": 0.0,
        }

    faturamento_bruto = float(
        df[
            "faturamento_bruto_historico"
        ].sum()
    )

    desconto = float(
        df[
            "desconto_historico"
        ].sum()
    )

    faturamento_liquido = float(
        df[
            "faturamento_historico"
        ].sum()
    )

    percentual_desconto = 0.0

    if faturamento_bruto > 0:

        percentual_desconto = (
            desconto
            /
            faturamento_bruto
        ) * 100

    return {
        "produtos_ativos":
            int(len(df)),

        "alto_giro":
            int(
                (
                    df["classificacao_giro"]
                    == "ALTO GIRO"
                ).sum()
            ),

        "medio_giro":
            int(
                (
                    df["classificacao_giro"]
                    == "MÉDIO GIRO"
                ).sum()
            ),

        "baixo_giro":
            int(
                (
                    df["classificacao_giro"]
                    == "BAIXO GIRO"
                ).sum()
            ),

        "sem_giro":
            int(
                (
                    df["classificacao_giro"]
                    == "SEM GIRO"
                ).sum()
            ),

        "ruptura":
            int(
                (
                    df["situacao_estoque"]
                    == "RUPTURA"
                ).sum()
            ),

        "sem_estoque":
            int(
                (
                    df["situacao_estoque"]
                    == "SEM ESTOQUE"
                ).sum()
            ),

        "abaixo_minimo":
            int(
                (
                    df["situacao_estoque"]
                    == "ABAIXO DO MÍNIMO"
                ).sum()
            ),

        "estoque_parado":
            int(
                (
                    df["situacao_estoque"]
                    == "ESTOQUE PARADO"
                ).sum()
            ),

        "possivel_excesso":
            int(
                (
                    df["situacao_estoque"]
                    == "POSSÍVEL EXCESSO"
                ).sum()
            ),

        "sem_minimo":
            int(
                (
                    df["minimo_cadastrado"]
                    == False
                ).sum()
            ),

        "sem_custo":
            int(
                (
                    df["custo_conhecido"]
                    == False
                ).sum()
            ),

        "desconto_elevado":
            int(
                (
                    df["alerta_desconto"]
                    == "DESCONTO ELEVADO"
                ).sum()
            ),

        "desconto_muito_elevado":
            int(
                (
                    df["alerta_desconto"]
                    == "DESCONTO MUITO ELEVADO"
                ).sum()
            ),

        "capital_estoque_conhecido":
            float(
                df[
                    "valor_estoque_custo"
                ].sum()
            ),

        "faturamento_bruto_historico":
            faturamento_bruto,

        "desconto_historico":
            desconto,

        "faturamento_historico":
            faturamento_liquido,

        "percentual_desconto_historico":
            float(
                percentual_desconto
            ),
    }


# ============================================================
# CONFERENCIA
# ============================================================

def conferir_giro_estoque():

    df = listar_giro_estoque()

    if df.empty:
        return {
            "quantidade_produtos": 0,
            "quantidade_unidades": 0,
            "valor_estoque_custo": 0.0,
            "vendas_historico_unidades": 0,
            "faturamento_bruto_historico": 0.0,
            "desconto_historico": 0.0,
            "faturamento_historico": 0.0,
            "diferenca_conciliacao": 0.0,
            "inicio_historico": None,
            "fim_historico": None,
        }

    inicio_historico = None
    fim_historico = None

    if "inicio_historico" in df.columns:

        valores = df[
            "inicio_historico"
        ].dropna()

        if not valores.empty:
            inicio_historico = valores.iloc[0]

    if "fim_historico" in df.columns:

        valores = df[
            "fim_historico"
        ].dropna()

        if not valores.empty:
            fim_historico = valores.iloc[0]

    faturamento_bruto = float(
        df[
            "faturamento_bruto_historico"
        ].sum()
    )

    desconto = float(
        df[
            "desconto_historico"
        ].sum()
    )

    faturamento_liquido = float(
        df[
            "faturamento_historico"
        ].sum()
    )

    diferenca_conciliacao = (
        faturamento_bruto
        -
        desconto
        -
        faturamento_liquido
    )

    return {
        "quantidade_produtos":
            int(len(df)),

        "quantidade_unidades":
            int(
                df.loc[
                    df["estoque_atual"] > 0,
                    "estoque_atual"
                ].sum()
            ),

        "valor_estoque_custo":
            float(
                df[
                    "valor_estoque_custo"
                ].sum()
            ),

        "vendas_historico_unidades":
            int(
                df[
                    "vendas_historico"
                ].sum()
            ),

        "faturamento_bruto_historico":
            faturamento_bruto,

        "desconto_historico":
            desconto,

        "faturamento_historico":
            faturamento_liquido,

        "diferenca_conciliacao":
            float(
                diferenca_conciliacao
            ),

        "inicio_historico":
            inicio_historico,

        "fim_historico":
            fim_historico,
    }