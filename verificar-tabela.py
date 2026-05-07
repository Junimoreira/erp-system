from database.connection import conectar

try:

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)

    tabelas = cur.fetchall()

    print("\n📦 TABELAS DO BANCO:\n")

    for tabela in tabelas:
        print("✅", tabela[0])

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Erro:", e)