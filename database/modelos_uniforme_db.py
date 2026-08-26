from database.connection import conectar


# =========================================================
# LISTAR MODELOS DE UNIFORME
# =========================================================
def listar_modelos_uniforme(apenas_ativos=True):

    conn = conectar()

    if conn is None:
        return []

    try:

        cursor = conn.cursor()

        if apenas_ativos:

            cursor.execute(
                """
                SELECT
                    id,
                    codigo,
                    nome,
                    ativo
                FROM modelos_uniforme
                WHERE ativo = TRUE
                ORDER BY codigo
                """
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    codigo,
                    nome,
                    ativo
                FROM modelos_uniforme
                ORDER BY codigo
                """
            )

        colunas = [
            "id",
            "codigo",
            "nome",
            "ativo"
        ]

        return [
            dict(zip(colunas, linha))
            for linha in cursor.fetchall()
        ]

    except Exception as erro:

        print(
            "Erro ao listar modelos de uniforme:",
            erro
        )

        return []

    finally:

        conn.close()


# =========================================================
# CADASTRAR MODELO DE UNIFORME
# =========================================================
def cadastrar_modelo_uniforme(
    nome,
    codigo=None
):

    conn = conectar()

    if conn is None:
        return False

    try:

        cursor = conn.cursor()

        nome = str(nome).strip()

        if not nome:
            return False

        if codigo is None:

            cursor.execute(
                """
                SELECT
                    COALESCE(MAX(codigo), 0) + 1
                FROM modelos_uniforme
                """
            )

            codigo = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO modelos_uniforme (
                codigo,
                nome,
                ativo
            )
            VALUES (%s, %s, TRUE)
            """,
            (
                int(codigo),
                nome
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao cadastrar modelo de uniforme:",
            erro
        )

        return False

    finally:

        conn.close()