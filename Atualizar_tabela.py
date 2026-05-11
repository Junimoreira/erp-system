from database.connection import conectar


def atualizar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    sql = """
    ALTER TABLE financeiro
    ALTER COLUMN data_lancamento
    SET DEFAULT CURRENT_DATE;
    """

    cursor.execute(sql)

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ Tabela atualizada com sucesso!")


atualizar_tabela()