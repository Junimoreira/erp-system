from database.connection import conectar

with open("database/schema.sql", "r", encoding="utf-8") as arquivo:
    sql = arquivo.read()

try:

    conn = conectar()
    cur = conn.cursor()

    cur.execute(sql)

    conn.commit()

    print("✅ Banco criado com sucesso!")

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Erro:", e)