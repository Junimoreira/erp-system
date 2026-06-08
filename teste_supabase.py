import psycopg2

try:

    conn = psycopg2.connect(
        host="db.phgotjnzpchjivzflafi.supabase.co",
        port=5432,
        database="postgres",
        user="postgres",
        password="@verde@@2026",
        sslmode="require"
    )

    print("✅ CONECTOU NO SUPABASE")

    conn.close()

except Exception as e:

    print("❌ ERRO")
    print(type(e).__name__)
    print(e)