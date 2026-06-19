from database.connection import conectar


def importar_nfe_xml(dados_xml, usuario="Sistema"):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        fornecedor = dados_xml["fornecedor"]
        produtos = dados_xml["produtos"]

        cnpj = fornecedor.get("cnpj", "")

        cursor.execute("""
            SELECT id
            FROM fornecedores
            WHERE cnpj = %s
            LIMIT 1
        """, (cnpj,))

        resultado = cursor.fetchone()

        if resultado:
            fornecedor_id = resultado[0]
        else:
            cursor.execute("""
                INSERT INTO fornecedores (
                    razao_social,
                    nome_fantasia,
                    cnpj,
                    inscricao_estadual,
                    telefone,
                    email,
                    endereco,
                    numero,
                    bairro,
                    cidade,
                    estado,
                    cep,
                    contato_responsavel,
                    observacoes,
                    ativo
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (
                fornecedor.get("razao_social"),
                fornecedor.get("nome_fantasia"),
                fornecedor.get("cnpj"),
                fornecedor.get("inscricao_estadual"),
                fornecedor.get("telefone"),
                fornecedor.get("email"),
                fornecedor.get("endereco"),
                fornecedor.get("numero"),
                fornecedor.get("bairro"),
                fornecedor.get("cidade"),
                fornecedor.get("estado"),
                fornecedor.get("cep"),
                fornecedor.get("contato_responsavel"),
                fornecedor.get("observacoes"),
                True
            ))

            fornecedor_id = cursor.fetchone()[0]

        valor_total = sum(float(p["subtotal"]) for p in produtos)

        cursor.execute("""
            INSERT INTO compras (
                fornecedor_id,
                data_compra,
                valor_total,
                observacoes,
                usuario,
                status
            )
            VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
            RETURNING id
        """, (
            fornecedor_id,
            valor_total,
            "Compra importada via XML NF-e",
            usuario,
            "finalizada"
        ))

        compra_id = cursor.fetchone()[0]

        for item in produtos:

            produto_id = None
            codigo_barras = item.get("codigo_barras", "")

            if codigo_barras:
                cursor.execute("""
                    SELECT id
                    FROM produtos
                    WHERE codigo_barras = %s
                    LIMIT 1
                """, (codigo_barras,))

                produto = cursor.fetchone()

                if produto:
                    produto_id = produto[0]

            if produto_id is None:
                cursor.execute("""
                    SELECT id
                    FROM produtos
                    WHERE nome = %s
                    LIMIT 1
                """, (item.get("nome"),))

                produto = cursor.fetchone()

                if produto:
                    produto_id = produto[0]

            if produto_id is None:
                cursor.execute("""
                    INSERT INTO produtos (
                        nome,
                        preco,
                        estoque,
                        codigo_barras,
                        sku,
                        referencia,
                        marca,
                        categoria,
                        ncm,
                        cest,
                        cfop_padrao,
                        unidade,
                        custo,
                        margem_lucro,
                        estoque_minimo,
                        localizacao,
                        ativo,
                        observacoes
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (
                    item.get("nome"),
                    float(item.get("preco", 0)),
                    0,
                    item.get("codigo_barras"),
                    item.get("sku"),
                    item.get("referencia"),
                    item.get("marca"),
                    item.get("categoria"),
                    item.get("ncm"),
                    item.get("cest"),
                    item.get("cfop_padrao"),
                    item.get("unidade"),
                    float(item.get("custo", 0)),
                    float(item.get("margem_lucro", 0)),
                    float(item.get("estoque_minimo", 0)),
                    item.get("localizacao"),
                    True,
                    item.get("observacoes")
                ))

                produto_id = cursor.fetchone()[0]

            quantidade = float(item.get("quantidade", 0))
            custo = float(item.get("custo", 0))
            subtotal = float(item.get("subtotal", quantidade * custo))

            cursor.execute("""
                INSERT INTO itens_compra (
                    compra_id,
                    produto_id,
                    quantidade,
                    custo_unitario,
                    subtotal
                )
                VALUES (%s,%s,%s,%s,%s)
            """, (
                compra_id,
                produto_id,
                quantidade,
                custo,
                subtotal
            ))

            cursor.execute("""
                UPDATE produtos
                SET estoque = COALESCE(estoque, 0) + %s,
                    custo = %s,
                    ncm = COALESCE(NULLIF(ncm, ''), %s),
                    cest = COALESCE(NULLIF(cest, ''), %s),
                    cfop_padrao = COALESCE(NULLIF(cfop_padrao, ''), %s),
                    unidade = COALESCE(NULLIF(unidade, ''), %s)
                WHERE id = %s
            """, (
                quantidade,
                custo,
                item.get("ncm"),
                item.get("cest"),
                item.get("cfop_padrao"),
                item.get("unidade"),
                produto_id
            ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro importar XML NF-e:", erro)
        return False

    finally:
        cursor.close()
        conn.close()