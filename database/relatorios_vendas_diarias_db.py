from datetime import date, timedelta

import pandas as pd

from database.connection import conectar


STATUS_CONCLUIDOS = [
    "Concluída",
    "Concluida",
    "Conclu?da",
]


# ============================================================
# VENDAS POR DIA
# ============================================================

def obter_vendas_por_dia(
    data_inicio,
    data_fim,
):
    """
    Retorna uma linha para cada dia do período.

    data_inicio:
        data inicial inclusiva.

    data_fim:
        data final inclusiva para o usuário.

    Dias sem vendas também são retornados com valores zerados.

    Quando o período alcançar datas futuras, o calendário
    será limitado à data atual.
    """

    if data_inicio is None or data_fim is None:
        return pd.DataFrame()

    if data_inicio > data_fim:
        return pd.DataFrame()

    hoje = date.today()

    data_final_calendario = min(
        data_fim,
        hoje,
    )

    if data_inicio > data_final_calendario:
        return pd.DataFrame()

    data_fim_sql = (
        data_final_calendario
        + timedelta(days=1)
    )

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                DATE(v.data_venda) AS data,

                COUNT(
                    DISTINCT v.id
                ) AS quantidade_vendas,

                COALESCE(
                    SUM(
                        COALESCE(
                            v.valor_final,
                            v.valor_total,
                            0
                        )
                    ),
                    0
                ) AS faturamento

            FROM vendas v

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)

            GROUP BY
                DATE(v.data_venda)

            ORDER BY
                DATE(v.data_venda)
        """

        df = pd.read_sql(
            query,
            conn,
            params=(
                data_inicio,
                data_fim_sql,
                STATUS_CONCLUIDOS,
            ),
        )

    except Exception as erro:

        print(
            "Erro ao obter vendas por dia:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()

    # ========================================================
    # CALENDARIO COMPLETO
    # ========================================================

    calendario = pd.DataFrame(
        {
            "data": pd.date_range(
                start=data_inicio,
                end=data_final_calendario,
                freq="D",
            )
        }
    )

    calendario["data"] = (
        calendario["data"].dt.date
    )

    if df is not None and not df.empty:

        df = df.copy()

        df["data"] = pd.to_datetime(
            df["data"]
        ).dt.date

        calendario = calendario.merge(
            df,
            on="data",
            how="left",
        )

    else:

        calendario["quantidade_vendas"] = 0
        calendario["faturamento"] = 0

    calendario["quantidade_vendas"] = (
        calendario["quantidade_vendas"]
        .fillna(0)
        .astype(int)
    )

    calendario["faturamento"] = (
        calendario["faturamento"]
        .fillna(0)
        .astype(float)
    )

    calendario["ticket_medio"] = (
        calendario.apply(
            lambda row:
                (
                    row["faturamento"]
                    / row["quantidade_vendas"]
                )
                if row["quantidade_vendas"] > 0
                else 0,
            axis=1,
        )
    )

    return calendario


# ============================================================
# DETALHAMENTO DAS VENDAS
# ============================================================

def obter_detalhes_vendas_dia(
    data_inicio,
    data_fim,
):
    """
    Retorna uma linha por venda.

    data_inicio e data_fim são inclusivas para o usuário.

    Utilizado para conferência dos pedidos/talões.
    """

    if data_inicio is None or data_fim is None:
        return pd.DataFrame()

    if data_inicio > data_fim:
        return pd.DataFrame()

    data_fim_sql = (
        data_fim
        + timedelta(days=1)
    )

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                v.id AS venda_id,
                v.data_venda,
                c.nome AS cliente,
                v.forma_pagamento,

                COALESCE(
                    v.valor_total,
                    0
                ) AS valor_total,

                COALESCE(
                    v.desconto,
                    0
                ) AS desconto,

                COALESCE(
                    v.valor_final,
                    v.valor_total,
                    0
                ) AS valor_final

            FROM vendas v

            LEFT JOIN clientes c
                ON c.id = v.cliente_id

            WHERE
                v.data_venda >= %s
                AND v.data_venda < %s
                AND v.status = ANY(%s)

            ORDER BY
                v.data_venda,
                v.id
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                data_inicio,
                data_fim_sql,
                STATUS_CONCLUIDOS,
            ),
        )

    except Exception as erro:

        print(
            "Erro ao obter detalhes das vendas:",
            erro,
        )

        return pd.DataFrame()

    finally:

        conn.close()
