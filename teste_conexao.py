from database.connection import conectar

conn = conectar()

if conn:

    print("Conectado com sucesso!")

    conn.close()

else:

    print("Erro na conexão.")