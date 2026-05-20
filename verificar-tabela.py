from database.connection import conectar


try:

    conn = conectar()

    cursor = conn.cursor()

    # ==================================================
    # ADICIONA CAMPO DESCONTO
    # ==================================================

    cursor.execute("""
        SELECT FROM USUARIOS
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