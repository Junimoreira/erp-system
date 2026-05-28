def validar_sql(sql: str):
    proibidos = [
        "v.produto_id",
        "v.quantidade",
        "v.valor_unitario"
    ]

    for p in proibidos:
        if p in sql:
            raise Exception(f"❌ SQL proibido detectado: {p}")