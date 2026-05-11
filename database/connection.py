import os
import psycopg2


def conectar():
    try:
        database_url = os.getenv("DATABASE_URL")

        print("DATABASE_URL =", database_url)

        conn = psycopg2.connect(
            database_url,
            sslmode="require"
        )

        print("Conexão realizada com sucesso!")

        return conn

    except Exception as e:
        print("Erro ao conectar:", e)
        return None