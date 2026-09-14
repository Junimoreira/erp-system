from database.connection import conectar


# ============================================================
# BUSCAR EMPRESA
# ============================================================
def buscar_empresa():

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                cnpj,
                telefone,
                endereco,
                email,
                logo
            FROM empresa
            ORDER BY id DESC
            LIMIT 1
            """
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "nome": row[1],
            "cnpj": row[2],
            "telefone": row[3],
            "endereco": row[4],
            "email": row[5],
            "logo": row[6]
        }

    except Exception as erro:

        print(
            "Erro ao buscar empresa:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# SALVAR EMPRESA
#
# Se logo_bytes=None:
# - mantém a logo atual
#
# Se logo_bytes possuir bytes:
# - substitui a logo
# ============================================================
def salvar_empresa(
    nome,
    cnpj,
    telefone,
    endereco,
    email,
    logo_bytes=None
):

    conn = conectar()

    if conn is None:
        return False

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                logo
            FROM empresa
            ORDER BY id DESC
            LIMIT 1
            """
        )

        existe = cursor.fetchone()

        # ----------------------------------------------------
        # NOVO REGISTRO
        # ----------------------------------------------------
        if existe is None:

            cursor.execute(
                """
                INSERT INTO empresa (
                    nome,
                    cnpj,
                    telefone,
                    endereco,
                    email,
                    logo
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    nome,
                    cnpj,
                    telefone,
                    endereco,
                    email,
                    logo_bytes
                )
            )

        # ----------------------------------------------------
        # ATUALIZAR REGISTRO EXISTENTE
        # ----------------------------------------------------
        else:

            empresa_id = existe[0]
            logo_atual = existe[1]

            logo_final = (
                logo_bytes
                if logo_bytes is not None
                else logo_atual
            )

            cursor.execute(
                """
                UPDATE empresa
                SET
                    nome = %s,
                    cnpj = %s,
                    telefone = %s,
                    endereco = %s,
                    email = %s,
                    logo = %s
                WHERE id = %s
                """,
                (
                    nome,
                    cnpj,
                    telefone,
                    endereco,
                    email,
                    logo_final,
                    empresa_id
                )
            )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao salvar empresa:",
            erro
        )

        return False

    finally:

        conn.close()


# ============================================================
# ATUALIZAR SOMENTE A LOGO
# ============================================================
def atualizar_logo_empresa(
    logo_bytes
):

    conn = conectar()

    if conn is None:
        return False

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM empresa
            ORDER BY id DESC
            LIMIT 1
            """
        )

        registro = cursor.fetchone()

        if not registro:

            return False

        cursor.execute(
            """
            UPDATE empresa
            SET logo = %s
            WHERE id = %s
            """,
            (
                logo_bytes,
                registro[0]
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao atualizar logo da empresa:",
            erro
        )

        return False

    finally:

        conn.close()


# ============================================================
# REMOVER LOGO
# ============================================================
def remover_logo_empresa():

    conn = conectar()

    if conn is None:
        return False

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM empresa
            ORDER BY id DESC
            LIMIT 1
            """
        )

        registro = cursor.fetchone()

        if not registro:
            return False

        cursor.execute(
            """
            UPDATE empresa
            SET logo = NULL
            WHERE id = %s
            """,
            (
                registro[0],
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao remover logo da empresa:",
            erro
        )

        return False

    finally:

        conn.close()