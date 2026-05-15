from database.connection import conectar


try:

    conn = conectar()

    cursor = conn.cursor()

    # ==================================================
    # ADICIONA CAMPO DESCONTO
    # ==================================================

    cursor.execute("""
        ALTER TABLE vendas
        ADD COLUMN desconto NUMERIC(10,2) DEFAULT 0
    """)

    # ==================================================
    # ADICIONA CAMPO VALOR FINAL
    # ==================================================

    cursor.execute("""
        ALTER TABLE vendas
        ADD COLUMN valor_final NUMERIC(10,2)
    """)

    conn.commit()

    print(
        "✅ Colunas adicionadas com sucesso!"
    )

    cursor.close()
    conn.close()

except Exception as erro:

    print(
        "❌ Erro:",
        erro
    )