import argparse
from pathlib import Path

from database.connection import (
    ERP_ENV,
    INFO_CONEXAO,
    conectar,
)


ARQUIVO_MIGRATION = (
    Path(__file__).resolve().parent.parent
    / "migrations"
    / "2026_09_23_adicionar_csosn_origem_regras_fiscais.sql"
)


def exibir_ambiente():
    print("=" * 60)
    print("MIGRATION CSOSN ORIGEM - REGRAS FISCAIS")
    print("=" * 60)
    print("Ambiente:", ERP_ENV)
    print("Banco:", INFO_CONEXAO.get("banco"))
    print("Host:", INFO_CONEXAO.get("host"))


def validar_execucao(
    permitir_prod=False,
):
    if ERP_ENV not in {
        "TESTE",
        "PROD",
    }:
        raise RuntimeError(
            "ERP_ENV deve ser TESTE ou PROD."
        )

    if (
        ERP_ENV == "PROD"
        and not permitir_prod
    ):
        raise RuntimeError(
            "Execucao em PROD bloqueada. "
            "Use --allow-prod somente com "
            "autorizacao explicita."
        )

    if not ARQUIVO_MIGRATION.exists():
        raise RuntimeError(
            "Arquivo da migration nao encontrado: "
            f"{ARQUIVO_MIGRATION}"
        )


def buscar_coluna(
    conn,
):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'regras_fiscais'
              AND column_name = 'csosn_origem'
            """
        )

        linha = cursor.fetchone()

        if linha is None:
            return None

        return {
            "column_name": linha[0],
            "data_type": linha[1],
            "is_nullable": linha[2],
            "maximum_length": linha[3],
        }

    finally:
        cursor.close()


def validar_coluna(
    coluna,
):
    if coluna is None:
        raise RuntimeError(
            "Coluna csosn_origem nao foi criada."
        )

    if (
        coluna["data_type"]
        != "character varying"
    ):
        raise RuntimeError(
            "Tipo inesperado para csosn_origem: "
            f"{coluna['data_type']}"
        )

    if coluna["maximum_length"] != 4:
        raise RuntimeError(
            "Tamanho inesperado para csosn_origem: "
            f"{coluna['maximum_length']}"
        )

    if coluna["is_nullable"] != "YES":
        raise RuntimeError(
            "csosn_origem deve aceitar NULL para "
            "preservar regras existentes."
        )


def aplicar_migration(
    permitir_prod=False,
):
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
        antes = buscar_coluna(
            conn
        )

        cursor = conn.cursor()

        try:
            cursor.execute(
                sql
            )
        finally:
            cursor.close()

        depois = buscar_coluna(
            conn
        )

        validar_coluna(
            depois
        )

        conn.commit()

        print()
        print("Migration aplicada com sucesso.")
        print()
        print("Coluna antes:", antes)
        print("Coluna depois:", depois)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Adiciona csosn_origem em regras_fiscais."
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

    argumentos = parser.parse_args()

    aplicar_migration(
        permitir_prod=argumentos.allow_prod
    )


if __name__ == "__main__":
    main()
