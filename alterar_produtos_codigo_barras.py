from database.connection import conectar

try:

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN codigo_barras VARCHAR(100)
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("✅ Coluna codigo_barras adicionada!")

except Exception as erro:

    print("❌ Erro:", erro)