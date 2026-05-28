import pandas as pd
from database.connection import conectar
from relatorios.base_pdf import gerar_pdf_base


def relatorio_vendas():

    conn = conectar()

    if conn is None:
        raise Exception("Erro ao conectar no banco")

    try:

        query = """
        SELECT 
            v.id AS venda_id,
            v.data_venda,
            c.nome AS cliente,
            v.valor_total,
            v.desconto,
            v.valor_final,
            v.forma_pagamento,
            v.status
        FROM vendas v
        LEFT JOIN clientes c ON c.id = v.cliente_id
        ORDER BY v.id DESC
        """

        df = pd.read_sql_query(query, conn)

        return gerar_pdf_base(
            "relatorio_vendas",
            "Relatório de Vendas",
            df.values.tolist(),
            [
                "Venda ID",
                "Data",
                "Cliente",
                "Total",
                "Desconto",
                "Final",
                "Pagamento",
                "Status"
            ]
        )

    finally:
        conn.close()