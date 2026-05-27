import pandas as pd
from database.connection import conectar
from relatorios.base_pdf import gerar_pdf_base


def relatorio_clientes():

    conn = conectar()

    query = """
    SELECT id, nome, telefone, email
    FROM clientes
    ORDER BY nome
    """

    df = pd.read_sql_query(query, conn)

    dados = df.values.tolist()

    return gerar_pdf_base(
        "relatorio_clientes",
        "Relatório de Clientes",
        dados,
        ["ID", "Nome", "Telefone", "Email"]
    )