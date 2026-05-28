# database/dashboard_db.py

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
        # VENDAS DO MÊS
        # ==========================================
        try:

            cursor.execute("""
                SELECT COALESCE(SUM(valor_total), 0)
                FROM vendas
                WHERE DATE_TRUNC('month', data_venda)
                = DATE_TRUNC('month', CURRENT_DATE)
            """)

            dados["vendas_mes"] = float(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["vendas_mes"] = 0

        # ==========================================
        # CONTAS A RECEBER DO MÊS
        # ==========================================
        try:

            cursor.execute("""
                SELECT COALESCE(SUM(valor), 0)
                FROM contas_receber
                WHERE LOWER(status) = 'pendente'
                AND DATE_TRUNC('month', vencimento)
                = DATE_TRUNC('month', CURRENT_DATE)
            """)

            dados["receber_mes"] = float(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["receber_mes"] = 0

        # ==========================================
        # CONTAS A PAGAR DO MÊS
        # ==========================================
        try:

            cursor.execute("""
                SELECT COALESCE(SUM(valor), 0)
                FROM contas_pagar
                WHERE LOWER(status) = 'pendente'
                AND DATE_TRUNC('month', vencimento)
                = DATE_TRUNC('month', CURRENT_DATE)
            """)

            dados["pagar_mes"] = float(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["pagar_mes"] = 0

        # ==========================================
        # CLIENTES
        # ==========================================
        try:

            cursor.execute("""
                SELECT COUNT(*)
                FROM clientes
            """)

            dados["clientes"] = int(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["clientes"] = 0

        # ==========================================
        # FORNECEDORES
        # ==========================================
        try:

            cursor.execute("""
                SELECT COUNT(*)
                FROM fornecedores
            """)

            dados["fornecedores"] = int(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["fornecedores"] = 0

        # ==========================================
        # PRODUTOS
        # ==========================================
        try:

            cursor.execute("""
                SELECT COUNT(*)
                FROM produtos
            """)

            dados["produtos"] = int(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["produtos"] = 0

        # ==========================================
        # ESTOQUE BAIXO
        # ==========================================
        try:

            cursor.execute("""
                SELECT COUNT(*)
                FROM produtos
                WHERE estoque <= estoque_minimo
            """)

            dados["estoque_baixo"] = int(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["estoque_baixo"] = 0

        # ==========================================
        # CAIXA ATUAL
        # ==========================================
        try:

            cursor.execute("""
                SELECT
                    COALESCE(SUM(
                        CASE
                            WHEN LOWER(tipo) = 'entrada'
                            THEN valor
                            ELSE 0
                        END
                    ), 0)
                    -
                    COALESCE(SUM(
                        CASE
                            WHEN LOWER(tipo) = 'saida'
                            THEN valor
                            ELSE 0
                        END
                    ), 0)
                FROM movimentacoes
            """)

            dados["caixa_atual"] = float(
                cursor.fetchone()[0] or 0
            )

        except:

            dados["caixa_atual"] = 0

        # ==========================================
        # LUCRO DO MÊS
        # ==========================================
        dados["lucro_mes"] = (
            dados["vendas_mes"]
            -
            dados["pagar_mes"]
        )

        return dados

    except Exception as erro:

        print(
            f"Erro dashboard: {erro}"
        )

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

        total = cursor.fetchone()[0]

        return float(total or 0)

    except:

        return 0

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

        total = cursor.fetchone()[0]

        return float(total or 0)

    except:

        return 0

    finally:

        cursor.close()
        conn.close()


# ==================================================
# META DO MÊS
# ==================================================
def calcular_meta_mes():

    despesas = total_despesas_fixas_mes()

    # ==========================================
    # MARGEM DE LUCRO 20%
    # ==========================================
    margem_lucro = despesas * 0.20

    meta = despesas + margem_lucro

    return round(
        float(meta),
        2
    )


# ==================================================
# FALTA PARA META
# ==================================================
def calcular_falta_meta():

    meta = calcular_meta_mes()

    vendido = total_vendido_mes()

    falta = meta - vendido

    return max(
        round(float(falta), 2),
        0
    )


# ==================================================
# PERCENTUAL META
# ==================================================
def percentual_meta():

    meta = calcular_meta_mes()

    vendido = total_vendido_mes()

    if meta <= 0:

        return 0

    percentual = (
        vendido / meta
    ) * 100

    return round(
        percentual,
        2
    )


# ==================================================
# LUCRO ESTIMADO
# ==================================================
def lucro_estimado():

    vendido = total_vendido_mes()

    despesas = total_despesas_fixas_mes()

    lucro = vendido - despesas

    return round(
        lucro,
        2
    )