from database.connection import conectar


try:

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS empresa (
    id SERIAL PRIMARY KEY,
    nome TEXT,
    cnpj TEXT,
    telefone TEXT,
    endereco TEXT,
    email TEXT,
    logo BYTEA
);

        

    """)

    conn.commit()

    print("✅ Tabela empresa criada com sucesso!")

except Exception as erro:

    print("❌ Erro:", erro)

finally:

    cursor.close()
    conn.close()