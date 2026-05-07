import psycopg2
import os

from dotenv import load_dotenv

load_dotenv()

def conectar():

    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        sslmode="require"
    )

    return conn