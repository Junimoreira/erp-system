from datetime import datetime
from database.connection import conectar


def registrar_movimentacao_financeira(
    tipo,
    valor,
    descricao,
    origem=None,
    categoria=None,
    referencia_id=None,
    referencia_tipo=None,
    caixa_id=None,
    conta_bancaria_id=None,
    meio=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO movimentacoes (
                valor,
                data_movimentacao,
                caixa_id,
                referencia_id,
                conta_bancaria_id,
                meio,
                categoria,
                tipo,
                usuario,
                descricao,
                origem,
                referencia_tipo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            float(valor),
            datetime.now(),
            caixa_id,
            referencia_id,
            conta_bancaria_id,
            meio,
            categoria,
            tipo,
            usuario,
            descricao,
            origem,
            referencia_tipo
        ))

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_movimentacao_financeira:", erro)
        return False

    finally:
        cursor.close()

        if conn_externa is None:
            conn.close()


def registrar_entrada_caixa(
    caixa_id,
    valor,
    descricao,
    origem="DINHEIRO",
    categoria="ENTRADA_CAIXA",
    referencia_id=None,
    referencia_tipo=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE caixa
            SET saldo_final = COALESCE(saldo_final, saldo_inicial, 0) + %s
            WHERE id = %s
              AND LOWER(status) = 'aberto'
        """, (
            float(valor),
            caixa_id
        ))

        if cursor.rowcount == 0:
            raise Exception("Nenhum caixa aberto encontrado para entrada.")

        sucesso = registrar_movimentacao_financeira(
            tipo="ENTRADA",
            valor=valor,
            descricao=descricao,
            origem=origem,
            categoria=categoria,
            referencia_id=referencia_id,
            referencia_tipo=referencia_tipo,
            caixa_id=caixa_id,
            meio="CAIXA",
            usuario=usuario,
            conn_externa=conn
        )

        if not sucesso:
            raise Exception("Falha ao registrar movimentação de entrada.")

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_entrada_caixa:", erro)
        return False

    finally:
        cursor.close()

        if conn_externa is None:
            conn.close()


def registrar_saida_caixa(
    caixa_id,
    valor,
    descricao,
    origem="DINHEIRO",
    categoria="SAIDA_CAIXA",
    referencia_id=None,
    referencia_tipo=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE caixa
            SET saldo_final = COALESCE(saldo_final, saldo_inicial, 0) - %s
            WHERE id = %s
              AND LOWER(status) = 'aberto'
        """, (
            float(valor),
            caixa_id
        ))

        if cursor.rowcount == 0:
            raise Exception("Nenhum caixa aberto encontrado para saída.")

        sucesso = registrar_movimentacao_financeira(
            tipo="SAIDA",
            valor=valor,
            descricao=descricao,
            origem=origem,
            categoria=categoria,
            referencia_id=referencia_id,
            referencia_tipo=referencia_tipo,
            caixa_id=caixa_id,
            meio="CAIXA",
            usuario=usuario,
            conn_externa=conn
        )

        if not sucesso:
            raise Exception("Falha ao registrar movimentação de saída.")

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_saida_caixa:", erro)
        return False

    finally:
        cursor.close()

        if conn_externa is None:
            conn.close()


def obter_saldo_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(saldo_final, saldo_inicial, 0)
            FROM caixa
            WHERE id = %s
        """, (caixa_id,))

        resultado = cursor.fetchone()

        return resultado[0] if resultado else 0

    except Exception as erro:
        print("Erro obter_saldo_caixa:", erro)
        return 0

    finally:
        cursor.close()
        conn.close()