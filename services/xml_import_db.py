from database.connection import conectar


def coluna_existe(cursor, tabela, coluna):
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = %s
          AND column_name = %s
    """, (tabela, coluna))

    return cursor.fetchone()[0] > 0


def verificar_nfe_duplicada(cursor, chave_nfe):
    if not chave_nfe:
        return None

    cursor.execute("""
        SELECT
            c.id,
            c.numero_nfe,
            c.chave_nfe,
            c.data_compra,
            f.razao_social
        FROM compras c
        LEFT JOIN fornecedores f
            ON f.id = c.fornecedor_id
        WHERE c.chave_nfe = %s
        LIMIT 1
    """, (chave_nfe,))

    return cursor.fetchone()


def buscar_ou_criar_fornecedor(cursor, fornecedor):
    cnpj = fornecedor.get("cnpj", "")
    razao_social = fornecedor.get("razao_social", "Fornecedor XML")

    if coluna_existe(cursor, "fornecedores", "cnpj") and cnpj:
        cursor.execute("""
            SELECT id
            FROM fornecedores
            WHERE cnpj = %s
            LIMIT 1
        """, (cnpj,))

        encontrado = cursor.fetchone()

        if encontrado:
            return encontrado[0], False

    cursor.execute("""
        INSERT INTO fornecedores (razao_social)
        VALUES (%s)
        RETURNING id
    """, (razao_social,))

    return cursor.fetchone()[0], True


def buscar_produto_por_codigo(cursor, codigo_barras, codigo_fornecedor):
    if codigo_barras and coluna_existe(cursor, "produtos", "codigo_barras"):
        cursor.execute("""
            SELECT id
            FROM produtos
            WHERE TRIM(COALESCE(codigo_barras, '')) = %s
            LIMIT 1
        """, (codigo_barras,))

        encontrado = cursor.fetchone()

        if encontrado:
            return encontrado[0]

    if codigo_fornecedor and coluna_existe(cursor, "produtos", "sku"):
        cursor.execute("""
            SELECT id
            FROM produtos
            WHERE TRIM(COALESCE(sku, '')) = %s
            LIMIT 1
        """, (codigo_fornecedor,))

        encontrado = cursor.fetchone()

        if encontrado:
            return encontrado[0]

    return None


def buscar_ou_criar_produto(cursor, produto):
    nome = produto.get("nome", "Produto XML")
    codigo_barras = produto.get("ean", "")
    codigo_fornecedor = produto.get("codigo", "")
    ncm = produto.get("ncm", "")
    unidade = produto.get("unidade", "")
    custo = float(produto.get("custo", 0) or 0)

    produto_id = buscar_produto_por_codigo(
        cursor,
        codigo_barras,
        codigo_fornecedor
    )

    if produto_id:
        return produto_id, False

    cursor.execute("""
        SELECT id
        FROM produtos
        WHERE LOWER(TRIM(nome)) = LOWER(TRIM(%s))
        LIMIT 1
    """, (nome,))

    encontrado = cursor.fetchone()

    if encontrado:
        produto_id = encontrado[0]

        atualizacoes = []
        valores = []

        if coluna_existe(cursor, "produtos", "custo"):
            atualizacoes.append("custo = %s")
            valores.append(custo)

        if codigo_barras and coluna_existe(cursor, "produtos", "codigo_barras"):
            atualizacoes.append(
                "codigo_barras = COALESCE(NULLIF(codigo_barras, ''), %s)"
            )
            valores.append(codigo_barras)

        if codigo_fornecedor and coluna_existe(cursor, "produtos", "sku"):
            atualizacoes.append(
                "sku = COALESCE(NULLIF(sku, ''), %s)"
            )
            valores.append(codigo_fornecedor)

        if ncm and coluna_existe(cursor, "produtos", "ncm"):
            atualizacoes.append(
                "ncm = COALESCE(NULLIF(ncm, ''), %s)"
            )
            valores.append(ncm)

        if unidade and coluna_existe(cursor, "produtos", "unidade"):
            atualizacoes.append(
                "unidade = COALESCE(NULLIF(unidade, ''), %s)"
            )
            valores.append(unidade)

        if atualizacoes:
            valores.append(produto_id)

            cursor.execute(f"""
                UPDATE produtos
                SET {", ".join(atualizacoes)}
                WHERE id = %s
            """, valores)

        return produto_id, False

    colunas = ["nome", "preco", "estoque"]
    valores = [nome, 0, 0]

    if coluna_existe(cursor, "produtos", "custo"):
        colunas.append("custo")
        valores.append(custo)

    if codigo_barras and coluna_existe(cursor, "produtos", "codigo_barras"):
        colunas.append("codigo_barras")
        valores.append(codigo_barras)

    if codigo_fornecedor and coluna_existe(cursor, "produtos", "sku"):
        colunas.append("sku")
        valores.append(codigo_fornecedor)

    if ncm and coluna_existe(cursor, "produtos", "ncm"):
        colunas.append("ncm")
        valores.append(ncm)

    if unidade and coluna_existe(cursor, "produtos", "unidade"):
        colunas.append("unidade")
        valores.append(unidade)

    if coluna_existe(cursor, "produtos", "ativo"):
        colunas.append("ativo")
        valores.append(True)

    placeholders = ", ".join(["%s"] * len(colunas))
    colunas_sql = ", ".join(colunas)

    cursor.execute(f"""
        INSERT INTO produtos ({colunas_sql})
        VALUES ({placeholders})
        RETURNING id
    """, valores)

    return cursor.fetchone()[0], True


def obter_custo_atual(cursor, produto_id):
    if not coluna_existe(cursor, "produtos", "custo"):
        return 0.0

    cursor.execute("""
        SELECT COALESCE(custo, 0)
        FROM produtos
        WHERE id = %s
    """, (produto_id,))

    resultado = cursor.fetchone()

    return float(resultado[0] or 0) if resultado else 0.0


def buscar_conversao_produto(
    cursor,
    produto_id,
    codigo_barras="",
    codigo_fornecedor=""
):
    try:
        cursor.execute("""
            SELECT
                tipo_compra,
                unidade_compra,
                unidade_estoque,
                fator_conversao
            FROM conversao_produtos_xml
            WHERE ativo = true
              AND (
                    produto_id = %s
                    OR TRIM(COALESCE(codigo_barras, '')) = %s
                    OR TRIM(COALESCE(codigo_fornecedor, '')) = %s
              )
            ORDER BY id DESC
            LIMIT 1
        """, (
            produto_id,
            codigo_barras,
            codigo_fornecedor
        ))

        resultado = cursor.fetchone()

        if resultado:
            return {
                "tipo_compra": resultado[0] or "UNIDADE",
                "unidade_compra": resultado[1] or "UNIDADE",
                "unidade_estoque": resultado[2] or "UNIDADE",
                "fator_conversao": float(resultado[3] or 1)
            }

    except Exception as erro:
        print("Erro buscar_conversao_produto:", erro)

    return {
        "tipo_compra": "UNIDADE",
        "unidade_compra": "UNIDADE",
        "unidade_estoque": "UNIDADE",
        "fator_conversao": 1.0
    }


def aplicar_conversao_produto(
    quantidade_xml,
    custo_xml,
    subtotal_xml,
    conversao
):
    fator = float(conversao.get("fator_conversao", 1) or 1)

    if fator <= 0:
        fator = 1

    quantidade_estoque = float(quantidade_xml) * fator
    custo_unitario_estoque = float(custo_xml) / fator
    subtotal_convertido = float(subtotal_xml)

    return {
        "fator_conversao": fator,
        "quantidade_xml": float(quantidade_xml),
        "custo_xml": float(custo_xml),
        "subtotal_xml": float(subtotal_xml),
        "quantidade_estoque": quantidade_estoque,
        "custo_unitario_estoque": custo_unitario_estoque,
        "subtotal_convertido": subtotal_convertido,
        "tipo_compra": conversao.get("tipo_compra", "UNIDADE"),
        "unidade_compra": conversao.get("unidade_compra", "UNIDADE"),
        "unidade_estoque": conversao.get("unidade_estoque", "UNIDADE")
    }


def importar_nfe_xml(dados_xml, usuario="Sistema"):
    conn = conectar()

    if conn is None:
        return {
            "sucesso": False,
            "duplicada": False,
            "mensagem": "Não foi possível conectar ao banco de dados."
        }

    cursor = conn.cursor()

    try:
        fornecedor = dados_xml["fornecedor"]
        produtos_xml = dados_xml["produtos"]

        valor_total = float(dados_xml.get("valor_total", 0) or 0)
        numero_nfe = dados_xml.get("numero_nfe", "")
        chave_nfe = dados_xml.get("chave_nfe", "")

        duplicada = verificar_nfe_duplicada(cursor, chave_nfe)

        if duplicada:
            return {
                "sucesso": False,
                "duplicada": True,
                "mensagem": "Esta NF-e já foi importada anteriormente.",
                "compra_id": duplicada[0],
                "numero_nfe": duplicada[1],
                "chave_nfe": duplicada[2],
                "data_importacao": duplicada[3],
                "fornecedor": duplicada[4]
            }

        fornecedor_id, fornecedor_novo = buscar_ou_criar_fornecedor(
            cursor,
            fornecedor
        )

        observacoes = (
            f"Importação XML NF-e "
            f"Nº {numero_nfe} "
            f"Chave {chave_nfe}"
        )

        cursor.execute("""
            INSERT INTO compras (
                fornecedor_id,
                data_compra,
                valor_total,
                observacoes,
                usuario,
                status,
                numero_nfe,
                chave_nfe,
                origem
            )
            VALUES (
                %s,
                CURRENT_TIMESTAMP,
                %s,
                %s,
                %s,
                'finalizada',
                %s,
                %s,
                'XML'
            )
            RETURNING id
        """, (
            fornecedor_id,
            valor_total,
            observacoes,
            usuario,
            numero_nfe,
            chave_nfe
        ))

        compra_id = cursor.fetchone()[0]

        produtos_novos = 0
        produtos_atualizados = 0
        itens_convertidos = []

        for item in produtos_xml:
            produto_id, produto_novo = buscar_ou_criar_produto(
                cursor,
                item
            )

            if produto_novo:
                produtos_novos += 1
            else:
                produtos_atualizados += 1

            quantidade_xml = float(item.get("quantidade", 0) or 0)
            custo_xml = float(item.get("custo", 0) or 0)
            subtotal_xml = float(
                item.get("subtotal", quantidade_xml * custo_xml) or 0
            )

            codigo_fornecedor = item.get("codigo", "")
            codigo_barras = item.get("ean", "")
            ncm = item.get("ncm", "")

            conversao = buscar_conversao_produto(
                cursor,
                produto_id,
                codigo_barras,
                codigo_fornecedor
            )

            dados_conversao = aplicar_conversao_produto(
                quantidade_xml=quantidade_xml,
                custo_xml=custo_xml,
                subtotal_xml=subtotal_xml,
                conversao=conversao
            )

            quantidade = dados_conversao["quantidade_estoque"]
            custo = dados_conversao["custo_unitario_estoque"]
            subtotal = dados_conversao["subtotal_convertido"]

            custo_anterior = obter_custo_atual(cursor, produto_id)

            cursor.execute("""
                INSERT INTO itens_compra (
                    compra_id,
                    produto_id,
                    quantidade,
                    quantidade_xml,
                    fator_conversao,
                    custo_unitario,
                    subtotal,
                    codigo_fornecedor,
                    codigo_barras,
                    ncm,
                    unidade
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
            """, (
                compra_id,
                produto_id,
                quantidade,
                quantidade_xml,
                dados_conversao["fator_conversao"],
                custo,
                subtotal,
                codigo_fornecedor,
                codigo_barras,
                ncm,
                dados_conversao["unidade_estoque"]
            ))

            item_compra_id = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE produtos
                SET
                    estoque = COALESCE(estoque, 0) + %s,
                    custo = %s
                WHERE id = %s
            """, (
                quantidade,
                custo,
                produto_id
            ))

            cursor.execute("""
                INSERT INTO historico_custos (
                    produto_id,
                    fornecedor_id,
                    compra_id,
                    data_compra,
                    custo_anterior,
                    custo_novo,
                    quantidade,
                    numero_nfe,
                    chave_nfe
                )
                VALUES (
                    %s, %s, %s,
                    CURRENT_TIMESTAMP,
                    %s, %s, %s,
                    %s, %s
                )
            """, (
                produto_id,
                fornecedor_id,
                compra_id,
                custo_anterior,
                custo,
                quantidade,
                numero_nfe,
                chave_nfe
            ))

            cursor.execute("""
                INSERT INTO lotes_estoque (
                    produto_id,
                    fornecedor_id,
                    compra_id,
                    item_compra_id,
                    data_compra,
                    quantidade_entrada,
                    quantidade_restante,
                    custo_unitario,
                    numero_nfe,
                    chave_nfe,
                    status
                )
                VALUES (
                    %s, %s, %s, %s,
                    CURRENT_TIMESTAMP,
                    %s, %s, %s,
                    %s, %s,
                    'ATIVO'
                )
            """, (
                produto_id,
                fornecedor_id,
                compra_id,
                item_compra_id,
                quantidade,
                quantidade,
                custo,
                numero_nfe,
                chave_nfe
            ))

            itens_convertidos.append({
                "produto_id": produto_id,
                "produto": item.get("nome", ""),
                "quantidade_xml": quantidade_xml,
                "fator_conversao": dados_conversao["fator_conversao"],
                "quantidade_estoque": quantidade,
                "custo_xml": custo_xml,
                "custo_unitario_estoque": custo,
                "unidade_estoque": dados_conversao["unidade_estoque"]
            })

        conn.commit()

        return {
            "sucesso": True,
            "duplicada": False,
            "mensagem": "NF-e importada com sucesso.",
            "compra_id": compra_id,
            "numero_nfe": numero_nfe,
            "chave_nfe": chave_nfe,
            "fornecedor": fornecedor.get("razao_social", ""),
            "valor_total": valor_total,
            "total_produtos": len(produtos_xml),
            "produtos_novos": produtos_novos,
            "produtos_atualizados": produtos_atualizados,
            "fornecedor_novo": fornecedor_novo,
            "conversao_xml": True,
            "itens_convertidos": itens_convertidos
        }

    except Exception as erro:
        conn.rollback()
        print("Erro importar_nfe_xml:", erro)

        return {
            "sucesso": False,
            "duplicada": False,
            "mensagem": f"Erro ao importar NF-e: {erro}"
        }

    finally:
        cursor.close()
        conn.close()