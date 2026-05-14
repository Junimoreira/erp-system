from connection import conectar

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
DROP TABLE IF EXISTS itens_venda CASCADE;
DROP TABLE IF EXISTS vendas CASCADE;
""")

conn.commit()

cursor.close()
conn.close()

print("Tabelas removidas com sucesso!")