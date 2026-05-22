import pandas as pd
from database.connection import conectar


# ==================================================
# VERIFICAR CAIXA ABERTO
# ==================================================
def verificar_caixa_aberto():

    conn = conectar()

    if conn is None:
        return None

    try:

        query = """
            SELECT *
            FROM caixa
            WHERE status = 'aberto'
            ORDER BY id DESC
            LIMIT 1
        """

        df = pd.read_sql(query, conn)

        if df.empty:
            return None

        return df.iloc[0]

    except Exception as erro:

        print("Erro ao verificar caixa:", erro)
        return None

    finally:

        conn.close()


# ==================================================
# ABRIR CAIXA
# ==================================================
def abrir_caixa(usuario, saldo_inicial):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        saldo_inicial = float(saldo_inicial)

        cursor.execute("""
            INSERT INTO caixa (
                usuario,
                data_abertura,
                saldo_inicial,
                total_entradas,
                total_saidas,
                saldo_final,
                valor_conferido,
                diferenca,
                status
            )
            VALUES (
                %s,
                CURRENT_TIMESTAMP,
                %s,
                0,
                0,
                0,
                0,
                0,
                'aberto'
            )
        """, (
            usuario,
            saldo_inicial
        ))

        conn.commit()
        return True

    except Exception as erro:

        conn.rollback()
        print("Erro ao abrir caixa:", erro)
        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# RESUMO DO CAIXA
# ==================================================
def resumo_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0}

    cursor = conn.cursor()

    try:

        caixa_id = int(caixa_id)

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'entrada'
            AND caixa_id = %s
        """, (caixa_id,))

        entradas = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'saida'
            AND caixa_id = %s
        """, (caixa_id,))

        saidas = float(cursor.fetchone()[0])

        return {
            "entradas": entradas,
            "saidas": saidas
        }

    except Exception as erro:

        print("Erro no resumo do caixa:", erro)

        return {"entradas": 0, "saidas": 0}

    finally:

        cursor.close()
        conn.close()


# ==================================================
# FECHAR CAIXA
# ==================================================
def fechar_caixa(
    caixa_id,
    total_entradas,
    total_saidas,
    saldo_final,
    valor_conferido,
    diferenca
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE caixa
            SET
                data_fechamento = CURRENT_TIMESTAMP,
                total_entradas = %s,
                total_saidas = %s,
                saldo_final = %s,
                valor_conferido = %s,
                diferenca = %s,
                status = 'fechado'
            WHERE id = %s
        """, (
            float(total_entradas),
            float(total_saidas),
            float(saldo_final),
            float(valor_conferido),
            float(diferenca),
            int(caixa_id)
        ))

        conn.commit()
        return True

    except Exception as erro:

        conn.rollback()
        print("Erro ao fechar caixa:", erro)
        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR MOVIMENTAÇÕES DO CAIXA
# ==================================================
def listar_movimentacoes_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                tipo,
                valor,
                descricao,
                origem,
                data_movimentacao
            FROM movimentacoes
            WHERE caixa_id = %s
            ORDER BY data_movimentacao DESC
        """

        df = pd.read_sql(query, conn, params=(int(caixa_id),))

        return df

    except Exception as erro:

        print("Erro ao listar movimentações:", erro)
        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# 🔥 NOVO: LISTAR CAIXA POR PERÍODO (RELATÓRIO)
# ==================================================
def listar_caixa_periodo(data_inicio, data_fim):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                usuario,
                data_abertura,
                data_fechamento,
                saldo_inicial,
                total_entradas,
                total_saidas,
                saldo_final,
                valor_conferido,
                diferenca,
                status
            FROM caixa
            WHERE DATE(data_abertura) BETWEEN %s AND %s
            ORDER BY data_abertura DESC
        """

        df = pd.read_sql(query, conn, params=(data_inicio, data_fim))

        return df

    except Exception as erro:

        print("Erro ao listar caixa por período:", erro)
        return pd.DataFrame()

    finally:

        conn.close()