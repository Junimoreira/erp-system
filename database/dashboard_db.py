from database.connection import conectar


def obter_dashboard():

    conn = conectar()

    cursor = conn.cursor()

    # =====================================
    # CLIENTES
    # =====================================
    cursor.execute("""
        SELECT COUNT(*)
        FROM clientes
    """)

    total_clientes = cursor.fetchone()[0]

    # =====================================
    # PRODUTOS
    # =====================================
    cursor.execute("""
        SELECT COUNT(*)
        FROM produtos
    """)

    total_produtos = cursor.fetchone()[0]

    # =====================================
    # ENTRADAS
    # =====================================
    cursor.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM financeiro
        WHERE tipo = 'Entrada'
    """)

    entradas = float(cursor.fetchone()[0])

    # =====================================
    # SAÍDAS
    # =====================================
    cursor.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM financeiro
        WHERE tipo = 'Saída'
    """)

    saidas = float(cursor.fetchone()[0])

    saldo = entradas - saidas

    cursor.close()
    conn.close()

    return {
        "clientes": total_clientes,
        "produtos": total_produtos,
        "entradas": entradas,
        "saidas": saidas,
        "saldo": saldo
    }