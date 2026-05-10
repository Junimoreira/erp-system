from database.connection import conectar


def criar_tabelas():

    conn = conectar()

    cursor = conn.cursor()

    with open("schema.sql", "r", encoding="utf-8") as arquivo:

        sql = arquivo.read()

    cursor.execute(sql)

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ Tabelas criadas com sucesso!")


criar_tabelas()