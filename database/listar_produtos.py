def listar_produtos():

    conn = conectar()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            nome,
            preco,
            estoque,
            criado_em
        FROM produtos
        ORDER BY id DESC
    """

    cursor.execute(query)

    dados = cursor.fetchall()

    colunas = [
        "ID",
        "Nome",
        "Preço",
        "Estoque",
        "Criado em"
    ]

    import pandas as pd

    df = pd.DataFrame(dados, columns=colunas)

    cursor.close()
    conn.close()

    return df