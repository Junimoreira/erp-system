import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def conectar():

    database_url = os.getenv("DATABASE_URL")

    print("DATABASE_URL =", database_url)

    if not database_url:
        raise Exception("DATABASE_URL não encontrada")

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )

    print("✅ CONEXÃO COM POSTGRES REALIZADA COM SUCESSO")

    return conn