import os
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"


def obter_database_url():
    ambiente = os.getenv("ERP_ENV", "TESTE").upper()

    if ambiente == "PROD":
        return os.getenv("DATABASE_URL_PROD"), ambiente

    return os.getenv("DATABASE_URL_TESTE"), ambiente


def localizar_executavel(nome):
    caminhos = [
        rf"C:\Program Files\PostgreSQL\18\bin\{nome}.exe",
        rf"C:\Program Files\PostgreSQL\17\bin\{nome}.exe",
        rf"C:\Program Files\PostgreSQL\16\bin\{nome}.exe",
        rf"C:\Program Files\PostgreSQL\15\bin\{nome}.exe",
        rf"C:\Program Files\PostgreSQL\14\bin\{nome}.exe",
        nome
    ]

    for caminho in caminhos:
        if caminho == nome or os.path.exists(caminho):
            return caminho

    return None


def preparar_env(database_url):
    parsed = urlparse(database_url)

    env = os.environ.copy()

    if parsed.password:
        env["PGPASSWORD"] = parsed.password

    return env


def montar_parametros_banco(database_url):
    parsed = urlparse(database_url)

    return {
        "host": parsed.hostname,
        "port": str(parsed.port or 5432),
        "user": parsed.username,
        "dbname": parsed.path.replace("/", "")
    }


def criar_backup():
    try:
        database_url, ambiente = obter_database_url()

        if not database_url:
            return {
                "sucesso": False,
                "mensagem": "DATABASE_URL não encontrada no arquivo .env.",
                "arquivo": None
            }

        pg_dump = localizar_executavel("pg_dump")

        if not pg_dump:
            return {
                "sucesso": False,
                "mensagem": "pg_dump não encontrado. Verifique se o PostgreSQL está instalado.",
                "arquivo": None
            }

        BACKUP_DIR.mkdir(exist_ok=True)

        data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"backup_{ambiente}_{data_hora}.backup"
        caminho_backup = BACKUP_DIR / nome_arquivo

        banco = montar_parametros_banco(database_url)
        env = preparar_env(database_url)

        comando = [
            pg_dump,
            "-h", banco["host"],
            "-p", banco["port"],
            "-U", banco["user"],
            "-F", "c",
            "-b",
            "-v",
            "-f", str(caminho_backup),
            banco["dbname"]
        ]

        resultado = subprocess.run(
            comando,
            env=env,
            capture_output=True,
            text=True
        )

        if resultado.returncode != 0:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao gerar backup: {resultado.stderr}",
                "arquivo": None
            }

        return {
            "sucesso": True,
            "mensagem": "Backup gerado com sucesso.",
            "arquivo": str(caminho_backup)
        }

    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro inesperado ao gerar backup: {e}",
            "arquivo": None
        }


def listar_backups():
    try:
        BACKUP_DIR.mkdir(exist_ok=True)

        arquivos = []

        for arquivo in BACKUP_DIR.glob("*.backup"):
            stat = arquivo.stat()

            arquivos.append({
                "arquivo": arquivo.name,
                "data": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S"),
                "tamanho_mb": round(stat.st_size / (1024 * 1024), 2),
                "caminho": str(arquivo)
            })

        arquivos.sort(key=lambda x: x["data"], reverse=True)

        return arquivos

    except Exception:
        return []


def restaurar_backup(caminho_backup):
    try:
        database_url, ambiente = obter_database_url()

        if not database_url:
            return {
                "sucesso": False,
                "mensagem": "DATABASE_URL não encontrada no arquivo .env."
            }

        caminho_backup = Path(caminho_backup)

        if not caminho_backup.exists():
            return {
                "sucesso": False,
                "mensagem": "Arquivo de backup não encontrado."
            }

        pg_restore = localizar_executavel("pg_restore")

        if not pg_restore:
            return {
                "sucesso": False,
                "mensagem": "pg_restore não encontrado. Verifique se o PostgreSQL está instalado."
            }

        banco = montar_parametros_banco(database_url)
        env = preparar_env(database_url)

        comando = [
            pg_restore,
            "-h", banco["host"],
            "-p", banco["port"],
            "-U", banco["user"],
            "-d", banco["dbname"],
            "--clean",
            "--if-exists",
            "--no-owner",
            "--verbose",
            str(caminho_backup)
        ]

        resultado = subprocess.run(
            comando,
            env=env,
            capture_output=True,
            text=True
        )

        if resultado.returncode != 0:
            return {
                "sucesso": False,
                "mensagem": f"Erro ao restaurar backup: {resultado.stderr}"
            }

        return {
            "sucesso": True,
            "mensagem": f"Backup restaurado com sucesso no ambiente {ambiente}."
        }

    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro inesperado ao restaurar backup: {e}"
        }