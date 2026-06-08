import psycopg2

try:

    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="Loja_ERP",
        user="postgres",
        password="123456"
    )

    print("✅ CONECTOU NO BANCO LOCAL")

    cursor = conn.cursor()

    cursor.execute("SELECT current_database();")

    print("Banco:", cursor.fetchone()[0])

    conn.close()

except Exception as e:

    print("❌ ERRO")
    print(type(e).__name__)
    print(e)