# database/dashboard_db.py

from database.connection import conectar


# ==================================================
# UTIL: SEGURANÇA DE CONEXÃO
# ==================================================
def safe_fetchone(cursor, default=0):
    try:
        return cursor.fetchone()[0] or default
    except:
        return default


# ==================================================
# DASHBOARD MENSAL (ERP PROFISSIONAL)
# ==================================================
def obter_dashboard_mensal():

    conn = conectar()

    if conn is None:
        return {}

    cursor = conn.cursor()

    dados = {}

    try:

        # ==================================================
        # VENDAS DO MÊS
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor_total), 0)
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)
        dados["vendas_mes"] = float(safe_fetchone(cursor))

        # ==================================================
        # CONTAS A RECEBER (MÊS)
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_receber
            WHERE LOWER(status) = 'pendente'
            AND DATE_TRUNC('month', vencimento)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)
        dados["receber_mes"] = float(safe_fetchone(cursor))

        # ==================================================
        # CONTAS A PAGAR (MÊS)
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE LOWER(status) = 'pendente'
            AND DATE_TRUNC('month', vencimento)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)
        dados["pagar_mes"] = float(safe_fetchone(cursor))

        # ==================================================
        # CADASTROS
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM clientes")
        dados["clientes"] = int(safe_fetchone(cursor))

        cursor.execute("SELECT COUNT(*) FROM fornecedores")
        dados["fornecedores"] = int(safe_fetchone(cursor))

        cursor.execute("SELECT COUNT(*) FROM produtos")
        dados["produtos"] = int(safe_fetchone(cursor))

        cursor.execute("""
            SELECT COUNT(*)
            FROM produtos
            WHERE estoque <= estoque_minimo
        """)
        dados["estoque_baixo"] = int(safe_fetchone(cursor))

        # ==================================================
        # CAIXA ATUAL
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN LOWER(tipo) = 'entrada' THEN valor ELSE 0 END
            ), 0)
            -
            COALESCE(SUM(
                CASE WHEN LOWER(tipo) = 'saida' THEN valor ELSE 0 END
            ), 0)
            FROM movimentacoes
        """)
        dados["caixa_atual"] = float(safe_fetchone(cursor))

        # ==================================================
        # LUCRO DO MÊS (REAL)
        # ==================================================
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


# ==================================================
# DESPESAS FIXAS DO MÊS
# ==================================================
def total_despesas_fixas_mes():

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE LOWER(status) = 'pendente'
            AND DATE_TRUNC('month', vencimento)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)

        return float(safe_fetchone(cursor))

    finally:

        cursor.close()
        conn.close()


# ==================================================
# TOTAL VENDIDO NO MÊS
# ==================================================
def total_vendido_mes():

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COALESCE(SUM(valor_total), 0)
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)

        return float(safe_fetchone(cursor))

    finally:

        cursor.close()
        conn.close()


# ==================================================
# META DO MÊS
# ==================================================
def calcular_meta_mes():

    despesas = total_despesas_fixas_mes()

    margem_lucro = despesas * 0.20

    return round(despesas + margem_lucro, 2)


# ==================================================
# FALTA PARA META
# ==================================================
def calcular_falta_meta():

    meta = calcular_meta_mes()
    vendido = total_vendido_mes()

    falta = meta - vendido

    return max(round(falta, 2), 0)


# ==================================================
# PERCENTUAL META
# ==================================================
def percentual_meta():

    meta = calcular_meta_mes()
    vendido = total_vendido_mes()

    if meta <= 0:
        return 0

    return round((vendido / meta) * 100, 2)


# ==================================================
# LUCRO ESTIMADO
# ==================================================
def lucro_estimado():

    vendido = total_vendido_mes()
    despesas = total_despesas_fixas_mes()

    return round(vendido - despesas, 2)