import psycopg2

url = "postgresql://bd_erp_system_user:SUA_SENHA@dpg-d7uc7aho3t8c73fao0rg-a.virginia-postgres.render.com/bd_erp_system"

try:
    conn = psycopg2.connect(
        url,
        sslmode="require"
    )

    print("✅ CONECTOU")

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usuarios")

    print("Usuários:", cursor.fetchone())

    conn.close()

except Exception as e:
    print("❌ ERRO:")
    print(type(e).__name__)
    print(e)