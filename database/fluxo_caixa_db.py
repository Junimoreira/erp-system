import pandas as pd
from database.connection import conectar


# ==================================================
# LISTAR CONTAS A PAGAR FUTURAS / EM ABERTO
# ==================================================
def listar_pagar_previsto(data_inicio=None, data_fim=None):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        filtros = """
            WHERE UPPER(COALESCE(status, '')) NOT IN ('PAGO', 'PAGA')
        """

        params = []

        if data_inicio:
            filtros += " AND vencimento >= %s"
            params.append(data_inicio)

        if data_fim:
            filtros += " AND vencimento <= %s"
            params.append(data_fim)

        query = f"""
            SELECT
                id,
                descricao,
                valor,
                vencimento,
                categoria,
                status,
                observacoes
            FROM contas_pagar
            {filtros}
            ORDER BY vencimento ASC
        """

        return pd.read_sql(query, conn, params=params)

    except Exception as erro:
        print("Erro ao listar contas a pagar previstas:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# LISTAR CONTAS A RECEBER FUTURAS / EM ABERTO
# ==================================================
def listar_receber_previsto(data_inicio=None, data_fim=None):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        filtros = """
            WHERE UPPER(COALESCE(status, '')) NOT IN ('RECEBIDO', 'RECEBIDA')
        """

        params = []

        if data_inicio:
            filtros += " AND vencimento >= %s"
            params.append(data_inicio)

        if data_fim:
            filtros += " AND vencimento <= %s"
            params.append(data_fim)

        query = f"""
            SELECT
                id,
                cliente,
                descricao,
                valor,
                vencimento,
                status,
                observacoes
            FROM contas_receber
            {filtros}
            ORDER BY vencimento ASC
        """

        return pd.read_sql(query, conn, params=params)

    except Exception as erro:
        print("Erro ao listar contas a receber previstas:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RESUMO MENSAL PREVISTO
# ==================================================
def resumo_fluxo_caixa_previsto(data_inicio=None, data_fim=None):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        params_pagar = []
        params_receber = []

        filtro_pagar = """
            WHERE UPPER(COALESCE(status, '')) NOT IN ('PAGO', 'PAGA')
        """

        filtro_receber = """
            WHERE UPPER(COALESCE(status, '')) NOT IN ('RECEBIDO', 'RECEBIDA')
        """

        if data_inicio:
            filtro_pagar += " AND vencimento >= %s"
            filtro_receber += " AND vencimento >= %s"
            params_pagar.append(data_inicio)
            params_receber.append(data_inicio)

        if data_fim:
            filtro_pagar += " AND vencimento <= %s"
            filtro_receber += " AND vencimento <= %s"
            params_pagar.append(data_fim)
            params_receber.append(data_fim)

        query = f"""
            WITH receber AS (
                SELECT
                    DATE_TRUNC('month', vencimento)::date AS mes,
                    SUM(valor) AS total_receber
                FROM contas_receber
                {filtro_receber}
                GROUP BY DATE_TRUNC('month', vencimento)
            ),
            pagar AS (
                SELECT
                    DATE_TRUNC('month', vencimento)::date AS mes,
                    SUM(valor) AS total_pagar
                FROM contas_pagar
                {filtro_pagar}
                GROUP BY DATE_TRUNC('month', vencimento)
            ),
            meses AS (
                SELECT mes FROM receber
                UNION
                SELECT mes FROM pagar
            )
            SELECT
                meses.mes,
                COALESCE(receber.total_receber, 0) AS total_receber,
                COALESCE(pagar.total_pagar, 0) AS total_pagar,
                COALESCE(receber.total_receber, 0)
                    - COALESCE(pagar.total_pagar, 0) AS saldo_previsto
            FROM meses
            LEFT JOIN receber ON receber.mes = meses.mes
            LEFT JOIN pagar ON pagar.mes = meses.mes
            ORDER BY meses.mes ASC
        """

        params = params_receber + params_pagar

        df = pd.read_sql(query, conn, params=params)

        if df.empty:
            return df

        df["saldo_acumulado"] = df["saldo_previsto"].cumsum()

        return df

    except Exception as erro:
        print("Erro ao gerar resumo do fluxo de caixa previsto:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RESUMO GERAL DO PERÍODO
# ==================================================
def resumo_geral_fluxo(data_inicio=None, data_fim=None):

    df_resumo = resumo_fluxo_caixa_previsto(data_inicio, data_fim)

    if df_resumo.empty:
        return {
            "total_receber": 0,
            "total_pagar": 0,
            "saldo_previsto": 0,
            "saldo_acumulado": 0
        }

    total_receber = float(df_resumo["total_receber"].sum())
    total_pagar = float(df_resumo["total_pagar"].sum())
    saldo_previsto = total_receber - total_pagar
    saldo_acumulado = float(df_resumo["saldo_acumulado"].iloc[-1])

    return {
        "total_receber": total_receber,
        "total_pagar": total_pagar,
        "saldo_previsto": saldo_previsto,
        "saldo_acumulado": saldo_acumulado
    }