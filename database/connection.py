import os
import psycopg2

from dotenv import load_dotenv


# =====================================
# CARREGA .ENV
# =====================================
load_dotenv()


# =====================================
# DEFINE AMBIENTE
# =====================================
ERP_ENV = os.getenv(
    "ERP_ENV",
    "TESTE"
).upper()


# =====================================
# DEFINE URL CONFORME AMBIENTE
# =====================================
if ERP_ENV == "PROD":

    DATABASE_URL = os.getenv(
        "DATABASE_URL_PROD"
    )

else:

    DATABASE_URL = os.getenv(
        "DATABASE_URL_TESTE"
    )


print(f"\n🌎 Ambiente atual: {ERP_ENV}")

print(f"🔗 DATABASE_URL: {DATABASE_URL}\n")


# =====================================
# CONEXÃO BANCO
# =====================================
def conectar():

    try:

        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode="require"
        )

        return conn

    except Exception as erro:

        print("\n❌ ERRO AO CONECTAR NO BANCO:")

        print(erro)

        return None