from database.connection import conectar


# ==================================================
# DASHBOARD MENSAL
# ==================================================
def obter_dashboard_mensal():

    conn = conectar()

    if conn is None:
        return {}

    cursor = conn.cursor()

    dados = {}

    try:

        # ==========================================
        # VENDAS MÊS
        # ==========================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor_total), 0)
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)

        dados["vendas_mes"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # CONTAS RECEBER
        # ==========================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_receber
            WHERE status = 'PENDENTE'
        """)

        dados["receber_mes"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # CONTAS PAGAR
        # ==========================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE status = 'PENDENTE'
        """)

        dados["pagar_mes"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # CLIENTES
        # ==========================================
        cursor.execute("""
            SELECT COUNT(*)
            FROM clientes
        """)

        dados["clientes"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # FORNECEDORES
        # ==========================================
        cursor.execute("""
            SELECT COUNT(*)
            FROM fornecedores
        """)

        dados["fornecedores"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # PRODUTOS
        # ==========================================
        cursor.execute("""
            SELECT COUNT(*)
            FROM produtos
        """)

        dados["produtos"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # ESTOQUE BAIXO
        # ==========================================
        cursor.execute("""
            SELECT COUNT(*)
            FROM produtos
            WHERE estoque <= estoque_minimo
        """)

        dados["estoque_baixo"] = (
            cursor.fetchone()[0] or 0
        )

        # ==========================================
        # CAIXA ATUAL
        # ==========================================
        cursor.execute("""
            SELECT COALESCE(saldo_final, 0)
            FROM caixa
            ORDER BY id DESC
            LIMIT 1
        """)

        resultado_caixa = cursor.fetchone()

        dados["caixa_atual"] = (
            resultado_caixa[0]
            if resultado_caixa
            else 0
        )

        # ==========================================
        # LUCRO MÊS
        # ==========================================
        cursor.execute("""
            SELECT COALESCE(
                SUM(valor_total - custo_total),
                0
            )
            FROM vendas
            WHERE DATE_TRUNC('month', data_venda)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)

        dados["lucro_mes"] = (
            cursor.fetchone()[0] or 0
        )

        return dados

    except Exception as erro:

        print(
            "Erro dashboard:",
            erro
        )

        return {}

    finally:

        cursor.close()
        conn.close()


# ==================================================
# DESPESAS FIXAS MÊS
# ==================================================
def total_despesas_fixas_mes():

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM despesas
            WHERE DATE_TRUNC('month', data_despesa)
            = DATE_TRUNC('month', CURRENT_DATE)
        """)

        return float(
            cursor.fetchone()[0] or 0
        )

    except:
        return 0

    finally:

        cursor.close()
        conn.close()


# ==================================================
# TOTAL VENDIDO
# ==================================================
def total_vendido_mes():

    dados = obter_dashboard_mensal()

    return float(
        dados.get("vendas_mes", 0)
    )


# ==================================================
# META MÊS
# ==================================================
def calcular_meta_mes():

    despesas = total_despesas_fixas_mes()

    return float(despesas * 2)


# ==================================================
# FALTA META
# ==================================================
def calcular_falta_meta():

    meta = calcular_meta_mes()

    vendido = total_vendido_mes()

    falta = meta - vendido

    return max(falta, 0)


# ==================================================
# PERCENTUAL META
# ==================================================
def percentual_meta():

    meta = calcular_meta_mes()

    vendido = total_vendido_mes()

    if meta <= 0:
        return 0

    return round(
        (vendido / meta) * 100,
        2
    )


# ==================================================
# LUCRO ESTIMADO
# ==================================================
def lucro_estimado():

    vendido = total_vendido_mes()

    despesas = total_despesas_fixas_mes()

    return round(
        vendido - despesas,
        2
    )