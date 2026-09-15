import pandas as pd

from database.connection import conectar


# ============================================================
# STATUS DE VENDAS CONCLUÍDAS
#
# Mantemos as três grafias encontradas no histórico do ERP.
# ============================================================

STATUS_CONCLUIDOS = [
    "Concluída",
    "Concluida",
    "Conclu?da",
]


# ============================================================
# REGRA DE NORMALIZAÇÃO HISTÓRICA
#
# O ERP possui dois padrões históricos de gravação:
#
# PADRÃO ANTIGO
# ------------------------------------------------------------
# valor_total = valor já com desconto
# desconto    = desconto concedido
# valor_final = mesmo valor_total
#
# Exemplo:
# itens        = 316,00
# desconto     = 12,00
# valor_total  = 304,00
# valor_final  = 304,00
#
# Nesse caso:
# bruto correto = 304,00 + 12,00 = 316,00
#
#
# PADRÃO ATUAL
# ------------------------------------------------------------
# valor_total = valor bruto
# desconto    = desconto concedido
# valor_final = valor líquido
#
# Exemplo:
# valor_total = 169,98
# desconto    = 74,97
# valor_final = 95,01
#
#
# IMPORTANTE:
# Não alteramos dados históricos.
# Apenas normalizamos a interpretação para relatórios.
# ============================================================


# ============================================================
# OBTER VENDAS DETALHADAS
# ============================================================

def obter_vendas_detalhadas(
    data_inicio,
    data_fim,
):
    """
    Retorna uma linha por venda/pedido.

    Não faz JOIN com itens_venda para não multiplicar
    a venda pela quantidade de itens do pedido.

    O campo valor_bruto é normalizado para compatibilizar
    vendas antigas e atuais.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                v.id AS pedido,

                v.data_venda,

                COALESCE(
                    c.nome,
                    'Sem identificação'
                ) AS cliente,

                CASE

                    WHEN
                        COALESCE(
                            v.desconto,
                            0
                        ) > 0

                        AND COALESCE(
                            v.valor_total,
                            0
                        ) = COALESCE(
                            v.valor_final,
                            0
                        )

                    THEN
                        COALESCE(
                            v.valor_total,
                            0
                        )
                        +
                        COALESCE(
                            v.desconto,
                            0
                        )

                    ELSE
                        COALESCE(
                            v.valor_total,
                            0
                        )

                END AS valor_bruto,

                COALESCE(
                    v.desconto,
                    0
                ) AS desconto,

                COALESCE(
                    v.valor_final,
                    v.valor_total,
                    0
                ) AS valor_final,

                COALESCE(
                    v.forma_pagamento,
                    ''
                ) AS forma_pagamento,

                COALESCE(
                    v.status,
                    ''
                ) AS status,

                CASE

                    WHEN
                        COALESCE(
                            v.desconto,
                            0
                        ) > 0

                        AND COALESCE(
                            v.valor_total,
                            0
                        ) = COALESCE(
                            v.valor_final,
                            0
                        )

                    THEN
                        TRUE

                    ELSE
                        FALSE

                END AS ajuste_historico

            FROM vendas v

            LEFT JOIN clientes c
                ON c.id = v.cliente_id

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)

            ORDER BY
                v.data_venda DESC,
                v.id DESC
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
            "Erro ao obter vendas detalhadas:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# OBTER RESUMO DAS VENDAS DO PERÍODO
# ============================================================

def obter_resumo_vendas_periodo(
    data_inicio,
    data_fim,
):
    """
    Retorna:

    - quantidade de vendas
    - valor bruto normalizado
    - descontos
    - faturamento líquido
    - ticket médio
    - quantidade de vendas históricas normalizadas

    Conferência esperada:

    valor_bruto
    -
    total_descontos
    =
    faturamento
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

                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                COALESCE(
                                    v.desconto,
                                    0
                                ) > 0

                                AND COALESCE(
                                    v.valor_total,
                                    0
                                ) = COALESCE(
                                    v.valor_final,
                                    0
                                )

                            THEN
                                COALESCE(
                                    v.valor_total,
                                    0
                                )
                                +
                                COALESCE(
                                    v.desconto,
                                    0
                                )

                            ELSE
                                COALESCE(
                                    v.valor_total,
                                    0
                                )

                        END
                    ),
                    0
                ) AS valor_bruto,

                COALESCE(
                    SUM(
                        COALESCE(
                            v.desconto,
                            0
                        )
                    ),
                    0
                ) AS total_descontos,

                COALESCE(
                    SUM(
                        COALESCE(
                            v.valor_final,
                            v.valor_total,
                            0
                        )
                    ),
                    0
                ) AS faturamento,

                CASE

                    WHEN COUNT(
                        DISTINCT v.id
                    ) > 0

                    THEN
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
                        /
                        COUNT(
                            DISTINCT v.id
                        )

                    ELSE 0

                END AS ticket_medio,

                COUNT(
                    DISTINCT v.id
                ) FILTER (
                    WHERE
                        COALESCE(
                            v.desconto,
                            0
                        ) > 0

                        AND COALESCE(
                            v.valor_total,
                            0
                        ) = COALESCE(
                            v.valor_final,
                            0
                        )
                ) AS vendas_normalizadas

            FROM vendas v

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)
        """

        cursor = conn.cursor()

        cursor.execute(
            query,
            (
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
            ),
        )

        row = cursor.fetchone()

        if row is None:

            return {
                "quantidade_vendas": 0,
                "valor_bruto": 0,
                "total_descontos": 0,
                "faturamento": 0,
                "ticket_medio": 0,
                "vendas_normalizadas": 0,
            }

        return {
            "quantidade_vendas":
                row[0] or 0,

            "valor_bruto":
                row[1] or 0,

            "total_descontos":
                row[2] or 0,

            "faturamento":
                row[3] or 0,

            "ticket_medio":
                row[4] or 0,

            "vendas_normalizadas":
                row[5] or 0,
        }

    except Exception as erro:

        print(
            "Erro ao obter resumo das vendas:",
            erro,
        )

        return None

    finally:

        conn.close()


# ============================================================
# CONFERIR CONSISTÊNCIA DO PERÍODO
# ============================================================

def conferir_totais_vendas(
    data_inicio,
    data_fim,
):
    """
    Retorna uma conferência matemática do período.

    Esperado:

    bruto - descontos = faturamento

    diferença deve ser 0 ou muito próxima de 0,
    considerando arredondamentos.
    """

    resumo = obter_resumo_vendas_periodo(
        data_inicio,
        data_fim,
    )

    if resumo is None:

        return None

    valor_bruto = float(
        resumo.get(
            "valor_bruto",
            0,
        )
        or 0
    )

    descontos = float(
        resumo.get(
            "total_descontos",
            0,
        )
        or 0
    )

    faturamento = float(
        resumo.get(
            "faturamento",
            0,
        )
        or 0
    )

    valor_esperado = (
        valor_bruto
        - descontos
    )

    diferenca = (
        valor_esperado
        - faturamento
    )

    return {
        "valor_bruto":
            valor_bruto,

        "descontos":
            descontos,

        "faturamento":
            faturamento,

        "valor_esperado":
            valor_esperado,

        "diferenca":
            diferenca,

        "ok":
            abs(
                diferenca
            ) < 0.01,

        "vendas_normalizadas":
            resumo.get(
                "vendas_normalizadas",
                0,
            ),
    }