def relatorio_contas_pagar():

    conn = conectar()

    query = """
    SELECT descricao, valor, vencimento, status
    FROM contas_pagar
    ORDER BY vencimento
    """

    df = pd.read_sql_query(query, conn)

    return gerar_pdf_base(
        "relatorio_contas_pagar",
        "Contas a Pagar",
        df.values.tolist(),
        ["Descrição", "Valor", "Vencimento", "Status"]
    )