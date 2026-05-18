from database.connection import conectar


try:

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        ALTER TABLE movimentacoes
        ADD COLUMN IF NOT EXISTS data_movimentacao
        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    """)

    conn.commit()

    print("✅ Tabela movimentacoes atualizada!")

except Exception as erro:

    print("❌ Erro:", erro)

finally:

    cursor.close()
    conn.close()