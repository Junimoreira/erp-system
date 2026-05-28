# database/queries_vendas.py

def vendas_detalhadas():
    """
    Query oficial de vendas (NUNCA DUPLICAR NO SISTEMA)
    """

    return """
    SELECT 
        v.id AS venda_id,
        v.data_venda,
        c.nome AS cliente,
        p.nome AS produto,
        iv.quantidade,
        iv.valor_unitario,
        (iv.quantidade * iv.valor_unitario) AS total_item
    FROM vendas v
    JOIN clientes c ON c.id = v.cliente_id
    JOIN itens_venda iv ON iv.venda_id = v.id
    JOIN produtos p ON p.id = iv.produto_id
    ORDER BY v.id DESC
    """