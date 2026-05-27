import pandas as pd
from database.connection import conectar
from relatorios.base_pdf import gerar_pdf_base


def relatorio_vendas():

    conn = conectar()

    query = """
    SELECT id, cliente_id, valor_total, valor_final, data_venda
    FROM vendas
    ORDER BY data_venda DESC
    """

    df = pd.read_sql_query(query, conn)

    dados = df.values.tolist()

    return gerar_pdf_base(
        "relatorio_vendas",
        "Relatório de Vendas",
        dados,
        ["ID", "Cliente", "Total", "Final", "Data"]
    )