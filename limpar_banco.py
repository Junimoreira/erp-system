from database.connection import conectar


conn = conectar()
cursor = conn.cursor()

tabelas = [
    "itens_venda",
    "vendas",
    "movimentacoes",
    "contas_pagar",
    "contas_receber",
    "despesas",
    "clientes",
    "produtos"
]

for tabela in tabelas:

    cursor.execute(
        f"TRUNCATE TABLE {tabela} RESTART IDENTITY CASCADE"
    )

conn.commit()

cursor.close()
conn.close()

print("Banco limpo com sucesso!")