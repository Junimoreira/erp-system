from decimal import Decimal

import pandas as pd

from database.connection import conectar


# ============================================================
# CONFIGURAÇÕES
# ============================================================

STATUS_CONCLUIDOS = [
    "Concluída",
    "Concluida",
    "Conclu?da",
]

# Cadastro utilizado pelo ERP quando a venda não possui
# identificação individual do cliente.
CLIENTES_GENERICOS_IDS = [
    1,
]


# ============================================================
# CONVERTER VALOR PARA FLOAT
# ============================================================

def _para_float(valor):

    if valor is None:
        return 0.0

    if isinstance(valor, Decimal):
        return float(valor)

    try:
        return float(valor)

    except Exception:
        return 0.0


# ============================================================
# LISTAR VENDAS POR CLIENTE IDENTIFICADO
# ============================================================

def listar_vendas_por_cliente(
    data_inicio,
    data_fim,
):
    """
    Retorna uma linha por cliente identificado.

    Não inclui:
    - vendas com cliente_id NULL;
    - cadastro genérico "Consumidor".

    data_inicio é inclusiva.
    data_fim é exclusiva.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            WITH vendas_normalizadas AS (

                SELECT
                    v.id,
                    v.cliente_id,
                    v.data_venda,

                    CASE
                        WHEN
                            COALESCE(v.desconto, 0) > 0
                            AND COALESCE(v.valor_total, 0)
                                = COALESCE(v.valor_final, 0)
                        THEN
                            COALESCE(v.valor_total, 0)
                            + COALESCE(v.desconto, 0)
                        ELSE
                            COALESCE(v.valor_total, 0)
                    END AS valor_bruto,

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

                WHERE
                    v.data_venda >= %s
                    AND v.data_venda < %s
                    AND v.status = ANY(%s)
                    AND v.cliente_id IS NOT NULL
                    AND NOT (
                        v.cliente_id = ANY(%s)
                    )
            )

            SELECT
                c.id AS cliente_id,

                COALESCE(
                    NULLIF(TRIM(c.nome), ''),
                    NULLIF(TRIM(c.nome_fantasia), ''),
                    'CLIENTE SEM NOME'
                ) AS cliente,

                COALESCE(
                    c.telefone,
                    ''
                ) AS telefone,

                COALESCE(
                    c.email,
                    ''
                ) AS email,

                COUNT(
                    vn.id
                ) AS quantidade_compras,

                COALESCE(
                    SUM(vn.valor_bruto),
                    0
                ) AS valor_bruto,

                COALESCE(
                    SUM(vn.desconto),
                    0
                ) AS descontos,

                COALESCE(
                    SUM(vn.valor_final),
                    0
                ) AS total_gasto,

                COALESCE(
                    AVG(vn.valor_final),
                    0
                ) AS ticket_medio,

                MIN(
                    vn.data_venda
                ) AS primeira_compra,

                MAX(
                    vn.data_venda
                ) AS ultima_compra,

                CASE
                    WHEN COUNT(vn.id) >= 2
                    THEN 'RECORRENTE'
                    ELSE 'COMPRA ÚNICA'
                END AS recorrencia

            FROM vendas_normalizadas vn

            INNER JOIN clientes c
                ON c.id = vn.cliente_id

            GROUP BY
                c.id,
                c.nome,
                c.nome_fantasia,
                c.telefone,
                c.email

            ORDER BY
                total_gasto DESC,
                quantidade_compras DESC,
                cliente ASC
        """

        cursor = conn.cursor()

        cursor.execute(
            query,
            (
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
                CLIENTES_GENERICOS_IDS,
            ),
        )

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        linhas = cursor.fetchall()

        df = pd.DataFrame(
            linhas,
            columns=colunas,
        )

        if df.empty:
            return df

        colunas_numericas = [
            "valor_bruto",
            "descontos",
            "total_gasto",
            "ticket_medio",
        ]

        for coluna in colunas_numericas:

            df[coluna] = (
                df[coluna]
                .apply(_para_float)
            )

        df["quantidade_compras"] = (
            pd.to_numeric(
                df["quantidade_compras"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

        return df

    except Exception as erro:

        print(
            "Erro ao listar vendas por cliente:",
            erro,
        )

        return pd.DataFrame()

    finally:
        conn.close()


# ============================================================
# RESUMO DE CLIENTES IDENTIFICADOS
# ============================================================

def obter_resumo_clientes(
    data_inicio,
    data_fim,
):

    conn = conectar()

    if conn is None:

        return {
            "clientes_atendidos": 0,
            "clientes_recorrentes": 0,
            "clientes_compra_unica": 0,
            "quantidade_vendas_identificadas": 0,
            "valor_bruto_identificado": 0.0,
            "descontos_identificados": 0.0,
            "faturamento_identificado": 0.0,
            "ticket_medio_cliente": 0.0,
            "ticket_medio_compra": 0.0,
        }

    try:

        query = """
            WITH vendas_normalizadas AS (

                SELECT
                    v.id,
                    v.cliente_id,

                    CASE
                        WHEN
                            COALESCE(v.desconto, 0) > 0
                            AND COALESCE(v.valor_total, 0)
                                = COALESCE(v.valor_final, 0)
                        THEN
                            COALESCE(v.valor_total, 0)
                            + COALESCE(v.desconto, 0)
                        ELSE
                            COALESCE(v.valor_total, 0)
                    END AS valor_bruto,

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

                WHERE
                    v.data_venda >= %s
                    AND v.data_venda < %s
                    AND v.status = ANY(%s)
                    AND v.cliente_id IS NOT NULL
                    AND NOT (
                        v.cliente_id = ANY(%s)
                    )
            ),

            clientes_periodo AS (

                SELECT
                    cliente_id,
                    COUNT(*) AS quantidade_compras,
                    SUM(valor_bruto) AS valor_bruto,
                    SUM(desconto) AS descontos,
                    SUM(valor_final) AS total_gasto

                FROM vendas_normalizadas

                GROUP BY cliente_id
            )

            SELECT

                COUNT(*) AS clientes_atendidos,

                COUNT(*) FILTER (
                    WHERE quantidade_compras >= 2
                ) AS clientes_recorrentes,

                COUNT(*) FILTER (
                    WHERE quantidade_compras = 1
                ) AS clientes_compra_unica,

                COALESCE(
                    SUM(quantidade_compras),
                    0
                ) AS quantidade_vendas_identificadas,

                COALESCE(
                    SUM(valor_bruto),
                    0
                ) AS valor_bruto_identificado,

                COALESCE(
                    SUM(descontos),
                    0
                ) AS descontos_identificados,

                COALESCE(
                    SUM(total_gasto),
                    0
                ) AS faturamento_identificado,

                CASE
                    WHEN COUNT(*) > 0
                    THEN
                        COALESCE(
                            SUM(total_gasto),
                            0
                        ) / COUNT(*)
                    ELSE 0
                END AS ticket_medio_cliente,

                CASE
                    WHEN
                        COALESCE(
                            SUM(quantidade_compras),
                            0
                        ) > 0
                    THEN
                        COALESCE(
                            SUM(total_gasto),
                            0
                        )
                        /
                        SUM(quantidade_compras)
                    ELSE 0
                END AS ticket_medio_compra

            FROM clientes_periodo
        """

        cursor = conn.cursor()

        cursor.execute(
            query,
            (
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
                CLIENTES_GENERICOS_IDS,
            ),
        )

        row = cursor.fetchone()

        if not row:

            return {
                "clientes_atendidos": 0,
                "clientes_recorrentes": 0,
                "clientes_compra_unica": 0,
                "quantidade_vendas_identificadas": 0,
                "valor_bruto_identificado": 0.0,
                "descontos_identificados": 0.0,
                "faturamento_identificado": 0.0,
                "ticket_medio_cliente": 0.0,
                "ticket_medio_compra": 0.0,
            }

        return {
            "clientes_atendidos":
                int(row[0] or 0),

            "clientes_recorrentes":
                int(row[1] or 0),

            "clientes_compra_unica":
                int(row[2] or 0),

            "quantidade_vendas_identificadas":
                int(row[3] or 0),

            "valor_bruto_identificado":
                _para_float(row[4]),

            "descontos_identificados":
                _para_float(row[5]),

            "faturamento_identificado":
                _para_float(row[6]),

            "ticket_medio_cliente":
                _para_float(row[7]),

            "ticket_medio_compra":
                _para_float(row[8]),
        }

    except Exception as erro:

        print(
            "Erro ao obter resumo de clientes:",
            erro,
        )

        return {
            "clientes_atendidos": 0,
            "clientes_recorrentes": 0,
            "clientes_compra_unica": 0,
            "quantidade_vendas_identificadas": 0,
            "valor_bruto_identificado": 0.0,
            "descontos_identificados": 0.0,
            "faturamento_identificado": 0.0,
            "ticket_medio_cliente": 0.0,
            "ticket_medio_compra": 0.0,
        }

    finally:
        conn.close()


# ============================================================
# VENDAS SEM IDENTIFICAÇÃO INDIVIDUAL
# ============================================================

def obter_vendas_sem_cliente(
    data_inicio,
    data_fim,
):
    """
    Considera como não identificadas:

    - vendas com cliente_id NULL;
    - vendas vinculadas ao cadastro genérico Consumidor.
    """

    conn = conectar()

    if conn is None:

        return {
            "quantidade_vendas": 0,
            "faturamento": 0.0,
        }

    try:

        query = """
            SELECT
                COUNT(*) AS quantidade_vendas,

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

                AND (
                    v.cliente_id IS NULL

                    OR v.cliente_id = ANY(%s)
                )
        """

        cursor = conn.cursor()

        cursor.execute(
            query,
            (
                data_inicio,
                data_fim,
                STATUS_CONCLUIDOS,
                CLIENTES_GENERICOS_IDS,
            ),
        )

        row = cursor.fetchone()

        if not row:

            return {
                "quantidade_vendas": 0,
                "faturamento": 0.0,
            }

        return {
            "quantidade_vendas":
                int(row[0] or 0),

            "faturamento":
                _para_float(row[1]),
        }

    except Exception as erro:

        print(
            "Erro ao obter vendas sem cliente:",
            erro,
        )

        return {
            "quantidade_vendas": 0,
            "faturamento": 0.0,
        }

    finally:
        conn.close()


# ============================================================
# CONFERÊNCIA GERAL
# ============================================================

def conferir_relatorio_clientes(
    data_inicio,
    data_fim,
):
    """
    Confere:

    vendas identificadas
    +
    vendas sem identificação individual
    =
    total de vendas concluídas do banco.

    O mesmo vale para o faturamento.
    """

    resumo = obter_resumo_clientes(
        data_inicio,
        data_fim,
    )

    sem_cliente = obter_vendas_sem_cliente(
        data_inicio,
        data_fim,
    )

    vendas_relatorio = (
        resumo["quantidade_vendas_identificadas"]
        +
        sem_cliente["quantidade_vendas"]
    )

    faturamento_relatorio = (
        resumo["faturamento_identificado"]
        +
        sem_cliente["faturamento"]
    )

    conn = conectar()

    if conn is None:

        return {
            "vendas_relatorio": vendas_relatorio,
            "vendas_banco": 0,
            "faturamento_relatorio":
                faturamento_relatorio,
            "faturamento_banco": 0.0,
            "diferenca": 0.0,
            "ok": False,
        }

    try:

        query = """
            SELECT
                COUNT(*),

                COALESCE(
                    SUM(
                        COALESCE(
                            valor_final,
                            valor_total,
                            0
                        )
                    ),
                    0
                )

            FROM vendas

            WHERE
                data_venda >= %s
                AND data_venda < %s
                AND status = ANY(%s)
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

        vendas_banco = int(
            row[0] or 0
        )

        faturamento_banco = (
            _para_float(row[1])
        )

        diferenca = round(
            faturamento_relatorio
            - faturamento_banco,
            2,
        )

        ok = (
            vendas_relatorio
            == vendas_banco
            and abs(diferenca) <= 0.01
        )

        return {
            "vendas_relatorio":
                vendas_relatorio,

            "vendas_banco":
                vendas_banco,

            "faturamento_relatorio":
                faturamento_relatorio,

            "faturamento_banco":
                faturamento_banco,

            "diferenca":
                diferenca,

            "ok":
                ok,
        }

    except Exception as erro:

        print(
            "Erro na conferência do relatório de clientes:",
            erro,
        )

        return {
            "vendas_relatorio": vendas_relatorio,
            "vendas_banco": 0,
            "faturamento_relatorio":
                faturamento_relatorio,
            "faturamento_banco": 0.0,
            "diferenca": 0.0,
            "ok": False,
        }

    finally:
        conn.close()