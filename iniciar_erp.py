from pathlib import Path
import os
import subprocess
import sys

from dotenv import load_dotenv


# ============================================================
# DIRETÓRIO DO ERP
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

os.chdir(BASE_DIR)


# ============================================================
# CARREGAR .ENV
# ============================================================
load_dotenv(
    BASE_DIR / ".env",
    encoding="utf-8"
)


# ============================================================
# AMBIENTE
# ============================================================
erp_env = (
    os.getenv(
        "ERP_ENV",
        "TESTE"
    )
    .strip()
    .upper()
)

if erp_env == "PROD":
    database_url = os.getenv(
        "DATABASE_URL_PROD"
    )
else:
    database_url = os.getenv(
        "DATABASE_URL_TESTE"
    )


# ============================================================
# CONFERÊNCIA SEGURA
# ============================================================
if not database_url:
    print()
    print("=" * 70)
    print("ERP VERDE INFÂNCIA")
    print("=" * 70)
    print("ERRO:")
    print(
        f"Banco não configurado para o ambiente {erp_env}."
    )
    print("=" * 70)
    raise SystemExit(1)


# ============================================================
# INICIAR STREAMLIT
# ============================================================
print()
print("=" * 70)
print("ERP VERDE INFÂNCIA")
print("=" * 70)
print("Ambiente:", erp_env)
print("Python:", sys.executable)
print("=" * 70)
print()

comando = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    str(
        BASE_DIR / "app.py"
    ),
]


try:

    subprocess.run(
        comando,
        check=False,
        cwd=BASE_DIR
    )

except KeyboardInterrupt:

    pass