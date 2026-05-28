import pandas as pd
from database.connection import conectar
from relatorios.base_pdf import gerar_pdf_base


def relatorio_contas_pagar():

    conn = conectar()

    if conn is None:
        raise Exception("Erro ao conectar no banco")

    try:

        query = """
        SELECT 
            id,
            descricao,
            valor,
            vencimento,
            status
        FROM contas_pagar
        ORDER BY vencimento ASC
        """

        df = pd.read_sql_query(query, conn)

        return gerar_pdf_base(
            "relatorio_contas_pagar",
            "Contas a Pagar",
            df.values.tolist(),
            ["ID", "Descrição", "Valor", "Vencimento", "Status"]
        )

    finally:
        conn.close()