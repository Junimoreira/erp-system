import os
from dotenv import load_dotenv

load_dotenv()

ERP_ENV = os.getenv("ERP_ENV", "TESTE").upper()

DATABASE_URL = (
    os.getenv("DATABASE_URL_PROD")
    if ERP_ENV == "PROD"
    else os.getenv("DATABASE_URL_TESTE")
)

def is_prod():
    return ERP_ENV == "PROD"