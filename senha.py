import bcrypt

senha = "123456"

hash_senha = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()

print(hash_senha)



UPDATE usuarios
SET senha = '$2b$12$bL83aNQtzA7mZPNjXngw6eMSnMSdfefqZ525Kpi6qadIOmbAKwdau'
WHERE usuario = 'atendente';