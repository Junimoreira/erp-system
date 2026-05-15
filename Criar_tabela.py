from database.connection import conectar


def criar_tabela():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS despesas (

            id SERIAL PRIMARY KEY,

            descricao VARCHAR(200) NOT NULL,

            tipo VARCHAR(20) NOT NULL,

            valor NUMERIC(10,2) NOT NULL,

            vencimento DATE,

            status VARCHAR(20) DEFAULT 'Pendente',

            observacoes TEXT,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        );

    """)

    conn.commit()

    cursor.close()

    conn.close()

    print("Tabela despesas criada com sucesso!")


criar_tabela()