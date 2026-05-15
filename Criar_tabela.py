from database.connection import conectar


def atualizar_tabela():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE movimentacoes (
        id SERIAL PRIMARY KEY,
        tipo VARCHAR(10), -- entrada / saida
        valor NUMERIC(10,2),
        descricao TEXT,
        origem VARCHAR(50),
        data TIMESTAMP DEFAULT NOW()
    );

    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Coluna adicionada!")


atualizar_tabela()