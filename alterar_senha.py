import bcrypt
from database.connection import conectar


usuario = "admin"
nova_senha = "Verde@@2026"

# gera hash
senha_hash = bcrypt.hashpw(
    nova_senha.encode(),
    bcrypt.gensalt()
).decode()

conn = conectar()
cur = conn.cursor()

cur.execute("""
    UPDATE usuarios
    SET senha = %s
    WHERE usuario = %s
""", (senha_hash, usuario))

conn.commit()

cur.close()
conn.close()

print("✅ Senha alterada com sucesso!")