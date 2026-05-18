from database.connection import conectar


try:

    conn = conectar()
    cursor = conn.cursor()

    # ==========================================
    # IDENTIFICAÇÃO
    # ==========================================

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS sku VARCHAR(100)
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS referencia VARCHAR(100)
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS marca VARCHAR(100)
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS categoria VARCHAR(100)
    """)

    # ==========================================
    # FISCAL
    # ==========================================

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS ncm VARCHAR(20)
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS cest VARCHAR(20)
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS cfop_padrao VARCHAR(10)
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS unidade VARCHAR(20)
        DEFAULT 'UN'
    """)

    # ==========================================
    # FINANCEIRO
    # ==========================================

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS custo NUMERIC(10,2)
        DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS margem_lucro NUMERIC(10,2)
        DEFAULT 0
    """)

    # ==========================================
    # ESTOQUE
    # ==========================================

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS estoque_minimo NUMERIC(10,3)
        DEFAULT 0
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS localizacao VARCHAR(100)
    """)

    # ==========================================
    # OPERACIONAL
    # ==========================================

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS ativo BOOLEAN
        DEFAULT TRUE
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS observacoes TEXT
    """)

    cursor.execute("""
        ALTER TABLE produtos
        ADD COLUMN IF NOT EXISTS data_cadastro TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
    """)

    conn.commit()

    print("✅ Estrutura da tabela produtos atualizada!")

except Exception as erro:

    print("❌ Erro:", erro)

finally:

    cursor.close()
    conn.close()