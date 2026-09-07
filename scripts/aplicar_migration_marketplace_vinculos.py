import argparse
from pathlib import Path

from database.connection import ERP_ENV, INFO_CONEXAO, conectar


ARQUIVO_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "2026_09_07_criar_vinculos_produtos_marketplaces.sql"
)


def exibir_ambiente():
    print()
    print("=" * 70)
    print("MIGRATION - VINCULOS DE PRODUTOS DOS MARKETPLACES")
    print("=" * 70)
    print(f"ERP_ENV: {ERP_ENV}")
    print(
        "Banco:",
        INFO_CONEXAO.get(
            "banco",
            "desconhecido",
        ),
    )
    print(
        "Servidor:",
        INFO_CONEXAO.get(
            "tipo",
            "desconhecido",
        ),
    )
    print(
        "Host:",
        INFO_CONEXAO.get(
            "host",
            "desconhecido",
        ),
    )
    print("=" * 70)
    print()


def validar_execucao(permitir_prod=False):
    if ERP_ENV == "PROD" and not permitir_prod:
        raise RuntimeError(
            "Execucao bloqueada em PROD. "
            "Use --allow-prod somente depois "
            "de validar em TESTE."
        )

    if ERP_ENV not in ("TESTE", "PROD"):
        raise RuntimeError(
            f"ERP_ENV invalido: {ERP_ENV}"
        )

    if not ARQUIVO_MIGRATION.exists():
        raise FileNotFoundError(
            "Arquivo de migration nao encontrado: "
            f"{ARQUIVO_MIGRATION}"
        )


def tabela_existe(conn):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'marketplace_produto_vinculos'
            );
            """
        )

        return bool(
            cursor.fetchone()[0]
        )

    finally:
        cursor.close()


def contar_registros(conn):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM marketplace_produto_vinculos;
            """
        )

        return int(
            cursor.fetchone()[0]
        )

    finally:
        cursor.close()


def aplicar_migration(permitir_prod=False):
    exibir_ambiente()

    validar_execucao(
        permitir_prod=permitir_prod
    )

    sql = ARQUIVO_MIGRATION.read_text(
        encoding="utf-8"
    )

    conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    try:
        ja_existia = tabela_existe(
            conn
        )

        cursor = conn.cursor()

        try:
            cursor.execute(
                sql
            )

        finally:
            cursor.close()

        conn.commit()

        if not tabela_existe(conn):
            raise RuntimeError(
                "A migration terminou sem erro, "
                "mas a tabela nao foi encontrada."
            )

        total = contar_registros(
            conn
        )

        print()
        print(
            "Migration concluida com sucesso."
        )
        print(
            "Tabela: marketplace_produto_vinculos"
        )
        print(
            "Ja existia antes:",
            ja_existia,
        )
        print(
            "Registros atuais:",
            total,
        )
        print()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Aplica a migration de vinculos "
            "de produtos dos marketplaces."
        )
    )

    parser.add_argument(
        "--allow-prod",
        action="store_true",
        help=(
            "Permite executar em PROD. "
            "Use somente apos validar em TESTE."
        ),
    )

    args = parser.parse_args()

    aplicar_migration(
        permitir_prod=args.allow_prod
    )


if __name__ == "__main__":
    main()