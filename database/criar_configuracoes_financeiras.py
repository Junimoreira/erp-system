# database/criar_configuracoes_financeiras.py

from connection import conectar


try:

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS configuracoes_financeiras (

            id SERIAL PRIMARY KEY,

            imposto_padrao NUMERIC(10,2) DEFAULT 0,

            frete_padrao NUMERIC(10,2) DEFAULT 0,

            taxa_cartao_padrao NUMERIC(10,2) DEFAULT 0,

            margem_lucro_padrao NUMERIC(10,2) DEFAULT 0,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

    """)

    # ==================================================
    # REGISTRO PADRÃO
    # ==================================================

    cursor.execute("""

        INSERT INTO configuracoes_financeiras (
            imposto_padrao,
            frete_padrao,
            taxa_cartao_padrao,
            margem_lucro_padrao
        )

        SELECT 0, 0, 0, 30

        WHERE NOT EXISTS (
            SELECT 1 FROM configuracoes_financeiras
        )

    """)

    conn.commit()

    print("✅ Tabela configuracoes_financeiras criada!")

except Exception as erro:

    print("❌ Erro:", erro)

finally:

    cursor.close()
    conn.close()