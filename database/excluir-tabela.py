from connection import conectar

conn = conectar()
cursor = conn.cursor()

cursor.execute("""
    SELECT
        tipo,
        descricao,
        valor,
        origem
    FROM fluxo_caixa
    ORDER BY id DESC;
""")

dados = cursor.fetchall()

for item in dados:

    print(item)

cursor.close()
conn.close()