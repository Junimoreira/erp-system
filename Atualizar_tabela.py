from database.connection import conectar


def atualizar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

        ALTER TABLE produtos
        ADD CONSTRAINT produtos_codigo_barras_unique UNIQUE (codigo_barras);

    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Coluna adicionada!")


atualizar_tabela()