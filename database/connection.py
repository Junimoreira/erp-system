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


# =====================================
# LOG INICIAL
# =====================================
print("\n" + "=" * 60)
print(f"🌎 Ambiente atual: {ERP_ENV}")
print(f"🔗 DATABASE_URL: {DATABASE_URL}")
print("=" * 60 + "\n")


# =====================================
# CONEXÃO BANCO
# =====================================
def conectar():

    try:

        print("\n🔄 Tentando conectar ao banco...")

        if ERP_ENV == "PROD":

            conn = psycopg2.connect(
                DATABASE_URL,
                sslmode="require"
            )

        else:

            conn = psycopg2.connect(
                DATABASE_URL
            )

        print("✅ Conexão realizada com sucesso!")

        return conn

    except Exception as erro:

        print("\n❌ ERRO AO CONECTAR NO BANCO:")
        print(type(erro).__name__)
        print(erro)

        return None