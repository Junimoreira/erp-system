from database.connection import conectar


def obter_dashboard():

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==================================================
        # CLIENTES
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_clientes = cursor.fetchone()[0]

        # ==================================================
        # PRODUTOS
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM produtos")
        total_produtos = cursor.fetchone()[0]

        # ==================================================
        # ENTRADAS
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'entrada'
        """)
        entradas = float(cursor.fetchone()[0])

        # ==================================================
        # SAÍDAS
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM movimentacoes
            WHERE tipo = 'saida'
        """)
        saidas = float(cursor.fetchone()[0])

        # ==================================================
        # SALDO
        # ==================================================
        saldo = entradas - saidas

        # ==================================================
        # CONTAS A PAGAR (OPCIONAL - já preparado p/ futuro)
        # ==================================================
        cursor.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM contas_pagar
            WHERE status = 'Pendente'
        """)
        contas_pagar = float(cursor.fetchone()[0])

        # ==================================================
        # RETORNO
        # ==================================================
        return {
            "clientes": total_clientes,
            "produtos": total_produtos,
            "entradas": entradas,
            "saidas": saidas,
            "saldo": saldo,
            "contas_pagar": contas_pagar
        }

    finally:
        cursor.close()
        conn.close()