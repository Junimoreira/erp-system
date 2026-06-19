import pandas as pd
from database.connection import conectar


# ==================================================
# TRATAMENTO TEXTO
# ==================================================
def tratar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


# ==================================================
# VALIDAR TIPO
# ==================================================
def validar_tipo(tipo):
    tipo = tratar_texto(tipo).lower()

    if tipo not in ["entrada", "saida"]:
        raise ValueError("Tipo inválido.")

    return tipo


# ==================================================
# REGISTRAR MOVIMENTAÇÃO
# ==================================================
def registrar_movimentacao(
    caixa_id,
    tipo,
    valor,
    descricao,
    categoria,
    origem,
    data_movimentacao,
    meio="CAIXA"
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        caixa_id = int(caixa_id)
        tipo = validar_tipo(tipo)
        valor = float(valor)

        descricao = tratar_texto(descricao)
        categoria = tratar_texto(categoria)
        origem = tratar_texto(origem)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        cursor.execute("""
            SELECT id
            FROM caixa
            WHERE id = %s
        """, (caixa_id,))

        if not cursor.fetchone():
            raise ValueError("Caixa não encontrado.")

        cursor.execute("""
            INSERT INTO movimentacoes (
                caixa_id,
                tipo,
                valor,
                descricao,
                categoria,
                origem,
                data_movimentacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            caixa_id,
            tipo,
            valor,
            descricao,
            categoria,
            origem,
            data_movimentacao
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao registrar movimentação:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# LISTAR MOVIMENTAÇÕES POR CAIXA
# ==================================================
def listar_movimentacoes_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT *
            FROM movimentacoes
            WHERE caixa_id = %s
            ORDER BY id DESC
        """

        df = pd.read_sql(query, conn, params=[caixa_id])

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.fillna("")

        if "data_movimentacao" in df.columns:
            df["data_movimentacao"] = pd.to_datetime(
                df["data_movimentacao"],
                errors="coerce"
            )

        return df

    except Exception as erro:
        print("Erro ao listar movimentações:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# LISTAR POR PERÍODO
# ==================================================
def listar_movimentacoes_periodo(data_inicio, data_fim):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT *
            FROM movimentacoes
            WHERE DATE(data_movimentacao)
            BETWEEN %s AND %s
            ORDER BY data_movimentacao DESC
        """

        df = pd.read_sql(query, conn, params=[data_inicio, data_fim])
        return df.fillna("")

    except Exception as erro:
        print("Erro listar período:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# ATUALIZAR MOVIMENTAÇÃO
# ==================================================
def atualizar_movimentacao(id_movimentacao, tipo, valor, descricao, categoria, origem):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        id_movimentacao = int(id_movimentacao)
        tipo = validar_tipo(tipo)
        valor = float(valor)

        cursor.execute("""
            UPDATE movimentacoes
            SET tipo = %s,
                valor = %s,
                descricao = %s,
                categoria = %s,
                origem = %s
            WHERE id = %s
        """, (
            tipo,
            valor,
            descricao,
            categoria,
            origem,
            id_movimentacao
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao atualizar movimentação:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR MOVIMENTAÇÃO
# ==================================================
def excluir_movimentacao(id_movimentacao):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM movimentacoes
            WHERE id = %s
        """, (int(id_movimentacao),))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao excluir movimentação:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# RESUMOS
# ==================================================
def resumo_movimentacoes():

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(valor),0)
            FROM movimentacoes
            WHERE LOWER(tipo)='entrada'
        """)
        entradas = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(valor),0)
            FROM movimentacoes
            WHERE LOWER(tipo)='saida'
        """)
        saidas = float(cursor.fetchone()[0])

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas
        }

    except Exception as erro:
        print("Erro resumo movimentações:", erro)
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    finally:
        cursor.close()
        conn.close()


# ==================================================
# RESUMO POR PERÍODO
# ==================================================
def resumo_por_periodo(data_inicio, data_fim):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(valor),0)
            FROM movimentacoes
            WHERE LOWER(tipo)='entrada'
            AND DATE(data_movimentacao) BETWEEN %s AND %s
        """, (data_inicio, data_fim))

        entradas = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(valor),0)
            FROM movimentacoes
            WHERE LOWER(tipo)='saida'
            AND DATE(data_movimentacao) BETWEEN %s AND %s
        """, (data_inicio, data_fim))

        saidas = float(cursor.fetchone()[0])

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas
        }

    except Exception as erro:
        print("Erro resumo período:", erro)
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    finally:
        cursor.close()
        conn.close()


# ==================================================
# LISTAR TODAS MOVIMENTAÇÕES
# ==================================================
def listar_movimentacoes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT *
            FROM movimentacoes
            ORDER BY data_movimentacao DESC, id DESC
        """

        df = pd.read_sql(query, conn)

        if df is None or df.empty:
            return pd.DataFrame()

        return df.fillna("")

    except Exception as erro:
        print("Erro ao listar movimentações:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RESUMO CAIXA
# ==================================================
def resumo_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COALESCE(SUM(valor),0)
            FROM movimentacoes
            WHERE caixa_id = %s AND tipo='entrada'
        """, (caixa_id,))

        entradas = float(cursor.fetchone()[0])

        cursor.execute("""
            SELECT COALESCE(SUM(valor),0)
            FROM movimentacoes
            WHERE caixa_id = %s AND tipo='saida'
        """, (caixa_id,))

        saidas = float(cursor.fetchone()[0])

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas
        }

    except Exception as erro:
        print("Erro resumo caixa:", erro)
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    finally:
        cursor.close()
        conn.close()