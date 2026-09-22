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
    / "2026_09_22_adicionar_numero_item_xml_itens_compra.sql"
)


def exibir_ambiente():
    print("=" * 60)
    print("MIGRATION NUMERO ITEM XML - ITENS_COMPRA")
    print("=" * 60)
    print(
        "Ambiente:",
        ERP_ENV,
    )
    print(
        "Banco:",
        INFO_CONEXAO.get("banco"),
    )
    print(
        "Host:",
        INFO_CONEXAO.get("host"),
    )
    print("=" * 60)


def validar_execucao(
    permitir_prod=False,
):
    if ERP_ENV == "PROD" and not permitir_prod:
        raise RuntimeError(
            "Execucao bloqueada em PROD. "
            "Use --allow-prod somente depois "
            "de validar conscientemente a migration."
        )

    if ERP_ENV not in (
        "TESTE",
        "PROD",
    ):
        raise RuntimeError(
            "ERP_ENV deve ser TESTE ou PROD."
        )

    if not ARQUIVO_MIGRATION.exists():
        raise RuntimeError(
            "Arquivo da migration nao encontrado: "
            f"{ARQUIVO_MIGRATION}"
        )


def buscar_coluna_numero_item_xml(
    conn,
):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'itens_compra'
              AND column_name = 'numero_item_xml'
            """
        )

        linha = cursor.fetchone()

        if linha is None:
            return None

        return {
            "column_name": linha[0],
            "data_type": linha[1],
            "is_nullable": linha[2],
        }

    finally:
        cursor.close()

def validar_coluna(
    coluna,
):
    if coluna is None:
        raise RuntimeError(
            "Coluna numero_item_xml nao foi criada."
        )

    if coluna["data_type"] != "integer":
        raise RuntimeError(
            "numero_item_xml possui tipo inesperado: "
            f"{coluna['data_type']}"
        )

    if coluna["is_nullable"] != "YES":
        raise RuntimeError(
            "numero_item_xml deveria aceitar NULL "
            "para preservar registros historicos."
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
        antes = buscar_coluna_numero_item_xml(
            conn
        )

        cursor = conn.cursor()

        try:
            cursor.execute(
                sql
            )
        finally:
            cursor.close()

        depois = buscar_coluna_numero_item_xml(
            conn
        )

        validar_coluna(
            depois
        )

        conn.commit()

        print(
            "\nMigration aplicada com sucesso."
        )

        print(
            "\nColuna antes:",
            antes,
        )

        print(
            "Coluna depois:",
            depois,
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Aplica migration dos campos "
            "numero_item_xml em itens_compra."
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
