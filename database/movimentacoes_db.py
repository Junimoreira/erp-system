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
        raise ValueError("Tipo inválido. Use entrada ou saida.")

    return tipo


# ==================================================
# VALIDAR MEIO
# ==================================================
def validar_meio(meio):
    meio = tratar_texto(meio).upper()

    if meio not in ["CAIXA", "BANCO"]:
        raise ValueError("Meio inválido. Use CAIXA ou BANCO.")

    return meio


# ==================================================
# REGISTRAR MOVIMENTAÇÃO
# ==================================================
def registrar_movimentacao(
    caixa_id=None,
    tipo=None,
    valor=0,
    descricao="",
    categoria="",
    origem="",
    data_movimentacao=None,
    meio="CAIXA",
    referencia_tipo=None,
    referencia_id=None,
    conta_bancaria_id=None,
    usuario=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        tipo = validar_tipo(tipo)
        meio = validar_meio(meio)

        valor = float(valor)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        descricao = tratar_texto(descricao)
        categoria = tratar_texto(categoria)
        origem = tratar_texto(origem).upper()

        if meio == "CAIXA":

            if caixa_id is None:
                raise ValueError("Movimentação em CAIXA exige caixa_id.")

            caixa_id = int(caixa_id)

            cursor.execute("""
                SELECT id
                FROM caixa
                WHERE id = %s
            """, (caixa_id,))

            if not cursor.fetchone():
                raise ValueError("Caixa não encontrado.")

        else:
            caixa_id = None

        if conta_bancaria_id is not None:
            conta_bancaria_id = int(conta_bancaria_id)

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
            VALUES (
                %s, %s, %s, %s, COALESCE(%s, NOW()),
                %s, %s, %s, %s, %s, %s, %s
            )
        """, (
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
            ORDER BY data_movimentacao DESC, id DESC
        """

        df = pd.read_sql(query, conn, params=[caixa_id])

        if df is None or df.empty:
            return pd.DataFrame()

        return df.fillna("")

    except Exception as erro:
        print("Erro ao listar movimentações do caixa:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# LISTAR POR PERÍODO
# ==================================================
def listar_movimentacoes_periodo(data_inicio, data_fim, meio=None):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        if meio:

            meio = validar_meio(meio)

            query = """
                SELECT *
                FROM movimentacoes
                WHERE DATE(data_movimentacao) BETWEEN %s AND %s
                AND meio = %s
                ORDER BY data_movimentacao DESC, id DESC
            """

            df = pd.read_sql(query, conn, params=[data_inicio, data_fim, meio])

        else:

            query = """
                SELECT *
                FROM movimentacoes
                WHERE DATE(data_movimentacao) BETWEEN %s AND %s
                ORDER BY data_movimentacao DESC, id DESC
            """

            df = pd.read_sql(query, conn, params=[data_inicio, data_fim])

        return df.fillna("")

    except Exception as erro:
        print("Erro listar movimentações por período:", erro)
        return pd.DataFrame()

    finally:
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
# ATUALIZAR MOVIMENTAÇÃO
# ==================================================
def atualizar_movimentacao(
    id_movimentacao,
    tipo,
    valor,
    descricao,
    categoria,
    origem,
    meio="CAIXA",
    conta_bancaria_id=None,
    usuario=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        id_movimentacao = int(id_movimentacao)
        tipo = validar_tipo(tipo)
        meio = validar_meio(meio)
        valor = float(valor)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        cursor.execute("""
            UPDATE movimentacoes
            SET
                tipo = %s,
                valor = %s,
                descricao = %s,
                categoria = %s,
                origem = %s,
                meio = %s,
                conta_bancaria_id = %s,
                usuario = %s
            WHERE id = %s
        """, (
            tipo,
            valor,
            descricao,
            categoria,
            origem,
            meio,
            conta_bancaria_id,
            usuario,
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
# RESUMO GERAL
# ==================================================
def resumo_movimentacoes(meio=None):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:

        params = []

        filtro_meio = ""

        if meio:
            meio = validar_meio(meio)
            filtro_meio = "AND meio = %s"
            params.append(meio)

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN LOWER(tipo)='entrada' THEN valor ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN LOWER(tipo)='saida' THEN valor ELSE 0 END),0)
            FROM movimentacoes
            WHERE 1=1
            {filtro_meio}
        """, params)

        entradas, saidas = cursor.fetchone()

        entradas = float(entradas)
        saidas = float(saidas)

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
def resumo_por_periodo(data_inicio, data_fim, meio=None):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:

        params = [data_inicio, data_fim]
        filtro_meio = ""

        if meio:
            meio = validar_meio(meio)
            filtro_meio = "AND meio = %s"
            params.append(meio)

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN LOWER(tipo)='entrada' THEN valor ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN LOWER(tipo)='saida' THEN valor ELSE 0 END),0)
            FROM movimentacoes
            WHERE DATE(data_movimentacao) BETWEEN %s AND %s
            {filtro_meio}
        """, params)

        entradas, saidas = cursor.fetchone()

        entradas = float(entradas)
        saidas = float(saidas)

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
# RESUMO CAIXA
# ==================================================
def resumo_caixa(caixa_id):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN LOWER(tipo)='entrada' THEN valor ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN LOWER(tipo)='saida' THEN valor ELSE 0 END),0)
            FROM movimentacoes
            WHERE caixa_id = %s
            AND meio = 'CAIXA'
        """, (caixa_id,))

        entradas, saidas = cursor.fetchone()

        entradas = float(entradas)
        saidas = float(saidas)

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


# ==================================================
# RESUMO BANCO
# ==================================================
def resumo_banco(conta_bancaria_id=None):

    conn = conectar()

    if conn is None:
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    cursor = conn.cursor()

    try:

        params = []
        filtro_conta = ""

        if conta_bancaria_id is not None:
            filtro_conta = "AND conta_bancaria_id = %s"
            params.append(int(conta_bancaria_id))

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN LOWER(tipo)='entrada' THEN valor ELSE 0 END),0),
                COALESCE(SUM(CASE WHEN LOWER(tipo)='saida' THEN valor ELSE 0 END),0)
            FROM movimentacoes
            WHERE meio = 'BANCO'
            {filtro_conta}
        """, params)

        entradas, saidas = cursor.fetchone()

        entradas = float(entradas)
        saidas = float(saidas)

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas
        }

    except Exception as erro:
        print("Erro resumo banco:", erro)
        return {"entradas": 0, "saidas": 0, "saldo": 0}

    finally:
        cursor.close()
        conn.close()