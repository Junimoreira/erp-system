from database.connection import conectar


def obter_dashboard():

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==================================================
        # CLIENTES
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]

        # ==================================================
        # PRODUTOS
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM produtos")
        total_produtos = cursor.fetchone()[0]

        # ==================================================
        # ENTRADAS
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'entrada'
        """)
        entradas = float(cursor.fetchone()[0])

        # ==================================================
        # SAÍDAS
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'saida'
        """)
        saidas = float(cursor.fetchone()[0])

        # ==================================================
        # SALDO
        # ==================================================
        saldo = entradas - saidas

        # ==================================================
        # CONTAS A PAGAR (OPCIONAL - já preparado p/ futuro)
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE status = 'Pendente'
        """)
        contas_pagar = float(cursor.fetchone()[0])

        # ==================================================
        # RETORNO
        # ==================================================
        return {
            "clientes": total_clientes,
            "produtos": total_produtos,
            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo,
            "contas_pagar": contas_pagar
        }

from database.connection import conectar
import pandas as pd


# ==================================================
# TOTAL DESPESAS FIXAS
# ==================================================

def total_despesas_fixas_mes():

    conn = conectar()

    query = """
        SELECT
            COALESCE(SUM(valor), 0) AS total
        FROM despesas
        WHERE tipo = 'Fixa'
    """

    df = pd.read_sql(
        query,
        conn
    )

    conn.close()

    return float(df.iloc[0]["total"])


# ==================================================
# TOTAL VENDAS MÊS
# ==================================================

def total_vendido_mes():

    conn = conectar()

    query = """
        SELECT
            COALESCE(SUM(valor_total), 0) AS total
        FROM vendas
    """

    df = pd.read_sql(
        query,
        conn
    )

    conn.close()

    return float(df.iloc[0]["total"])


# ==================================================
# META DO MÊS
# ==================================================

def calcular_meta_mes():

    despesas_fixas = total_despesas_fixas_mes()

    meta = despesas_fixas * 1.20

    return meta


# ==================================================
# QUANTO FALTA
# ==================================================

def calcular_falta_meta():

    meta = calcular_meta_mes()

    vendido = total_vendido_mes()

    falta = meta - vendido

    if falta < 0:

        falta = 0

    return falta


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

    return percentual


# ==================================================
# LUCRO ESTIMADO
# ==================================================

def lucro_estimado():

    vendido = total_vendido_mes()

    despesas = total_despesas_fixas_mes()

    lucro = vendido - despesas

    return lucro

    finally:
        cursor.close()
        conn.close()