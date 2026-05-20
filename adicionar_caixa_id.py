from database.connection import conectar


def adicionar_coluna_caixa_id():

    conn = conectar()

    if conn is None:

        print("Erro ao conectar no banco.")
        return

    cursor = conn.cursor()

    try:

        cursor.execute("""

            ALTER TABLE movimentacoes

            ADD COLUMN IF NOT EXISTS caixa_id INTEGER;

        """)

        conn.commit()

        print("✅ Coluna caixa_id criada com sucesso!")

    except Exception as erro:

        conn.rollback()

        print("❌ Erro ao criar coluna:", erro)

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXECUTAR
# ==================================================
adicionar_coluna_caixa_id()