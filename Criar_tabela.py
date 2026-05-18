from database.connection import conectar


try:

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS caixa (

            id SERIAL PRIMARY KEY,

            usuario VARCHAR(100),

            data_abertura TIMESTAMP,

            data_fechamento TIMESTAMP,

            saldo_inicial NUMERIC(10,2),

            total_entradas NUMERIC(10,2),

            total_saidas NUMERIC(10,2),

            saldo_final NUMERIC(10,2),

            valor_conferido NUMERIC(10,2),

            diferenca NUMERIC(10,2),

            status VARCHAR(20)

        )

    """)

    conn.commit()

    print("✅ Tabela caixa criada com sucesso!")

except Exception as erro:

    print("❌ Erro:", erro)

finally:

    cursor.close()
    conn.close()