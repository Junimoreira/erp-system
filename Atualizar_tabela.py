from database.connection import conectar


def atualizar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

        ALTER TABLE clientes
        ADD COLUMN cidade VARCHAR(100);

    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Coluna adicionada!")


atualizar_tabela()