from database.connection import conectar

try:
    conn = conectar()
    print("Conectado com sucesso!")
    conn.close()

except Exception as e:
    print("Erro:", e)