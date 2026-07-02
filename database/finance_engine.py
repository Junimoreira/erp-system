from datetime import datetime
from database.connection import conectar


# ==================================================
# BUSCAR CAIXA ABERTO
# ==================================================
def buscar_caixa_aberto(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM caixa
        WHERE LOWER(status) = 'aberto'
        ORDER BY id DESC
        LIMIT 1
    """)

    caixa = cursor.fetchone()
    cursor.close()

    return caixa[0] if caixa else None


# ==================================================
# REGISTRAR MOVIMENTAÇÃO FINANCEIRA
# ==================================================
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
        tipo = str(tipo).strip().lower()
        meio = str(meio).strip().upper() if meio else None
        valor = float(valor)

        if tipo not in ["entrada", "saida"]:
            raise ValueError("Tipo inválido. Use entrada ou saida.")

        if valor <= 0:
            raise ValueError("Valor inválido.")

        cursor.execute("""
            INSERT INTO movimentacoes (
                tipo,
                valor,
                descricao,
                origem,
                data_movimentacao,
                caixa_id,
                categoria,
                referencia_id,
                referencia_tipo,
                conta_bancaria_id,
                usuario,
                meio
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            tipo,
            valor,
            descricao,
            origem,
            datetime.now(),
            caixa_id,
            categoria,
            referencia_id,
            referencia_tipo,
            conta_bancaria_id,
            usuario,
            meio
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


# ==================================================
# ENTRADA NO CAIXA
# ==================================================
def registrar_entrada_caixa(
    valor,
    descricao,
    origem="CAIXA",
    categoria="ENTRADA_CAIXA",
    referencia_id=None,
    referencia_tipo=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    try:
        caixa_id = buscar_caixa_aberto(conn)

        if caixa_id is None:
            raise Exception("Nenhum caixa aberto encontrado.")

        sucesso = registrar_movimentacao_financeira(
            tipo="entrada",
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
            raise Exception("Falha ao registrar entrada no caixa.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE caixa
            SET
                total_entradas = COALESCE(total_entradas, 0) + %s,
                saldo_final = COALESCE(saldo_final, saldo_inicial, 0) + %s
            WHERE id = %s
        """, (
            float(valor),
            float(valor),
            caixa_id
        ))
        cursor.close()

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_entrada_caixa:", erro)
        return False

    finally:
        if conn_externa is None:
            conn.close()


# ==================================================
# SAÍDA DO CAIXA
# ==================================================
def registrar_saida_caixa(
    valor,
    descricao,
    origem="CAIXA",
    categoria="SAIDA_CAIXA",
    referencia_id=None,
    referencia_tipo=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    try:
        caixa_id = buscar_caixa_aberto(conn)

        if caixa_id is None:
            raise Exception("Nenhum caixa aberto encontrado.")

        sucesso = registrar_movimentacao_financeira(
            tipo="saida",
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
            raise Exception("Falha ao registrar saída do caixa.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE caixa
            SET
                total_saidas = COALESCE(total_saidas, 0) + %s,
                saldo_final = COALESCE(saldo_final, saldo_inicial, 0) - %s
            WHERE id = %s
        """, (
            float(valor),
            float(valor),
            caixa_id
        ))
        cursor.close()

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_saida_caixa:", erro)
        return False

    finally:
        if conn_externa is None:
            conn.close()


# ==================================================
# ENTRADA NO BANCO
# ==================================================
def registrar_entrada_banco(
    conta_bancaria_id,
    valor,
    descricao,
    origem="BANCO",
    categoria="ENTRADA_BANCO",
    referencia_id=None,
    referencia_tipo=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    try:
        sucesso = registrar_movimentacao_financeira(
            tipo="entrada",
            valor=valor,
            descricao=descricao,
            origem=origem,
            categoria=categoria,
            referencia_id=referencia_id,
            referencia_tipo=referencia_tipo,
            conta_bancaria_id=conta_bancaria_id,
            meio="BANCO",
            usuario=usuario,
            conn_externa=conn
        )

        if not sucesso:
            raise Exception("Falha ao registrar entrada bancária.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contas_bancarias
            SET saldo = COALESCE(saldo, 0) + %s
            WHERE id = %s
        """, (
            float(valor),
            int(conta_bancaria_id)
        ))
        cursor.close()

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_entrada_banco:", erro)
        return False

    finally:
        if conn_externa is None:
            conn.close()


# ==================================================
# SAÍDA DO BANCO
# ==================================================
def registrar_saida_banco(
    conta_bancaria_id,
    valor,
    descricao,
    origem="BANCO",
    categoria="SAIDA_BANCO",
    referencia_id=None,
    referencia_tipo=None,
    usuario=None,
    conn_externa=None
):

    conn = conn_externa if conn_externa else conectar()

    if conn is None:
        return False

    try:
        sucesso = registrar_movimentacao_financeira(
            tipo="saida",
            valor=valor,
            descricao=descricao,
            origem=origem,
            categoria=categoria,
            referencia_id=referencia_id,
            referencia_tipo=referencia_tipo,
            conta_bancaria_id=conta_bancaria_id,
            meio="BANCO",
            usuario=usuario,
            conn_externa=conn
        )

        if not sucesso:
            raise Exception("Falha ao registrar saída bancária.")

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contas_bancarias
            SET saldo = COALESCE(saldo, 0) - %s
            WHERE id = %s
        """, (
            float(valor),
            int(conta_bancaria_id)
        ))
        cursor.close()

        if conn_externa is None:
            conn.commit()

        return True

    except Exception as erro:
        if conn_externa is None:
            conn.rollback()

        print("Erro registrar_saida_banco:", erro)
        return False

    finally:
        if conn_externa is None:
            conn.close()


# ==================================================
# SALDO DO CAIXA ABERTO
# ==================================================
def obter_saldo_caixa(caixa_id=None):

    conn = conectar()

    if conn is None:
        return 0

    cursor = conn.cursor()

    try:
        if caixa_id is None:
            caixa_id = buscar_caixa_aberto(conn)

        if caixa_id is None:
            return 0

        cursor.execute("""
            SELECT
                COALESCE(saldo_inicial, 0)
                + COALESCE(total_entradas, 0)
                - COALESCE(total_saidas, 0)
            FROM caixa
            WHERE id = %s
        """, (caixa_id,))

        resultado = cursor.fetchone()

        return float(resultado[0]) if resultado else 0

    except Exception as erro:
        print("Erro obter_saldo_caixa:", erro)
        return 0

    finally:
        cursor.close()
        conn.close()