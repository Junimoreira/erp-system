from database.connection import conectar

with open("criar-tabela.py", "r", encoding="utf-8") as arquivo:
    sql = arquivo.read()

try:

    conn = conectar()
    cur = conn.cursor()

    cur.execute(sql)

    conn.commit()

    print("✅ tabela criada criado com sucesso!")

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Erro:", e)