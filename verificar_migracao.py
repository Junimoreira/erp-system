from database.connection import conectar


def verificar_migracao():

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==================================================
        # FLUXO CAIXA
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM fluxo_caixa")
        fluxo_total = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(id) FROM fluxo_caixa")
        fluxo_max_id = cursor.fetchone()[0]

        # ==================================================
        # MOVIMENTACOES
        # ==================================================
        cursor.execute("SELECT COUNT(*) FROM movimentacoes")
        mov_total = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(id) FROM movimentacoes")
        mov_max_id = cursor.fetchone()[0]

        # ==================================================
        # RESULTADO
        # ==================================================
        print("\n==============================")
        print("🔎 VALIDAÇÃO DE MIGRAÇÃO")
        print("==============================\n")

        print("📦 fluxo_caixa:")
        print(f" - Total: {fluxo_total}")
        print(f" - Último ID: {fluxo_max_id}\n")

        print("💰 movimentacoes:")
        print(f" - Total: {mov_total}")
        print(f" - Último ID: {mov_max_id}\n")

        print("==============================")

        # ==================================================
        # ALERTA AUTOMÁTICO
        # ==================================================
        if fluxo_total == mov_total:
            print("✅ MIGRAÇÃO OK - dados estão consistentes")
        else:
            print("⚠️ ATENÇÃO - diferença entre tabelas detectada")

        if fluxo_max_id == mov_max_id:
            print("✅ Nenhum crescimento irregular detectado em fluxo_caixa")
        else:
            print("⚠️ fluxo_caixa pode ainda estar recebendo novos dados")

        print("==============================\n")

    finally:
        cursor.close()
        conn.close()


# EXECUÇÃO
if __name__ == "__main__":
    verificar_migracao()