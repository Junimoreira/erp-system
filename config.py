import os

# =========================
# AMBIENTE DO SISTEMA
# =========================
ENV = os.getenv("ERP_ENV", "TESTE")  # TESTE ou PROD

# =========================
# CONFIGURAÇÃO BANCO
# =========================
DB_CONFIG = {

    "TESTE": {
        "host": "localhost",
        "database": "erp_teste",
        "user": "postgres",
        "password": "sua_senha"
    },

    "PROD": {
        "host": "localhost",
        "database": "erp_loja",
        "user": "postgres",
        "password": "sua_senha"
    }
}