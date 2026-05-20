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

        if not df.empty:
            return df.iloc[0]

        return None

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
        return None

    cursor = conn.cursor()

    try:

        caixa_id = int(caixa_id)

        # ==================================================
        # ENTRADAS
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'entrada'
            AND caixa_id = %s
        """, (caixa_id,))

        entradas = float(cursor.fetchone()[0])

        # ==================================================
        # SAÍDAS
        # ==================================================
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

        return {

            "entradas": 0,
            "saidas": 0

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

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        caixa_id = int(caixa_id)

        total_entradas = float(total_entradas)
        total_saidas = float(total_saidas)

        saldo_final = float(saldo_final)

        valor_conferido = float(valor_conferido)

        diferenca = float(diferenca)

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
# LISTAR MOVIMENTAÇÕES DO CAIXA
# ==================================================
def listar_movimentacoes_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        caixa_id = int(caixa_id)

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

        df = pd.read_sql(
            query,
            conn,
            params=(caixa_id,)
        )

        return df

    except Exception as erro:

        print("Erro ao listar movimentações:", erro)

        return pd.DataFrame()

    finally:

        conn.close()