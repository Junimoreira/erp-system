import pandas as pd
from database.connection import conectar
from relatorios.base_pdf_profissional import gerar_pdf_profissional


def relatorio_vendas():

    conn = conectar()

    try:

        query = """
        SELECT 
            v.id,
            v.data_venda,
            c.nome,
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

        return gerar_pdf_profissional(
            "relatorio_vendas",
            "RELATÓRIO DE VENDAS",
            ["ID", "Data", "Cliente", "Total", "Desconto", "Final", "Pagamento", "Status"],
            df.values.tolist()
        )

    finally:
        conn.close()