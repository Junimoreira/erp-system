from database.connection import conectar

from services.xml_conversao_service import (
    detectar_conversao_por_descricao,
    aplicar_conversao_produto
)


# ==========================================================
# VERIFICAR SE COLUNA EXISTE
# ==========================================================

def coluna_existe(cursor, tabela, coluna):

    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = %s
          AND column_name = %s
    """, (
        tabela,
        coluna
    ))

    return cursor.fetchone()[0] > 0


# ==========================================================
# VERIFICAR NF-E DUPLICADA
# ==========================================================

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
    """, (
        chave_nfe,
    ))

    return cursor.fetchone()


# ==========================================================
# BUSCAR OU CRIAR FORNECEDOR
# ==========================================================

def buscar_ou_criar_fornecedor(cursor, fornecedor):

    cnpj = str(
        fornecedor.get("cnpj", "") or ""
    ).strip()

    razao_social = fornecedor.get(
        "razao_social",
        "Fornecedor XML"
    )

    if (
        coluna_existe(
            cursor,
            "fornecedores",
            "cnpj"
        )
        and cnpj
    ):

        cursor.execute("""
            SELECT id
            FROM fornecedores
            WHERE TRIM(COALESCE(cnpj, '')) = %s
            LIMIT 1
        """, (
            cnpj,
        ))

        encontrado = cursor.fetchone()

        if encontrado:
            return encontrado[0], False

    cursor.execute("""
        INSERT INTO fornecedores (
            razao_social
        )
        VALUES (%s)
        RETURNING id
    """, (
        razao_social,
    ))

    return cursor.fetchone()[0], True


# ==========================================================
# BUSCAR PRODUTO POR CÓDIGO
# ==========================================================

def buscar_produto_por_codigo(
    cursor,
    codigo_barras,
    codigo_fornecedor
):

    codigo_barras = str(
        codigo_barras or ""
    ).strip()

    codigo_fornecedor = str(
        codigo_fornecedor or ""
    ).strip()

    # ------------------------------------------------------
    # PRIMEIRO: EAN / CÓDIGO DE BARRAS
    # ------------------------------------------------------

    if (
        codigo_barras
        and coluna_existe(
            cursor,
            "produtos",
            "codigo_barras"
        )
    ):

        cursor.execute("""
            SELECT id
            FROM produtos
            WHERE TRIM(COALESCE(codigo_barras, '')) = %s
            LIMIT 1
        """, (
            codigo_barras,
        ))

        encontrado = cursor.fetchone()

        if encontrado:
            return encontrado[0]

    # ------------------------------------------------------
    # DEPOIS: SKU / CÓDIGO DO FORNECEDOR
    # ------------------------------------------------------

    if (
        codigo_fornecedor
        and coluna_existe(
            cursor,
            "produtos",
            "sku"
        )
    ):

        cursor.execute("""
            SELECT id
            FROM produtos
            WHERE TRIM(COALESCE(sku, '')) = %s
            LIMIT 1
        """, (
            codigo_fornecedor,
        ))

        encontrado = cursor.fetchone()

        if encontrado:
            return encontrado[0]

    return None


# ==========================================================
# BUSCAR OU CRIAR PRODUTO
# ==========================================================

def buscar_ou_criar_produto(cursor, produto):

    nome = produto.get(
        "nome",
        "Produto XML"
    )

    codigo_barras = str(
        produto.get("ean", "") or ""
    ).strip()

    codigo_fornecedor = str(
        produto.get("codigo", "") or ""
    ).strip()

    ncm = str(
        produto.get("ncm", "") or ""
    ).strip()

    unidade = str(
        produto.get("unidade", "") or ""
    ).strip()

    produto_id = buscar_produto_por_codigo(
        cursor,
        codigo_barras,
        codigo_fornecedor
    )

    # ======================================================
    # PRODUTO JÁ LOCALIZADO PELO CÓDIGO
    # ======================================================

    if produto_id:

        atualizacoes = []
        valores = []

        if (
            codigo_barras
            and coluna_existe(
                cursor,
                "produtos",
                "codigo_barras"
            )
        ):
            atualizacoes.append("""
                codigo_barras =
                COALESCE(NULLIF(codigo_barras, ''), %s)
            """)
            valores.append(codigo_barras)

        if (
            codigo_fornecedor
            and coluna_existe(
                cursor,
                "produtos",
                "sku"
            )
        ):
            atualizacoes.append("""
                sku =
                COALESCE(NULLIF(sku, ''), %s)
            """)
            valores.append(codigo_fornecedor)

        if (
            ncm
            and coluna_existe(
                cursor,
                "produtos",
                "ncm"
            )
        ):
            atualizacoes.append("""
                ncm =
                COALESCE(NULLIF(ncm, ''), %s)
            """)
            valores.append(ncm)

        if (
            unidade
            and coluna_existe(
                cursor,
                "produtos",
                "unidade"
            )
        ):
            atualizacoes.append("""
                unidade =
                COALESCE(NULLIF(unidade, ''), %s)
            """)
            valores.append(unidade)

        if atualizacoes:

            valores.append(produto_id)

            cursor.execute(
                f"""
                    UPDATE produtos
                    SET {", ".join(atualizacoes)}
                    WHERE id = %s
                """,
                valores
            )

        return produto_id, False

    # ======================================================
    # TENTAR LOCALIZAR PELO NOME
    # ======================================================

    cursor.execute("""
        SELECT id
        FROM produtos
        WHERE LOWER(TRIM(nome)) = LOWER(TRIM(%s))
        LIMIT 1
    """, (
        nome,
    ))

    encontrado = cursor.fetchone()

    if encontrado:

        produto_id = encontrado[0]

        atualizacoes = []
        valores = []

        # IMPORTANTE:
        # NÃO atualizamos custo aqui.
        #
        # O custo correto será calculado depois da conversão.
        # Isso evita gravar custo de caixa/pacote como custo
        # unitário do produto.

        if (
            codigo_barras
            and coluna_existe(
                cursor,
                "produtos",
                "codigo_barras"
            )
        ):
            atualizacoes.append("""
                codigo_barras =
                COALESCE(NULLIF(codigo_barras, ''), %s)
            """)
            valores.append(codigo_barras)

        if (
            codigo_fornecedor
            and coluna_existe(
                cursor,
                "produtos",
                "sku"
            )
        ):
            atualizacoes.append("""
                sku =
                COALESCE(NULLIF(sku, ''), %s)
            """)
            valores.append(codigo_fornecedor)

        if (
            ncm
            and coluna_existe(
                cursor,
                "produtos",
                "ncm"
            )
        ):
            atualizacoes.append("""
                ncm =
                COALESCE(NULLIF(ncm, ''), %s)
            """)
            valores.append(ncm)

        if (
            unidade
            and coluna_existe(
                cursor,
                "produtos",
                "unidade"
            )
        ):
            atualizacoes.append("""
                unidade =
                COALESCE(NULLIF(unidade, ''), %s)
            """)
            valores.append(unidade)

        if atualizacoes:

            valores.append(produto_id)

            cursor.execute(
                f"""
                    UPDATE produtos
                    SET {", ".join(atualizacoes)}
                    WHERE id = %s
                """,
                valores
            )

        return produto_id, False

    # ======================================================
    # CRIAR NOVO PRODUTO
    # ======================================================

    colunas = [
        "nome",
        "preco",
        "estoque"
    ]

    valores = [
        nome,
        0,
        0
    ]

    # O custo será atualizado após a conversão.
    if coluna_existe(
        cursor,
        "produtos",
        "custo"
    ):
        colunas.append("custo")
        valores.append(0)

    if (
        codigo_barras
        and coluna_existe(
            cursor,
            "produtos",
            "codigo_barras"
        )
    ):
        colunas.append("codigo_barras")
        valores.append(codigo_barras)

    if (
        codigo_fornecedor
        and coluna_existe(
            cursor,
            "produtos",
            "sku"
        )
    ):
        colunas.append("sku")
        valores.append(codigo_fornecedor)

    if (
        ncm
        and coluna_existe(
            cursor,
            "produtos",
            "ncm"
        )
    ):
        colunas.append("ncm")
        valores.append(ncm)

    if (
        unidade
        and coluna_existe(
            cursor,
            "produtos",
            "unidade"
        )
    ):
        colunas.append("unidade")
        valores.append(unidade)

    if coluna_existe(
        cursor,
        "produtos",
        "ativo"
    ):
        colunas.append("ativo")
        valores.append(True)

    placeholders = ", ".join(
        ["%s"] * len(colunas)
    )

    colunas_sql = ", ".join(colunas)

    cursor.execute(
        f"""
            INSERT INTO produtos (
                {colunas_sql}
            )
            VALUES (
                {placeholders}
            )
            RETURNING id
        """,
        valores
    )

    return cursor.fetchone()[0], True


# ==========================================================
# OBTER CUSTO ATUAL
# ==========================================================

def obter_custo_atual(
    cursor,
    produto_id
):

    if not coluna_existe(
        cursor,
        "produtos",
        "custo"
    ):
        return 0.0

    cursor.execute("""
        SELECT
            COALESCE(custo, 0)
        FROM produtos
        WHERE id = %s
    """, (
        produto_id,
    ))

    resultado = cursor.fetchone()

    if not resultado:
        return 0.0

    return float(
        resultado[0] or 0
    )


# ==========================================================
# BUSCAR CONVERSÃO CADASTRADA
# ==========================================================

def buscar_conversao_produto(
    cursor,
    produto_id,
    codigo_barras="",
    codigo_fornecedor=""
):
    """
    Retorna a conversão cadastrada ou None.

    É importante retornar None quando não existir cadastro.

    Dessa forma conseguimos diferenciar:

    - fator 1 cadastrado propositalmente
    - nenhuma conversão cadastrada
    """

    codigo_barras = str(
        codigo_barras or ""
    ).strip()

    codigo_fornecedor = str(
        codigo_fornecedor or ""
    ).strip()

    try:

        # ==================================================
        # 1. PRIORIDADE: PRODUTO
        # ==================================================

        if produto_id:

            cursor.execute("""
                SELECT
                    tipo_compra,
                    unidade_compra,
                    unidade_estoque,
                    fator_conversao
                FROM conversao_produtos_xml
                WHERE ativo = true
                  AND produto_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (
                produto_id,
            ))

            resultado = cursor.fetchone()

            if resultado:

                return {
                    "tipo_compra":
                        resultado[0] or "UNIDADE",

                    "unidade_compra":
                        resultado[1] or "UNIDADE",

                    "unidade_estoque":
                        resultado[2] or "UNIDADE",

                    "fator_conversao":
                        float(resultado[3] or 1),

                    "cadastrada": True
                }

        # ==================================================
        # 2. CÓDIGO DE BARRAS
        # ==================================================

        if codigo_barras:

            cursor.execute("""
                SELECT
                    tipo_compra,
                    unidade_compra,
                    unidade_estoque,
                    fator_conversao
                FROM conversao_produtos_xml
                WHERE ativo = true
                  AND TRIM(
                        COALESCE(
                            codigo_barras,
                            ''
                        )
                      ) = %s
                ORDER BY id DESC
                LIMIT 1
            """, (
                codigo_barras,
            ))

            resultado = cursor.fetchone()

            if resultado:

                return {
                    "tipo_compra":
                        resultado[0] or "UNIDADE",

                    "unidade_compra":
                        resultado[1] or "UNIDADE",

                    "unidade_estoque":
                        resultado[2] or "UNIDADE",

                    "fator_conversao":
                        float(resultado[3] or 1),

                    "cadastrada": True
                }

        # ==================================================
        # 3. CÓDIGO DO FORNECEDOR
        # ==================================================

        if codigo_fornecedor:

            cursor.execute("""
                SELECT
                    tipo_compra,
                    unidade_compra,
                    unidade_estoque,
                    fator_conversao
                FROM conversao_produtos_xml
                WHERE ativo = true
                  AND TRIM(
                        COALESCE(
                            codigo_fornecedor,
                            ''
                        )
                      ) = %s
                ORDER BY id DESC
                LIMIT 1
            """, (
                codigo_fornecedor,
            ))

            resultado = cursor.fetchone()

            if resultado:

                return {
                    "tipo_compra":
                        resultado[0] or "UNIDADE",

                    "unidade_compra":
                        resultado[1] or "UNIDADE",

                    "unidade_estoque":
                        resultado[2] or "UNIDADE",

                    "fator_conversao":
                        float(resultado[3] or 1),

                    "cadastrada": True
                }

    except Exception as erro:
        print(
            "Erro buscar_conversao_produto:",
            erro
        )

    return None


# ==========================================================
# DEFINIR CONVERSÃO DO ITEM
# ==========================================================

def definir_conversao_item(
    cursor,
    produto_id,
    codigo_barras,
    codigo_fornecedor,
    nome_produto
):

    # ======================================================
    # PRIMEIRO: CONVERSÃO CADASTRADA
    # ======================================================

    conversao = buscar_conversao_produto(
        cursor,
        produto_id,
        codigo_barras,
        codigo_fornecedor
    )

    if conversao is not None:

        return (
            conversao,
            "Cadastrada"
        )

    # ======================================================
    # SEGUNDO: DETECÇÃO AUTOMÁTICA
    # ======================================================

    conversao_detectada = (
        detectar_conversao_por_descricao(
            nome_produto
        )
    )

    if conversao_detectada.get(
        "detectado"
    ):

        return (
            conversao_detectada,
            "Detectada automaticamente"
        )

    # ======================================================
    # TERCEIRO: PADRÃO FATOR 1
    # ======================================================

    conversao_padrao = {
        "tipo_compra": "UNIDADE",
        "unidade_compra": "UNIDADE",
        "unidade_estoque": "UNIDADE",
        "fator_conversao": 1.0
    }

    return (
        conversao_padrao,
        "Padrão"
    )


# ==========================================================
# IMPORTAR NF-E
# ==========================================================

def importar_nfe_xml(
    dados_xml,
    usuario="Sistema"
):

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "duplicada": False,
            "mensagem":
                "Não foi possível conectar ao banco de dados."
        }

    cursor = conn.cursor()

    try:

        fornecedor = dados_xml["fornecedor"]
        produtos_xml = dados_xml["produtos"]

        valor_total = float(
            dados_xml.get(
                "valor_total",
                0
            ) or 0
        )

        numero_nfe = dados_xml.get(
            "numero_nfe",
            ""
        )

        chave_nfe = dados_xml.get(
            "chave_nfe",
            ""
        )

        # ==================================================
        # VERIFICAR DUPLICIDADE
        # ==================================================

        duplicada = verificar_nfe_duplicada(
            cursor,
            chave_nfe
        )

        if duplicada:

            return {
                "sucesso": False,
                "duplicada": True,
                "mensagem":
                    "Esta NF-e já foi importada anteriormente.",
                "compra_id": duplicada[0],
                "numero_nfe": duplicada[1],
                "chave_nfe": duplicada[2],
                "data_importacao": duplicada[3],
                "fornecedor": duplicada[4]
            }

        # ==================================================
        # FORNECEDOR
        # ==================================================

        fornecedor_id, fornecedor_novo = (
            buscar_ou_criar_fornecedor(
                cursor,
                fornecedor
            )
        )

        observacoes = (
            f"Importação XML NF-e "
            f"Nº {numero_nfe} "
            f"Chave {chave_nfe}"
        )

        # ==================================================
        # CRIAR COMPRA
        # ==================================================

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

        # ==================================================
        # PROCESSAR PRODUTOS
        # ==================================================

        for item in produtos_xml:

            produto_id, produto_novo = (
                buscar_ou_criar_produto(
                    cursor,
                    item
                )
            )

            if produto_novo:
                produtos_novos += 1
            else:
                produtos_atualizados += 1

            nome_produto = item.get(
                "nome",
                ""
            )

            quantidade_xml = float(
                item.get(
                    "quantidade",
                    0
                ) or 0
            )

            custo_xml = float(
                item.get(
                    "custo",
                    0
                ) or 0
            )

            subtotal_xml = float(
                item.get(
                    "subtotal",
                    quantidade_xml * custo_xml
                ) or 0
            )

            codigo_fornecedor = str(
                item.get(
                    "codigo",
                    ""
                ) or ""
            ).strip()

            codigo_barras = str(
                item.get(
                    "ean",
                    ""
                ) or ""
            ).strip()

            ncm = str(
                item.get(
                    "ncm",
                    ""
                ) or ""
            ).strip()

            # ==================================================
            # PEGAR CUSTO ANTES DE ALTERAR
            # ==================================================

            custo_anterior = obter_custo_atual(
                cursor,
                produto_id
            )

            # ==================================================
            # DEFINIR CONVERSÃO
            # ==================================================

            conversao, origem_conversao = (
                definir_conversao_item(
                    cursor,
                    produto_id,
                    codigo_barras,
                    codigo_fornecedor,
                    nome_produto
                )
            )

            # ==================================================
            # APLICAR CONVERSÃO
            # ==================================================

            dados_conversao = (
                aplicar_conversao_produto(
                    quantidade_xml=quantidade_xml,
                    custo_xml=custo_xml,
                    subtotal_xml=subtotal_xml,
                    conversao=conversao
                )
            )

            quantidade = (
                dados_conversao[
                    "quantidade_estoque"
                ]
            )

            custo = (
                dados_conversao[
                    "custo_unitario_estoque"
                ]
            )

            subtotal = (
                dados_conversao[
                    "subtotal_convertido"
                ]
            )

            # ==================================================
            # ITEM DA COMPRA
            # ==================================================

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
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING id
            """, (
                compra_id,
                produto_id,
                quantidade,
                quantidade_xml,
                dados_conversao[
                    "fator_conversao"
                ],
                custo,
                subtotal,
                codigo_fornecedor,
                codigo_barras,
                ncm,
                dados_conversao[
                    "unidade_estoque"
                ]
            ))

            item_compra_id = (
                cursor.fetchone()[0]
            )

            # ==================================================
            # ATUALIZAR ESTOQUE E CUSTO
            # ==================================================

            cursor.execute("""
                UPDATE produtos
                SET
                    estoque =
                        COALESCE(estoque, 0) + %s,

                    custo = %s

                WHERE id = %s
            """, (
                quantidade,
                custo,
                produto_id
            ))

            # ==================================================
            # HISTÓRICO DE CUSTOS
            # ==================================================

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
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
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

            # ==================================================
            # LOTE DE ESTOQUE
            # ==================================================

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
                    %s,
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
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

            # ==================================================
            # RESUMO
            # ==================================================

            itens_convertidos.append({
                "produto_id":
                    produto_id,

                "produto":
                    nome_produto,

                "origem_conversao":
                    origem_conversao,

                "quantidade_xml":
                    quantidade_xml,

                "fator_conversao":
                    dados_conversao[
                        "fator_conversao"
                    ],

                "quantidade_estoque":
                    quantidade,

                "custo_xml":
                    custo_xml,

                "custo_unitario_estoque":
                    custo,

                "unidade_estoque":
                    dados_conversao[
                        "unidade_estoque"
                    ]
            })

        # ==================================================
        # CONFIRMAR TRANSAÇÃO
        # ==================================================

        conn.commit()

        return {
            "sucesso": True,
            "duplicada": False,
            "mensagem":
                "NF-e importada com sucesso.",
            "compra_id":
                compra_id,
            "numero_nfe":
                numero_nfe,
            "chave_nfe":
                chave_nfe,
            "fornecedor":
                fornecedor.get(
                    "razao_social",
                    ""
                ),
            "valor_total":
                valor_total,
            "total_produtos":
                len(produtos_xml),
            "produtos_novos":
                produtos_novos,
            "produtos_atualizados":
                produtos_atualizados,
            "fornecedor_novo":
                fornecedor_novo,
            "conversao_xml":
                True,
            "itens_convertidos":
                itens_convertidos
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro importar_nfe_xml:",
            erro
        )

        return {
            "sucesso": False,
            "duplicada": False,
            "mensagem":
                f"Erro ao importar NF-e: {erro}"
        }

    finally:

        cursor.close()
        conn.close()