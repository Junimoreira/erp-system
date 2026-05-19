from database.connection import conectar


try:

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
       ALTER TABLE configuracoes_financeiras
ADD COLUMN desconto_maximo NUMERIC DEFAULT 0;
    """)

    conn.commit()

    print("✅ Tabela Configuracoes_finacneiras atualizada!")

except Exception as erro:

    print("❌ Erro:", erro)

finally:

    cursor.close()
    conn.close()