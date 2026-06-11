from datetime import datetime

from database.connection import conectar


# ==================================================
# REGISTRAR MOVIMENTAÇÃO BANCÁRIA
# ==================================================
def registrar_movimentacao_bancaria(
    conta_id,
    tipo,
    valor,
    descricao,
    categoria_id=None
):

    conn = conectar()

    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO movimentacoes_bancarias
            (
                conta_id,
                tipo,
                valor,
                descricao,
                categoria_id,
                data_movimentacao
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            conta_id,
            tipo,
            valor,
            descricao,
            categoria_id,
            datetime.now()
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro movimentação bancária:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()