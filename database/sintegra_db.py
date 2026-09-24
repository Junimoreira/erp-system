from database.connection import conectar


# ==========================================================
# LISTAR ITENS DE ENTRADA PARA O SINTEGRA
#
# IMPORTANTE:
# - funcao exclusivamente de leitura;
# - competencia baseada em compras.data_entrada;
# - compra ligada ao documento pela chave da NF-e;
# - item ligado pelo nItem original do XML;
# - nao infere dados historicos ausentes.
# ==========================================================

# ==========================================================
# LISTAR POSSIVEIS PENDENCIAS DE DATA DE ENTRADA
#
# IMPORTANTE:
# - funcao exclusivamente de leitura;
# - procura compras sem data_entrada;
# - data_emissao serve SOMENTE para localizar a pendencia;
# - data_emissao NAO substitui data_entrada;
# - nenhum dado fiscal e inferido automaticamente.
# ==========================================================

def listar_pendencias_data_entrada(
    data_inicial,
    data_final,
    conn=None
):
    conexao_externa = (
        conn is not None
    )

    if not conexao_externa:
        conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                c.id AS compra_id,
                c.data_compra,
                c.data_entrada,
                c.numero_nfe,
                c.chave_nfe,
                c.valor_total AS valor_compra,

                df.id AS documento_fiscal_id,
                df.chave_acesso,
                df.modelo,
                df.serie,
                df.numero,
                df.tipo_movimento,
                df.data_emissao,
                df.emitente_cnpj,
                df.emitente_nome,
                df.emitente_uf,
                df.valor_total AS valor_documento,
                df.status

            FROM compras c

            INNER JOIN documentos_fiscais df
                ON df.chave_acesso = c.chave_nfe

            WHERE c.data_entrada IS NULL
              AND df.data_emissao >= %s
              AND df.data_emissao < %s

            ORDER BY
                df.data_emissao,
                c.id
            """,
            (
                data_inicial,
                data_final,
            )
        )

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        return [
            dict(
                zip(
                    colunas,
                    linha
                )
            )
            for linha in cursor.fetchall()
        ]

    finally:
        if cursor is not None:
            cursor.close()

        if not conexao_externa:
            conn.close()


def listar_itens_entrada_competencia(
    data_inicial,
    data_final,
    conn=None
):
    conexao_externa = (
        conn is not None
    )

    if not conexao_externa:
        conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    cursor = None

    try:
        cursor = conn.cursor()

        # Compatibilidade com bancos que ainda nao receberam
        # a migration classificacao_registro_50.
        #
        # Esta verificacao e somente leitura.
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'itens_compra'
                  AND column_name = 'classificacao_registro_50'
            )
            """
        )

        possui_classificacao_registro_50 = bool(
            cursor.fetchone()[0]
        )

        campo_classificacao_registro_50 = (
            "ic.classificacao_registro_50"
            if possui_classificacao_registro_50
            else "NULL AS classificacao_registro_50"
        )

        query = f"""
            SELECT
                c.id AS compra_id,
                c.data_entrada,
                c.data_compra,
                c.numero_nfe,
                c.chave_nfe,

                df.id AS documento_fiscal_id,
                df.chave_acesso,
                df.modelo,
                df.serie,
                df.numero,
                df.tipo_movimento,
                df.data_emissao,
                df.emitente_cnpj,
                df.emitente_nome,
                df.emitente_uf,
                df.valor_produtos,
                df.valor_frete,
                df.valor_desconto,
                df.valor_total,
                df.status,
                df.xml_original,
                df.xml_processado,

                ic.id AS item_compra_id,
                ic.produto_id,
                ic.numero_item_xml,
                ic.quantidade,
                ic.quantidade_xml,
                ic.fator_conversao,
                ic.custo_unitario,
                ic.subtotal,
                ic.codigo_fornecedor,
                ic.codigo_barras,
                ic.ncm,
                ic.unidade,
                ic.cfop_fornecedor,
                ic.cfop_entrada,
                {campo_classificacao_registro_50},

                dfi.id AS documento_fiscal_item_id,
                dfi.numero_item AS numero_item_fiscal,
                dfi.codigo_produto AS codigo_produto_fiscal,
                dfi.codigo_barras AS codigo_barras_fiscal,
                dfi.descricao AS descricao_fiscal,
                dfi.ncm AS ncm_fiscal,
                dfi.cest AS cest_fiscal,
                dfi.cfop AS cfop_fiscal,
                dfi.unidade AS unidade_fiscal,
                dfi.quantidade AS quantidade_fiscal,
                dfi.valor_unitario AS valor_unitario_fiscal,
                dfi.valor_produto AS valor_produto_fiscal,
                dfi.valor_desconto AS valor_desconto_fiscal,
                dfi.origem_icms,
                dfi.cst_icms,
                dfi.csosn

            FROM compras c

            LEFT JOIN documentos_fiscais df
                ON df.chave_acesso = c.chave_nfe

            LEFT JOIN itens_compra ic
                ON ic.compra_id = c.id

            LEFT JOIN documentos_fiscais_itens dfi
                ON dfi.documento_fiscal_id = df.id
               AND dfi.numero_item = ic.numero_item_xml

            WHERE c.data_entrada >= %s
              AND c.data_entrada <= %s

            ORDER BY
                c.data_entrada,
                c.id,
                ic.numero_item_xml,
                ic.id
            """

        cursor.execute(
            query,
            (
                data_inicial,
                data_final,
            )
        )

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        return [
            dict(
                zip(
                    colunas,
                    linha
                )
            )
            for linha in cursor.fetchall()
        ]

    finally:
        if cursor is not None:
            cursor.close()

        if not conexao_externa:
            conn.close()

# ============================================================
# LISTAR NFC-e DE SAIDA AUTORIZADAS POR COMPETENCIA
# ============================================================
def listar_nfce_saida_competencia(
    data_inicial,
    data_final,
    conn=None,
):
    """
    Retorna NFC-e modelo 65 de saida, autorizadas,
    cuja data de emissao pertence ao periodo informado.

    Consulta destinada a composicao dos Registros
    61 e 61R do SINTEGRA.

    A funcao e somente leitura.

    data_inicial: inclusiva
    data_final:   inclusiva
    """

    conexao_propria = (
        conn is None
    )

    if conexao_propria:
        conn = conectar()

    if conn is None:
        return []

    cursor = None

    try:

        cursor = conn.cursor()

        query = """
            SELECT
                id,
                data_emissao,
                modelo,
                serie,
                numero,
                tipo_movimento,
                valor_total,
                protocolo,
                cstat,
                status,
                venda_id,
                chave_acesso,
                xml_processado,
                xml_original
            FROM documentos_fiscais
            WHERE modelo = 65
              AND status = 'AUTORIZADO'
              AND UPPER(
                    COALESCE(
                        tipo_movimento,
                        ''
                    )
                  ) = 'SAIDA'
              AND data_emissao >= %s
              AND data_emissao < (%s::date + INTERVAL '1 day')
            ORDER BY
                data_emissao,
                serie,
                numero,
                id
        """

        cursor.execute(
            query,
            (
                data_inicial,
                data_final,
            ),
        )

        colunas = [
            descricao[0]
            for descricao
            in cursor.description
        ]

        return [
            dict(
                zip(
                    colunas,
                    linha,
                )
            )
            for linha in cursor.fetchall()
        ]

    finally:

        if cursor is not None:
            cursor.close()

        if (
            conexao_propria
            and conn is not None
        ):
            conn.close()
