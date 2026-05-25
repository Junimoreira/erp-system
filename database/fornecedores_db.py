import pandas as pd
from database.connection import conectar


# ==================================================
# LISTAR FORNECEDORES
# ==================================================
def listar_fornecedores():

    conn = conectar()

    try:

        query = """
            SELECT *
            FROM fornecedores
            ORDER BY id DESC
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        print("Erro ao listar fornecedores:", erro)

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# BUSCAR FORNECEDOR POR ID
# ==================================================
def buscar_fornecedor_por_id(fornecedor_id):

    conn = conectar()

    try:

        query = """
            SELECT *
            FROM fornecedores
            WHERE id = %s
        """

        df = pd.read_sql(
            query,
            conn,
            params=(int(fornecedor_id),)
        )

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    except Exception as erro:

        print("Erro ao buscar fornecedor:", erro)

        return None

    finally:

        conn.close()


# ==================================================
# CADASTRAR FORNECEDOR
# ==================================================
def cadastrar_fornecedor(
    razao_social,
    nome_fantasia,
    cnpj,
    inscricao_estadual,
    telefone,
    email,
    endereco,
    numero,
    bairro,
    cidade,
    estado,
    cep,
    contato_responsavel,
    observacoes
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO fornecedores (
                razao_social,
                nome_fantasia,
                cnpj,
                inscricao_estadual,
                telefone,
                email,
                endereco,
                numero,
                bairro,
                cidade,
                estado,
                cep,
                contato_responsavel,
                observacoes
            )
            VALUES (
                %s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s
            )
        """, (
            razao_social,
            nome_fantasia,
            cnpj,
            inscricao_estadual,
            telefone,
            email,
            endereco,
            numero,
            bairro,
            cidade,
            estado,
            cep,
            contato_responsavel,
            observacoes
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao cadastrar fornecedor:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR FORNECEDOR
# ==================================================
def atualizar_fornecedor(
    fornecedor_id,
    razao_social,
    nome_fantasia,
    cnpj,
    inscricao_estadual,
    telefone,
    email,
    endereco,
    numero,
    bairro,
    cidade,
    estado,
    cep,
    contato_responsavel,
    observacoes
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE fornecedores
            SET
                razao_social = %s,
                nome_fantasia = %s,
                cnpj = %s,
                inscricao_estadual = %s,
                telefone = %s,
                email = %s,
                endereco = %s,
                numero = %s,
                bairro = %s,
                cidade = %s,
                estado = %s,
                cep = %s,
                contato_responsavel = %s,
                observacoes = %s
            WHERE id = %s
        """, (
            razao_social,
            nome_fantasia,
            cnpj,
            inscricao_estadual,
            telefone,
            email,
            endereco,
            numero,
            bairro,
            cidade,
            estado,
            cep,
            contato_responsavel,
            observacoes,
            int(fornecedor_id)
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao atualizar fornecedor:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR FORNECEDOR
# ==================================================
def excluir_fornecedor(fornecedor_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM fornecedores
            WHERE id = %s
        """, (
            int(fornecedor_id),
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao excluir fornecedor:", erro)

        return False

    finally:

        cursor.close()
        conn.close()