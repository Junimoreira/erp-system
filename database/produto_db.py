# =====================================
# BUSCAR PRODUTO POR CÓDIGO DE BARRAS (PDV)
# =====================================
def buscar_produto_por_codigo(codigo_barras):

    conn = conectar()
    cursor = conn.cursor()

    query = """
        SELECT
            id,
            nome,
            preco,
            estoque,
            codigo_barras
        FROM produtos
        WHERE codigo_barras = %s
        LIMIT 1
    """

    cursor.execute(query, (codigo_barras,))
    produto = cursor.fetchone()

    cursor.close()
    conn.close()

    return produto