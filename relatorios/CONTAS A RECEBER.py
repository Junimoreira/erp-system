def relatorio_contas_receber():

    conn = conectar()

    query = """
    SELECT descricao, valor, vencimento, status
    FROM contas_receber
    ORDER BY vencimento
    """

    df = pd.read_sql_query(query, conn)

    return gerar_pdf_base(
        "relatorio_contas_receber",
        "Contas a Receber",
        df.values.tolist(),
        ["Descrição", "Valor", "Vencimento", "Status"]
    )