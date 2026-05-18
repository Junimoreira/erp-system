import pandas as pd
from database.connection import conectar


# ==================================================
# VERIFICAR CAIXA ABERTO
# ==================================================
def verificar_caixa_aberto():

    conn = conectar()

    query = """
        SELECT *
        FROM caixa
        WHERE status = 'aberto'
        ORDER BY id DESC
        LIMIT 1
    """

    df = pd.read_sql(query, conn)

    conn.close()

    if not df.empty:
        return df.iloc[0]

    return None


# ==================================================
# ABRIR CAIXA
# ==================================================
def abrir_caixa(usuario, saldo_inicial):

    conn = conectar()
    cursor = conn.cursor()

    try:

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
    cursor = conn.cursor()

    try:

        # ENTRADAS
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'entrada'
        """)

        entradas = float(cursor.fetchone()[0])

        # SAÍDAS
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'saida'
        """)

        saidas = float(cursor.fetchone()[0])

        return {

            "entradas": entradas,
            "saidas": saidas

        }

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

            total_entradas,
            total_saidas,
            saldo_final,
            valor_conferido,
            diferenca,
            caixa_id

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
# LISTAR MOVIMENTAÇÕES
# ==================================================
def listar_movimentacoes_caixa():

    conn = conectar()

    query = """
        SELECT

            tipo,
            valor,
            descricao,
            origem,
            data_movimentacao

        FROM movimentacoes

        ORDER BY data_movimentacao DESC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df