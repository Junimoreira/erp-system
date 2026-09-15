import pandas as pd

from database.connection import conectar


# ============================================================
# STATUS DE VENDAS CONCLUÍDAS
#
# Mantemos as grafias encontradas no histórico do ERP.
# ============================================================

STATUS_CONCLUIDOS = [
    "Concluída",
    "Concluida",
    "Conclu?da",
]


# ============================================================
# NORMALIZAR FORMA DE PAGAMENTO
#
# O histórico pode conter pequenas diferenças de escrita.
# A normalização serve somente para os relatórios.
# ============================================================

SQL_FORMA_PAGAMENTO_NORMALIZADA = """
    CASE

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) IN (
            'DINHEIRO',
            'CAIXA'
        )
        THEN 'DINHEIRO'

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) = 'PIX'
        THEN 'PIX'

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) IN (
            'CARTÃO DÉBITO',
            'CARTAO DEBITO',
            'CARTÃO DEBITO',
            'CARTAO DÉBITO',
            'DÉBITO',
            'DEBITO'
        )
        THEN 'CARTÃO DÉBITO'

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) IN (
            'CARTÃO CRÉDITO',
            'CARTAO CREDITO',
            'CARTÃO CREDITO',
            'CARTAO CRÉDITO',
            'CRÉDITO',
            'CREDITO',
            'CARTÃO'
        )
        THEN 'CARTÃO CRÉDITO'

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) IN (
            'TRANSFERÊNCIA',
            'TRANSFERENCIA'
        )
        THEN 'TRANSFERÊNCIA'

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) IN (
            'BOLETO',
            'BOLETO BANCÁRIO',
            'BOLETO BANCARIO'
        )
        THEN 'BOLETO'

        WHEN UPPER(
            TRIM(
                COALESCE(
                    v.forma_pagamento,
                    ''
                )
            )
        ) IN (
            'FIADO',
            'A PRAZO',
            'À PRAZO'
        )
        THEN 'FIADO'

        WHEN TRIM(
            COALESCE(
                v.forma_pagamento,
                ''
            )
        ) = ''
        THEN 'NÃO INFORMADO'

        ELSE UPPER(
            TRIM(
                v.forma_pagamento
            )
        )

    END
"""


# ============================================================
# RESUMO POR FORMA DE PAGAMENTO
# ============================================================

def obter_vendas_por_forma_pagamento(
    data_inicio,
    data_fim,
):
    """
    Retorna uma linha para cada forma de pagamento.

    Cada venda é contabilizada uma única vez porque a consulta
    utiliza somente a tabela vendas.

    O faturamento utiliza valor_final, ou seja, o valor
    efetivamente registrado como valor final da venda.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = f"""
            WITH vendas_periodo AS (

                SELECT
                    v.id,

                    {SQL_FORMA_PAGAMENTO_NORMALIZADA}
                        AS forma_pagamento,

                    COALESCE(
                        v.valor_final,
                        v.valor_total,
                        0
                    ) AS valor_final

                FROM vendas v

                WHERE
                    v.data_venda >= %s
                    AND v.data_venda < %s
                    AND v.status = ANY(%s)

            ),

            total_periodo AS (

                SELECT
                    COUNT(*) AS quantidade_total_vendas,

                    COALESCE(
                        SUM(
                            valor_final
                        ),
                        0
                    ) AS faturamento_total

                FROM vendas_periodo

            )

            SELECT
                vp.forma_pagamento,

                COUNT(*) AS quantidade_vendas,

                COALESCE(
                    SUM(
                        vp.valor_final
                    ),
                    0
                ) AS faturamento,

                CASE
                    WHEN COUNT(*) > 0
                    THEN
                        COALESCE(
                            SUM(
                                vp.valor_final
                            ),
                            0
                        )
                        /
                        COUNT(*)
                    ELSE 0
                END AS ticket_medio,

                CASE
                    WHEN tp.quantidade_total_vendas > 0
                    THEN
                        COUNT(*)::numeric
                        /
                        tp.quantidade_total_vendas
                        * 100
                    ELSE 0
                END AS participacao_quantidade_percentual,

                CASE
                    WHEN tp.faturamento_total > 0
                    THEN
                        COALESCE(
                            SUM(
                                vp.valor_final
                            ),
                            0
                        )
                        /
                        tp.faturamento_total
                        * 100
                    ELSE 0
                END AS participacao_faturamento_percentual

            FROM vendas_periodo vp

            CROSS JOIN total_periodo tp

            GROUP BY
                vp.forma_pagamento,
                tp.quantidade_total_vendas,
                tp.faturamento_total

            ORDER BY
                faturamento DESC,
                quantidade_vendas DESC,
                vp.forma_pagamento
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
            ),
        )

    except Exception as erro:

        print(
            "Erro ao obter vendas por forma de pagamento:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# RESUMO GERAL DAS FORMAS DE PAGAMENTO
# ============================================================

def obter_resumo_formas_pagamento(
    data_inicio,
    data_fim,
):
    """
    Retorna os principais indicadores do período.

    - quantidade de vendas
    - faturamento
    - ticket médio
    - quantidade de formas de pagamento utilizadas
    """

    df = obter_vendas_por_forma_pagamento(
        data_inicio,
        data_fim,
    )

    if df is None or df.empty:

        return {
            "quantidade_vendas": 0,
            "faturamento": 0,
            "ticket_medio": 0,
            "quantidade_formas": 0,
        }

    quantidade_vendas = int(
        df["quantidade_vendas"].sum()
    )

    faturamento = float(
        df["faturamento"].sum()
    )

    ticket_medio = (
        faturamento
        / quantidade_vendas
        if quantidade_vendas > 0
        else 0
    )

    quantidade_formas = int(
        df["forma_pagamento"].nunique()
    )

    return {
        "quantidade_vendas":
            quantidade_vendas,

        "faturamento":
            faturamento,

        "ticket_medio":
            ticket_medio,

        "quantidade_formas":
            quantidade_formas,
    }


# ============================================================
# CONFERÊNCIA COM O TOTAL DE VENDAS
# ============================================================

def conferir_formas_pagamento(
    data_inicio,
    data_fim,
):
    """
    Confere se a soma das formas de pagamento fecha com
    a quantidade de vendas e o faturamento registrados
    diretamente na tabela vendas.
    """

    conn = conectar()

    if conn is None:
        return None

    try:

        df = obter_vendas_por_forma_pagamento(
            data_inicio,
            data_fim,
        )

        if df is None:

            return None

        quantidade_formas = int(
            df["quantidade_vendas"].sum()
        ) if not df.empty else 0

        faturamento_formas = float(
            df["faturamento"].sum()
        ) if not df.empty else 0

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(
                    DISTINCT v.id
                ),

                COALESCE(
                    SUM(
                        COALESCE(
                            v.valor_final,
                            v.valor_total,
                            0
                        )
                    ),
                    0
                )

            FROM vendas v

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)
            """,
            (
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
            ),
        )

        row = cursor.fetchone()

        quantidade_banco = int(
            row[0] or 0
        )

        faturamento_banco = float(
            row[1] or 0
        )

        diferenca_quantidade = (
            quantidade_formas
            - quantidade_banco
        )

        diferenca_faturamento = (
            faturamento_formas
            - faturamento_banco
        )

        return {
            "quantidade_formas":
                quantidade_formas,

            "quantidade_banco":
                quantidade_banco,

            "diferenca_quantidade":
                diferenca_quantidade,

            "faturamento_formas":
                faturamento_formas,

            "faturamento_banco":
                faturamento_banco,

            "diferenca_faturamento":
                diferenca_faturamento,

            "ok":
                (
                    diferenca_quantidade == 0
                    and abs(
                        diferenca_faturamento
                    ) < 0.01
                ),
        }

    except Exception as erro:

        print(
            "Erro ao conferir formas de pagamento:",
            erro,
        )

        return None

    finally:

        conn.close()