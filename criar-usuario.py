import bcrypt
from database.connection import conectar

nome = "Administrador"
usuario = "admin"
senha = "123456@"

senha_hash = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()

conn = conectar()
cur = conn.cursor()

cur.execute("""
    INSERT INTO usuarios
    (nome, usuario, senha)

    VALUES (%s, %s, %s)
""", (nome, usuario, senha_hash))

conn.commit()

print("✅ Usuário criado!")

cur.close()
conn.close()