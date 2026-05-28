import pandas as pd
from database.connection import conectar
from database.queries_vendas import vendas_detalhadas


def relatorio_vendas():
    conn = conectar()

    try:
        query = vendas_detalhadas()
        df = pd.read_sql_query(query, conn)
        return df

    finally:
        conn.close()