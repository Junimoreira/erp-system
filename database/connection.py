import os
import psycopg2
from dotenv import load_dotenv


# =====================================
# CARREGA .ENV COM UTF-8
# =====================================
load_dotenv(encoding="utf-8")


# =====================================
# DEFINE AMBIENTE
# =====================================
ERP_ENV = os.getenv("ERP_ENV", "TESTE").upper()


# =====================================
# DEFINE URL CONFORME AMBIENTE
# =====================================
if ERP_ENV == "PROD":
    DATABASE_URL = os.getenv("DATABASE_URL_PROD")
else:
    DATABASE_URL = os.getenv("DATABASE_URL_TESTE")


# =====================================
# LOG INICIAL
# =====================================
print("\n" + "=" * 60)
print(f"Ambiente atual: {ERP_ENV}")
print(f"DATABASE_URL: {DATABASE_URL}")
print("=" * 60 + "\n")


# =====================================
# CONEXÃO BANCO
# =====================================
def conectar():

    try:

        print("\nTentando conectar ao banco...")

        if not DATABASE_URL:
            print("DATABASE_URL não encontrada no .env.")
            return None

        if ERP_ENV == "PROD":
            conn = psycopg2.connect(
                DATABASE_URL,
                sslmode="require"
            )
        else:
            conn = psycopg2.connect(DATABASE_URL)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT current_database(), current_user;
        """)

        banco, usuario = cursor.fetchone()

        print(f"Banco conectado: {banco}")
        print(f"Usuario: {usuario}")

        cursor.close()

        return conn

    except Exception as erro:

        print("\nERRO AO CONECTAR NO BANCO:")
        print(type(erro).__name__)
        print(erro)

        return None