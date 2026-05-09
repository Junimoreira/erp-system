import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def conectar():

    database_url = os.getenv("DATABASE_URL")

    print("DATABASE_URL =", postgresql://bd_erp_system_user:QEEydMjHue8CdduUnbcjOnSdKp7dQSbG@dpg-d7uc7aho3t8c73fao0rg-a/bd_erp_system

    if not database_url:
        raise Exception("DATABASE_URL não encontrada")

    return psycopg2.connect(
        database_url,
        sslmode="require"
    )

