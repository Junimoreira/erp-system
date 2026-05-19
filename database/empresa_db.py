import psycopg2
from database.connection import conectar


def buscar_empresa():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, cnpj, telefone, endereco, email, logo
        FROM empresa
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "nome": row[1],
            "cnpj": row[2],
            "telefone": row[3],
            "endereco": row[4],
            "email": row[5],
            "logo": row[6]
        }

    return None


def salvar_empresa(nome, cnpj, telefone, endereco, email, logo_bytes):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM empresa ORDER BY id DESC LIMIT 1
    """)

    existe = cursor.fetchone()

    if existe is None:

        cursor.execute("""
            INSERT INTO empresa (
                nome, cnpj, telefone, endereco, email, logo
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (nome, cnpj, telefone, endereco, email, logo_bytes))

    else:

        cursor.execute("""
            UPDATE empresa
            SET nome=%s, cnpj=%s, telefone=%s,
                endereco=%s, email=%s, logo=%s
            WHERE id=%s
        """, (nome, cnpj, telefone, endereco, email, logo_bytes, existe[0]))

    conn.commit()
    conn.close()

    return True