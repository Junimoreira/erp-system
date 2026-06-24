# database/dashboard_db.py

from database.connection import conectar


def safe_fetchone(cursor, default=0):
    resultado = cursor.fetchone()

    if resultado is None:
        return default

    return resultado[0] if resultado[0] is not None else default


def _valor(cursor, query):
    cursor.execute(query)
    return float(safe_fetchone(cursor, 0))


def obter_dashboard_mensal():

    conn = conectar()

    if conn is None:
        return {}

    cursor = conn.cursor()
    dados = {}

    try:
        dados["vendas_mes"] = _valor(cursor, """
            SELECT COALESCE(SUM(valor_final), 0)
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda) = DATE_TRUNC('month', CURRENT_DATE)
              AND UPPER(COALESCE(status, '')) <> 'CANCELADA'
        """)

        dados["receber_mes"] = _valor(cursor, """
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_receber
            WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('PENDENTE', 'ABERTO')
              AND DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
        """)

        dados["pagar_mes"] = _valor(cursor, """
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
        """)

        dados["despesas_fixas_mes"] = _valor(cursor, """
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
              AND UPPER(TRIM(COALESCE(categoria, ''))) = 'FIXA'
        """)

        dados["despesas_variaveis_mes"] = _valor(cursor, """
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
              AND UPPER(TRIM(COALESCE(categoria, ''))) <> 'FIXA'
        """)

        dados["pagar_pendente_mes"] = _valor(cursor, """
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('PENDENTE', 'ABERTO', 'VENCIDO', 'AGENDADO')
              AND DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
        """)

        cursor.execute("SELECT COUNT(*) FROM clientes")
        dados["clientes"] = int(safe_fetchone(cursor, 0))

        cursor.execute("SELECT COUNT(*) FROM fornecedores")
        dados["fornecedores"] = int(safe_fetchone(cursor, 0))

        cursor.execute("SELECT COUNT(*) FROM produtos")
        dados["produtos"] = int(safe_fetchone(cursor, 0))

        cursor.execute("""
            SELECT COUNT(*)
            FROM produtos
            WHERE COALESCE(estoque, 0) <= 5
        """)
        dados["estoque_baixo"] = int(safe_fetchone(cursor, 0))

        cursor.execute("""
            SELECT id, COALESCE(saldo_inicial, 0)
            FROM caixa
            WHERE LOWER(TRIM(COALESCE(status, ''))) = 'aberto'
            ORDER BY id DESC
            LIMIT 1
        """)

        caixa = cursor.fetchone()

        if caixa:
            caixa_id = caixa[0]
            saldo_inicial = float(caixa[1] or 0)

            cursor.execute("""
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN LOWER(TRIM(COALESCE(tipo, ''))) = 'entrada'
                            THEN COALESCE(valor, 0)
                            ELSE 0
                        END
                    ), 0) AS entradas,

                    COALESCE(SUM(
                        CASE
                            WHEN LOWER(TRIM(COALESCE(tipo, ''))) = 'saida'
                            THEN COALESCE(valor, 0)
                            ELSE 0
                        END
                    ), 0) AS saidas
                FROM movimentacoes
                WHERE caixa_id = %s
            """, (caixa_id,))

            resumo_caixa = cursor.fetchone()

            entradas = float(resumo_caixa[0] or 0)
            saidas = float(resumo_caixa[1] or 0)

            dados["caixa_atual"] = saldo_inicial + entradas - saidas

        else:
            dados["caixa_atual"] = 0

        dados["lucro_mes"] = round(
            dados["vendas_mes"] - dados["pagar_mes"],
            2
        )

        return dados

    except Exception as erro:
        print(f"Erro dashboard: {erro}")
        return {}

    finally:
        cursor.close()
        conn.close()


def total_despesas_fixas_mes():

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
              AND UPPER(TRIM(COALESCE(categoria, ''))) = 'FIXA'
        """)

        return float(safe_fetchone(cursor, 0))

    except Exception as erro:
        print(f"Erro despesas fixas mês: {erro}")
        return 0

    finally:
        cursor.close()
        conn.close()


def total_despesas_variaveis_mes():

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE DATE_TRUNC('month', vencimento) = DATE_TRUNC('month', CURRENT_DATE)
              AND UPPER(TRIM(COALESCE(categoria, ''))) <> 'FIXA'
        """)

        return float(safe_fetchone(cursor, 0))

    except Exception as erro:
        print(f"Erro despesas variáveis mês: {erro}")
        return 0

    finally:
        cursor.close()
        conn.close()


def total_vendido_mes():

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(valor_final), 0)
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda) = DATE_TRUNC('month', CURRENT_DATE)
              AND UPPER(COALESCE(status, '')) <> 'CANCELADA'
        """)

        return float(safe_fetchone(cursor, 0))

    except Exception as erro:
        print(f"Erro total vendido: {erro}")
        return 0

    finally:
        cursor.close()
        conn.close()


def calcular_meta_mes():

    despesas_fixas = total_despesas_fixas_mes()
    meta = despesas_fixas * 1.25

    return round(meta, 2)


def calcular_falta_meta():

    meta = calcular_meta_mes()
    vendido = total_vendido_mes()

    falta = meta - vendido

    return max(round(falta, 2), 0)


def percentual_meta():

    meta = calcular_meta_mes()
    vendido = total_vendido_mes()

    if meta <= 0:
        return 0

    return round((vendido / meta) * 100, 2)


def lucro_estimado():

    vendido = total_vendido_mes()
    despesas_fixas = total_despesas_fixas_mes()
    despesas_variaveis = total_despesas_variaveis_mes()

    lucro = vendido - despesas_fixas - despesas_variaveis

    return round(lucro, 2)


def obter_alertas_financeiros():

    conn = conectar()

    if conn is None:
        return {
            "vencidas": [],
            "hoje": [],
            "proximas": []
        }

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT descricao, valor, vencimento
            FROM contas_pagar
            WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('PENDENTE', 'ABERTO', 'VENCIDO', 'AGENDADO')
              AND vencimento < CURRENT_DATE
            ORDER BY vencimento
        """)

        vencidas = cursor.fetchall()

        cursor.execute("""
            SELECT descricao, valor, vencimento
            FROM contas_pagar
            WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('PENDENTE', 'ABERTO', 'VENCIDO', 'AGENDADO')
              AND vencimento = CURRENT_DATE
            ORDER BY vencimento
        """)

        hoje = cursor.fetchall()

        cursor.execute("""
            SELECT descricao, valor, vencimento
            FROM contas_pagar
            WHERE UPPER(TRIM(COALESCE(status, ''))) IN ('PENDENTE', 'ABERTO', 'VENCIDO', 'AGENDADO')
              AND vencimento > CURRENT_DATE
              AND vencimento <= CURRENT_DATE + INTERVAL '7 days'
            ORDER BY vencimento
        """)

        proximas = cursor.fetchall()

        return {
            "vencidas": vencidas,
            "hoje": hoje,
            "proximas": proximas
        }

    except Exception as erro:
        print(f"Erro alertas: {erro}")
        return {
            "vencidas": [],
            "hoje": [],
            "proximas": []
        }

    finally:
        cursor.close()
        conn.close()