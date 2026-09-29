from database.connection import conectar


# ==================================================
# VERIFICAR CATALOGO DE CATEGORIAS
# ==================================================
def catalogo_categorias_disponivel():

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'categorias_produtos'
            )
            """
        )

        resultado = cursor.fetchone()

        return bool(
            resultado
            and resultado[0]
        )

    except Exception:

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR CATEGORIAS ATIVAS
# ==================================================
def listar_categorias_ativas():

    conn = conectar()

    if conn is None:
        return []

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                nome,
                grupo
            FROM categorias_produtos
            WHERE ativo = TRUE
            ORDER BY
                grupo,
                nome
            """
        )

        linhas = cursor.fetchall()

        return [
            {
                "id": linha[0],
                "nome": linha[1],
                "grupo": linha[2]
            }
            for linha in linhas
        ]

    except Exception:

        return []

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR GRUPOS ATIVOS
# ==================================================
def listar_grupos_ativos():

    conn = conectar()

    if conn is None:
        return []

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT DISTINCT
                grupo
            FROM categorias_produtos
            WHERE ativo = TRUE
              AND grupo IS NOT NULL
              AND TRIM(grupo) <> ''
            ORDER BY grupo
            """
        )

        return [
            linha[0]
            for linha in cursor.fetchall()
        ]

    except Exception:

        return []

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR CATEGORIAS POR GRUPO
# ==================================================
def listar_categorias_por_grupo(grupo):

    if not grupo:
        return []

    conn = conectar()

    if conn is None:
        return []

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                nome,
                grupo
            FROM categorias_produtos
            WHERE ativo = TRUE
              AND UPPER(TRIM(grupo)) = UPPER(TRIM(%s))
            ORDER BY nome
            """,
            (grupo,)
        )

        linhas = cursor.fetchall()

        return [
            {
                "id": linha[0],
                "nome": linha[1],
                "grupo": linha[2]
            }
            for linha in linhas
        ]

    except Exception:

        return []

    finally:

        cursor.close()
        conn.close()


# ==================================================
# BUSCAR CATEGORIA PELO NOME
# ==================================================
def buscar_categoria_por_nome(nome):

    if not nome:
        return None

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                nome,
                grupo,
                ativo
            FROM categorias_produtos
            WHERE UPPER(TRIM(nome)) = UPPER(TRIM(%s))
            LIMIT 1
            """,
            (nome,)
        )

        linha = cursor.fetchone()

        if linha is None:
            return None

        return {
            "id": linha[0],
            "nome": linha[1],
            "grupo": linha[2],
            "ativo": linha[3]
        }

    except Exception:

        return None

    finally:

        cursor.close()
        conn.close()
