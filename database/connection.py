import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def conectar():

    try:

        database_url = os.getenv("DATABASE_URL")

        if not database_url:

            raise Exception(
                "DATABASE_URL não encontrada."
            )

        conn = psycopg2.connect(database_url)

        return conn

    except Exception as erro:

        print("Erro ao conectar:", erro)

        return None