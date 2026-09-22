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
    / "2026_09_22_adicionar_cfop_itens_compra.sql"
)


def exibir_ambiente():
    print("=" * 60)
    print("MIGRATION CFOP - ITENS_COMPRA")
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


def buscar_colunas_cfop(
    conn,
):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'itens_compra'
          AND column_name IN (
              'cfop_fornecedor',
              'cfop_entrada'
          )
        ORDER BY column_name
        """
    )

    return {
        linha[0]: {
            "data_type": linha[1],
            "is_nullable": linha[2],
            "maximum_length": linha[3],
        }
        for linha in cursor.fetchall()
    }


def validar_colunas(
    colunas,
):
    esperadas = (
        "cfop_fornecedor",
        "cfop_entrada",
    )

    for nome in esperadas:
        if nome not in colunas:
            raise RuntimeError(
                f"Coluna nao criada: {nome}"
            )

        dados = colunas[
            nome
        ]

        if (
            dados["data_type"]
            != "character varying"
        ):
            raise RuntimeError(
                f"Tipo inesperado para {nome}: "
                f"{dados['data_type']}"
            )

        if (
            dados["maximum_length"]
            != 4
        ):
            raise RuntimeError(
                f"Tamanho inesperado para {nome}: "
                f"{dados['maximum_length']}"
            )

        if (
            dados["is_nullable"]
            != "YES"
        ):
            raise RuntimeError(
                f"{nome} deveria aceitar NULL."
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
        antes = buscar_colunas_cfop(
            conn
        )

        cursor = conn.cursor()

        cursor.execute(
            sql
        )

        depois = buscar_colunas_cfop(
            conn
        )

        validar_colunas(
            depois
        )

        conn.commit()

        print(
            "\nMigration aplicada com sucesso."
        )

        print(
            "\nColunas antes:",
            sorted(
                antes.keys()
            ),
        )

        print(
            "Colunas depois:",
            sorted(
                depois.keys()
            ),
        )

        for nome in sorted(
            depois
        ):
            print(
                f"{nome}: "
                f"{depois[nome]}"
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
            "CFOP em itens_compra."
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
