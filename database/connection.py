import os
from urllib.parse import urlparse

import psycopg2
from dotenv import load_dotenv


# ============================================================
# CARREGAR .ENV
# ============================================================
load_dotenv(
    encoding="utf-8"
)


# ============================================================
# AMBIENTE DO ERP
#
# TESTE = homologação / desenvolvimento
# PROD  = produção
# ============================================================
ERP_ENV = (
    os.getenv(
        "ERP_ENV",
        "TESTE"
    )
    .strip()
    .upper()
)


# ============================================================
# VALIDAR AMBIENTE
# ============================================================
if ERP_ENV not in (
    "TESTE",
    "PROD",
):

    raise RuntimeError(
        "ERP_ENV inválido. "
        "Use TESTE ou PROD."
    )


# ============================================================
# DEFINIR URL DO BANCO
# ============================================================
if ERP_ENV == "PROD":

    DATABASE_URL = os.getenv(
        "DATABASE_URL_PROD"
    )

else:

    DATABASE_URL = os.getenv(
        "DATABASE_URL_TESTE"
    )


# ============================================================
# IDENTIFICAR BANCO SEM EXPOR CREDENCIAIS
# ============================================================
def _informacoes_conexao_seguras():

    if not DATABASE_URL:

        return {
            "banco": "NÃO CONFIGURADO",
            "host": "NÃO CONFIGURADO",
            "tipo": "DESCONHECIDO",
        }

    try:

        parsed = urlparse(
            DATABASE_URL
        )

        host = (
            parsed.hostname
            or
            "desconhecido"
        )

        banco = (
            parsed.path
            .lstrip("/")
            .split("?")[0]
            or
            "desconhecido"
        )

        host_lower = host.lower()

        if host_lower in (
            "localhost",
            "127.0.0.1",
            "::1",
        ):

            tipo = "LOCAL"

        else:

            tipo = "NUVEM"

        return {
            "banco": banco,
            "host": host,
            "tipo": tipo,
        }

    except Exception:

        return {
            "banco": "desconhecido",
            "host": "desconhecido",
            "tipo": "desconhecido",
        }


INFO_CONEXAO = (
    _informacoes_conexao_seguras()
)


# ============================================================
# PROTEÇÕES DE AMBIENTE
# ============================================================
def _validar_seguranca_ambiente():

    if not DATABASE_URL:

        raise RuntimeError(
            "URL do banco não configurada "
            f"para o ambiente {ERP_ENV}."
        )

    banco = (
        INFO_CONEXAO.get(
            "banco",
            ""
        )
        .lower()
    )

    # --------------------------------------------------------
    # PROTEÇÃO DO AMBIENTE DE TESTE
    # --------------------------------------------------------
    if ERP_ENV == "TESTE":

        nomes_permitidos_teste = (
            "erp_local",
            "erp_teste",
            "erp_homologacao",
        )

        if banco not in nomes_permitidos_teste:

            raise RuntimeError(
                "BLOQUEIO DE SEGURANÇA: "
                "o ambiente TESTE está apontando "
                f"para o banco '{banco}', que não está "
                "na lista de bancos de teste/homologação."
            )

    # --------------------------------------------------------
    # PROTEÇÃO DE PRODUÇÃO
    # --------------------------------------------------------
    if ERP_ENV == "PROD":

        if banco in (
            "erp_local",
            "erp_teste",
            "erp_homologacao",
        ):

            raise RuntimeError(
                "BLOQUEIO DE SEGURANÇA: "
                "o ambiente PROD está apontando "
                "para um banco de teste/homologação."
            )


_validar_seguranca_ambiente()


# ============================================================
# LOG INICIAL SEGURO
# ============================================================
print()
print("=" * 60)
print("ERP VERDE INFÂNCIA")
print("=" * 60)
print(
    f"Ambiente atual: {ERP_ENV}"
)
print(
    "Banco:",
    INFO_CONEXAO.get(
        "banco"
    )
)
print(
    "Servidor:",
    INFO_CONEXAO.get(
        "tipo"
    )
)
print(
    "Host:",
    INFO_CONEXAO.get(
        "host"
    )
)
print("=" * 60)
print()


# ============================================================
# CONECTAR AO BANCO
# ============================================================
def conectar():

    try:

        print(
            "Tentando conectar ao banco..."
        )

        if not DATABASE_URL:

            print(
                "DATABASE_URL não encontrada."
            )

            return None

        # ----------------------------------------------------
        # CONEXÃO
        #
        # O Render já fornece URL compatível.
        # Para conexões externas usamos SSL obrigatório.
        # ----------------------------------------------------
        if (
            INFO_CONEXAO.get(
                "tipo"
            )
            ==
            "NUVEM"
        ):

            conn = psycopg2.connect(
                DATABASE_URL,
                sslmode="require",
                connect_timeout=15,
            )

        else:

            conn = psycopg2.connect(
                DATABASE_URL,
                connect_timeout=10,
            )

        # ----------------------------------------------------
        # CONFIRMAR BANCO REALMENTE CONECTADO
        # ----------------------------------------------------
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                current_database(),
                current_user;
            """
        )

        banco, usuario = (
            cursor.fetchone()
        )

        cursor.close()

        print(
            f"Banco conectado: {banco}"
        )

        print(
            f"Usuário: {usuario}"
        )

        return conn

    except Exception as erro:

        print()
        print(
            "ERRO AO CONECTAR NO BANCO:"
        )

        print(
            type(
                erro
            ).__name__
        )

        print(
            erro
        )

        return None