import pandas as pd
from database.connection import conectar
from relatorios.base_pdf import gerar_pdf_base


def relatorio_contas_receber():

    conn = conectar()

    if conn is None:
        raise Exception("Erro ao conectar no banco")

    try:

        query = """
        SELECT 
            id,
            cliente_id,
            descricao,
            valor,
            vencimento,
            status
        FROM contas_receber
        ORDER BY vencimento ASC
        """

        df = pd.read_sql_query(query, conn)

        return gerar_pdf_base(
            "relatorio_contas_receber",
            "Contas a Receber",
            df.values.tolist(),
            ["ID", "Cliente", "Descrição", "Valor", "Vencimento", "Status"]
        )

    finally:
        conn.close()