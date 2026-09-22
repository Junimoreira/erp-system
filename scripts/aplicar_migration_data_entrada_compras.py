import argparse
from pathlib import Path

from database.connection import ERP_ENV, INFO_CONEXAO, conectar


ARQUIVO_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "2026_09_22_adicionar_data_entrada_compras.sql"
)


def exibir_ambiente():
    print()
    print("=" * 70)
    print("MIGRATION - DATA DE ENTRADA DAS COMPRAS")
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
            "de validar conscientemente a migration."
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


def buscar_coluna_data_entrada(conn):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'compras'
              AND column_name = 'data_entrada';
            """
        )

        return cursor.fetchone()

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
        coluna_antes = buscar_coluna_data_entrada(
            conn
        )

        cursor = conn.cursor()

        try:
            cursor.execute(
                sql
            )

        finally:
            cursor.close()

        coluna_depois = buscar_coluna_data_entrada(
            conn
        )

        if coluna_depois is None:
            raise RuntimeError(
                "A migration terminou sem erro, "
                "mas compras.data_entrada nao foi encontrada."
            )

        tipo_dado = coluna_depois[0]

        if tipo_dado != "date":
            raise RuntimeError(
                "compras.data_entrada foi criada com "
                f"tipo inesperado: {tipo_dado}"
            )

        conn.commit()

        print()
        print(
            "Migration concluida com sucesso."
        )
        print(
            "Coluna: compras.data_entrada"
        )
        print(
            "Ja existia antes:",
            coluna_antes is not None,
        )
        print(
            "Tipo:",
            coluna_depois[0],
        )
        print(
            "Aceita NULL:",
            coluna_depois[1],
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
            "Adiciona a data efetiva de entrada "
            "das mercadorias as compras."
        )
    )

    parser.add_argument(
        "--allow-prod",
        action="store_true",
        help=(
            "Permite executar em PROD. "
            "Use somente com autorizacao explicita."
        ),
    )

    args = parser.parse_args()

    aplicar_migration(
        permitir_prod=args.allow_prod
    )


if __name__ == "__main__":
    main()
