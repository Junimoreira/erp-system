import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

# força carregar .env da raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


def conectar():
    try:
        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            raise Exception("DATABASE_URL não encontrada no ambiente")

        conn = psycopg2.connect(database_url)

        #print("✔ Conexão OK com PostgreSQL")

        return conn

    except Exception as erro:
        print("❌ ERRO AO CONECTAR NO BANCO:")
        print(erro)
        return None