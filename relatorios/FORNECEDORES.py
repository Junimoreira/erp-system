def relatorio_fornecedores():

    conn = conectar()

    query = """
    SELECT id, nome, telefone, email
    FROM fornecedores
    ORDER BY nome
    """

    df = pd.read_sql_query(query, conn)

    return gerar_pdf_base(
        "relatorio_fornecedores",
        "Relatório de Fornecedores",
        df.values.tolist(),
        ["ID", "Nome", "Telefone", "Email"]
    )