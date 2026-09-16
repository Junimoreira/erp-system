import pandas as pd

from database.connection import conectar


# ==========================================================
# LISTAR POSIÇÃO DE ESTOQUE
# ==========================================================
def listar_posicao_estoque(
    somente_ativos=True,
    categoria=None,
    situacao=None,
):
    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        filtros = []
        parametros = []

        if somente_ativos:
            filtros.append(
                "COALESCE(p.ativo, TRUE) = TRUE"
            )

        if categoria:
            filtros.append(
                "UPPER(COALESCE(p.categoria, '')) = UPPER(%s)"
            )
            parametros.append(categoria)

        where_sql = ""

        if filtros:
            where_sql = (
                "WHERE "
                + " AND ".join(filtros)
            )

        query = f"""
            SELECT
                p.id,
                p.nome,
                p.codigo_barras,
                p.sku,
                p.marca,
                p.categoria,
                p.tamanho,
                p.unidade,

                COALESCE(
                    p.estoque,
                    0
                ) AS estoque,

                COALESCE(
                    p.estoque_minimo,
                    0
                ) AS estoque_minimo,

                COALESCE(
                    p.custo,
                    0
                ) AS custo,

                COALESCE(
                    p.preco,
                    0
                ) AS preco,

                CASE
                    WHEN COALESCE(p.estoque, 0) > 0
                     AND COALESCE(p.custo, 0) > 0
                    THEN
                        COALESCE(p.estoque, 0)
                        * COALESCE(p.custo, 0)
                    ELSE 0
                END AS valor_estoque_custo,

                CASE
                    WHEN COALESCE(p.estoque, 0) > 0
                     AND COALESCE(p.preco, 0) > 0
                    THEN
                        COALESCE(p.estoque, 0)
                        * COALESCE(p.preco, 0)
                    ELSE 0
                END AS valor_estoque_venda,

                CASE
                    WHEN COALESCE(p.estoque, 0) <= 0
                    THEN 'SEM ESTOQUE'

                    WHEN COALESCE(p.estoque_minimo, 0) <= 0
                    THEN 'SEM MÍNIMO'

                    WHEN
                        COALESCE(p.estoque, 0)
                        < COALESCE(p.estoque_minimo, 0)
                    THEN 'ABAIXO DO MÍNIMO'

                    WHEN
                        COALESCE(p.estoque, 0)
                        = COALESCE(p.estoque_minimo, 0)
                    THEN 'NO MÍNIMO'

                    ELSE 'NORMAL'
                END AS situacao_estoque,

                CASE
                    WHEN p.custo IS NULL
                      OR p.custo <= 0
                    THEN FALSE
                    ELSE TRUE
                END AS custo_valido,

                CASE
                    WHEN p.preco IS NULL
                      OR p.preco <= 0
                    THEN FALSE
                    ELSE TRUE
                END AS preco_valido,

                p.localizacao,

                COALESCE(
                    p.ativo,
                    TRUE
                ) AS ativo

            FROM produtos p

            {where_sql}

            ORDER BY
                CASE
                    WHEN COALESCE(p.estoque, 0) <= 0
                    THEN 1

                    WHEN
                        COALESCE(p.estoque, 0) > 0
                        AND COALESCE(p.estoque_minimo, 0) > 0
                        AND COALESCE(p.estoque, 0)
                            < COALESCE(p.estoque_minimo, 0)
                    THEN 2

                    WHEN
                        COALESCE(p.estoque, 0) > 0
                        AND COALESCE(p.estoque_minimo, 0) > 0
                        AND COALESCE(p.estoque, 0)
                            = COALESCE(p.estoque_minimo, 0)
                    THEN 3

                    WHEN
                        COALESCE(p.estoque, 0) > 0
                        AND COALESCE(p.estoque_minimo, 0) <= 0
                    THEN 4

                    ELSE 5
                END,
                p.nome
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=parametros,
        )

        if (
            situacao
            and not df.empty
        ):
            df = df[
                df["situacao_estoque"]
                == situacao
            ].copy()

        return df.reset_index(
            drop=True
        )

    finally:
        conn.close()


# ==========================================================
# RESUMO DO ESTOQUE
# ==========================================================
def obter_resumo_estoque():

    conn = conectar()

    if conn is None:
        return {}

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                -- PRODUTOS ATIVOS
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                ),

                -- PRODUTOS INATIVOS
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = FALSE
                ),

                -- PRODUTOS COM ESTOQUE POSITIVO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                ),

                -- SEM ESTOQUE
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) <= 0
                ),

                -- ABAIXO DO MÍNIMO
                -- SOMENTE QUANDO AINDA EXISTE ESTOQUE
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) > 0
                      AND COALESCE(estoque, 0)
                          < COALESCE(estoque_minimo, 0)
                ),

                -- EXATAMENTE NO MÍNIMO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) > 0
                      AND COALESCE(estoque, 0)
                          = COALESCE(estoque_minimo, 0)
                ),

                -- COM ESTOQUE, MAS SEM MÍNIMO DEFINIDO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) <= 0
                ),

                -- ESTOQUE NORMAL
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND COALESCE(estoque, 0) > 0
                      AND COALESCE(estoque_minimo, 0) > 0
                      AND COALESCE(estoque, 0)
                          > COALESCE(estoque_minimo, 0)
                ),

                -- SEM CUSTO VÁLIDO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND (
                            custo IS NULL
                            OR custo <= 0
                      )
                ),

                -- SEM PREÇO VÁLIDO
                COUNT(*) FILTER (
                    WHERE COALESCE(ativo, TRUE) = TRUE
                      AND (
                            preco IS NULL
                            OR preco <= 0
                      )
                ),

                -- QUANTIDADE TOTAL EM ESTOQUE
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(ativo, TRUE) = TRUE
                             AND COALESCE(estoque, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR DO ESTOQUE A CUSTO CONHECIDO
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(ativo, TRUE) = TRUE
                             AND COALESCE(estoque, 0) > 0
                             AND COALESCE(custo, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(custo, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR POTENCIAL DE VENDA
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(ativo, TRUE) = TRUE
                             AND COALESCE(estoque, 0) > 0
                             AND COALESCE(preco, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(preco, 0)
                            ELSE 0
                        END
                    ),
                    0
                )

            FROM produtos
            """
        )

        linha = cursor.fetchone()

        return {
            "produtos_ativos": linha[0],
            "produtos_inativos": linha[1],
            "produtos_com_estoque": linha[2],
            "produtos_sem_estoque": linha[3],
            "produtos_abaixo_minimo": linha[4],
            "produtos_no_minimo": linha[5],
            "produtos_sem_minimo": linha[6],
            "produtos_normais": linha[7],
            "produtos_sem_custo": linha[8],
            "produtos_sem_preco": linha[9],
            "quantidade_total_estoque": linha[10],
            "valor_custo_conhecido": linha[11],
            "valor_potencial_venda": linha[12],
        }

    finally:
        conn.close()


# ==========================================================
# LISTAR CATEGORIAS
# ==========================================================
def listar_categorias_produtos():

    conn = conectar()

    if conn is None:
        return []

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT
                TRIM(categoria)

            FROM produtos

            WHERE COALESCE(ativo, TRUE) = TRUE
              AND categoria IS NOT NULL
              AND TRIM(categoria) <> ''

            ORDER BY
                TRIM(categoria)
            """
        )

        return [
            linha[0]
            for linha in cursor.fetchall()
        ]

    finally:
        conn.close()


# ==========================================================
# CONFERÊNCIA DO RELATÓRIO
# ==========================================================
def conferir_posicao_estoque():

    conn = conectar()

    if conn is None:
        return {}

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT

                -- QUANTIDADE DE PRODUTOS ATIVOS
                COUNT(*),

                -- QUANTIDADE TOTAL DE UNIDADES
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(estoque, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR A CUSTO CONHECIDO
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(estoque, 0) > 0
                             AND COALESCE(custo, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(custo, 0)
                            ELSE 0
                        END
                    ),
                    0
                ),

                -- VALOR POTENCIAL DE VENDA
                COALESCE(
                    SUM(
                        CASE
                            WHEN COALESCE(estoque, 0) > 0
                             AND COALESCE(preco, 0) > 0
                            THEN
                                COALESCE(estoque, 0)
                                * COALESCE(preco, 0)
                            ELSE 0
                        END
                    ),
                    0
                )

            FROM produtos

            WHERE COALESCE(ativo, TRUE) = TRUE
            """
        )

        (
            quantidade_produtos,
            quantidade_estoque,
            valor_custo,
            valor_venda,
        ) = cursor.fetchone()

        return {
            "quantidade_produtos": quantidade_produtos,
            "quantidade_estoque": quantidade_estoque,
            "valor_custo_conhecido": valor_custo,
            "valor_potencial_venda": valor_venda,
        }

    finally:
        conn.close()
# ==========================================================
# RELATORIO DE SITUACAO FISCAL DOS PRODUTOS
# ==========================================================

def listar_pendencias_fiscais_produtos(
    somente_ativos=True,
    categoria=None,
    situacao=None,
):
    """
    Lista a situacao cadastral/fiscal dos produtos.

    Importante:
    - NCM com formato valido significa apenas 8 digitos.
    - CEST ausente nao e considerado erro automaticamente.
    - fiscal_revisado indica revisao do cadastro, nao garante
      sozinho que todos os campos estejam preenchidos.
    """

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        filtros = []
        parametros = []

        if somente_ativos:
            filtros.append(
                "COALESCE(p.ativo, TRUE) = TRUE"
            )

        if categoria:
            filtros.append(
                "UPPER(COALESCE(p.categoria, '')) = UPPER(%s)"
            )
            parametros.append(categoria)

        where_sql = ""

        if filtros:
            where_sql = (
                "WHERE "
                + " AND ".join(filtros)
            )

        query = f"""
            SELECT
                p.id,
                p.nome,
                p.codigo_barras,
                p.sku,
                p.categoria,
                p.marca,
                p.ativo,

                p.ncm,
                p.cest,
                p.origem_mercadoria,
                p.perfil_icms,

                p.cfop_saida_interna,
                p.csosn_saida_interna,

                p.cfop_saida_interestadual,
                p.csosn_saida_interestadual,

                p.cst_pis_saida,
                p.aliquota_pis_saida,

                p.cst_cofins_saida,
                p.aliquota_cofins_saida,

                p.cst_ibs_cbs_saida,
                p.classificacao_tributaria_saida,

                COALESCE(
                    p.fiscal_revisado,
                    FALSE
                ) AS fiscal_revisado,

                p.fiscal_fonte,
                p.fiscal_confianca,
                p.fiscal_observacao,
                p.fiscal_atualizado_em,

                CASE
                    WHEN
                        p.ncm IS NULL
                        OR LOWER(
                            TRIM(p.ncm)
                        ) IN (
                            '',
                            'nan',
                            'none',
                            'null'
                        )
                    THEN FALSE

                    WHEN
                        REGEXP_REPLACE(
                            TRIM(p.ncm),
                            '[^0-9]',
                            '',
                            'g'
                        ) ~ '^[0-9]{{8}}$'
                    THEN TRUE

                    ELSE FALSE
                END AS ncm_formato_valido,

                CASE
                    WHEN
                        p.ncm IS NULL
                        OR LOWER(
                            TRIM(p.ncm)
                        ) IN (
                            '',
                            'nan',
                            'none',
                            'null'
                        )
                    THEN NULL

                    WHEN
                        REGEXP_REPLACE(
                            TRIM(p.ncm),
                            '[^0-9]',
                            '',
                            'g'
                        ) ~ '^[0-9]{{8}}$'
                    THEN REGEXP_REPLACE(
                        TRIM(p.ncm),
                        '[^0-9]',
                        '',
                        'g'
                    )

                    ELSE NULL
                END AS ncm_normalizado,

                CONCAT_WS(
                    '; ',

                    CASE
                        WHEN
                            p.ncm IS NULL
                            OR LOWER(
                                TRIM(p.ncm)
                            ) IN (
                                '',
                                'nan',
                                'none',
                                'null'
                            )
                        THEN 'NCM NAO INFORMADO'

                        WHEN
                            REGEXP_REPLACE(
                                TRIM(p.ncm),
                                '[^0-9]',
                                '',
                                'g'
                            ) !~ '^[0-9]{{8}}$'
                        THEN 'NCM COM FORMATO INADEQUADO'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.origem_mercadoria),
                            ''
                        ) IS NULL
                        THEN 'ORIGEM NAO INFORMADA'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.perfil_icms),
                            ''
                        ) IS NULL
                        THEN 'PERFIL ICMS NAO INFORMADO'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.cfop_saida_interna),
                            ''
                        ) IS NULL
                        THEN 'CFOP INTERNO NAO INFORMADO'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.csosn_saida_interna),
                            ''
                        ) IS NULL
                        THEN 'CSOSN INTERNO NAO INFORMADO'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.cst_pis_saida),
                            ''
                        ) IS NULL
                        THEN 'CST PIS NAO INFORMADO'
                    END,

                    CASE
                        WHEN p.aliquota_pis_saida IS NULL
                        THEN 'ALIQUOTA PIS NAO INFORMADA'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.cst_cofins_saida),
                            ''
                        ) IS NULL
                        THEN 'CST COFINS NAO INFORMADO'
                    END,

                    CASE
                        WHEN p.aliquota_cofins_saida IS NULL
                        THEN 'ALIQUOTA COFINS NAO INFORMADA'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(p.cst_ibs_cbs_saida),
                            ''
                        ) IS NULL
                        THEN 'CST IBS/CBS NAO INFORMADO'
                    END,

                    CASE
                        WHEN NULLIF(
                            TRIM(
                                p.classificacao_tributaria_saida
                            ),
                            ''
                        ) IS NULL
                        THEN 'CLASSIFICACAO TRIBUTARIA NAO INFORMADA'
                    END

                ) AS pendencias_fiscais,

                CASE

                    WHEN
                        p.ncm IS NULL
                        OR LOWER(
                            TRIM(p.ncm)
                        ) IN (
                            '',
                            'nan',
                            'none',
                            'null'
                        )
                        OR REGEXP_REPLACE(
                            TRIM(p.ncm),
                            '[^0-9]',
                            '',
                            'g'
                        ) !~ '^[0-9]{{8}}$'
                    THEN 'PENDENTE'

                    WHEN
                        NULLIF(
                            TRIM(p.origem_mercadoria),
                            ''
                        ) IS NULL
                        OR NULLIF(
                            TRIM(p.perfil_icms),
                            ''
                        ) IS NULL
                        OR NULLIF(
                            TRIM(p.cfop_saida_interna),
                            ''
                        ) IS NULL
                        OR NULLIF(
                            TRIM(p.csosn_saida_interna),
                            ''
                        ) IS NULL
                        OR NULLIF(
                            TRIM(p.cst_pis_saida),
                            ''
                        ) IS NULL
                        OR p.aliquota_pis_saida IS NULL
                        OR NULLIF(
                            TRIM(p.cst_cofins_saida),
                            ''
                        ) IS NULL
                        OR p.aliquota_cofins_saida IS NULL
                        OR NULLIF(
                            TRIM(p.cst_ibs_cbs_saida),
                            ''
                        ) IS NULL
                        OR NULLIF(
                            TRIM(
                                p.classificacao_tributaria_saida
                            ),
                            ''
                        ) IS NULL
                    THEN 'PENDENTE'

                    WHEN COALESCE(
                        p.fiscal_revisado,
                        FALSE
                    ) = FALSE
                    THEN 'REVISAR'

                    ELSE 'REVISADO'

                END AS situacao_fiscal

            FROM produtos p

            {where_sql}

            ORDER BY
                p.nome,
                p.id
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=parametros,
        )

        if (
            situacao
            and situacao != "TODAS"
            and not df.empty
        ):
            df = df[
                df["situacao_fiscal"]
                == situacao
            ].copy()

        return df

    except Exception as e:

        print(
            "Erro ao listar pendencias "
            f"fiscais dos produtos: {e}"
        )

        return pd.DataFrame()

    finally:
        conn.close()


# ==========================================================
# RESUMO FISCAL DOS PRODUTOS
# ==========================================================

def obter_resumo_fiscal_produtos():

    df = listar_pendencias_fiscais_produtos(
        somente_ativos=True
    )

    resumo = {
        "produtos_ativos": 0,
        "ncm_valido": 0,
        "ncm_pendente": 0,
        "revisados": 0,
        "nao_revisados": 0,
        "pendentes": 0,
        "revisar": 0,
    }

    if df is None or df.empty:
        return resumo

    resumo["produtos_ativos"] = len(df)

    resumo["ncm_valido"] = int(
        df["ncm_formato_valido"]
        .fillna(False)
        .sum()
    )

    resumo["ncm_pendente"] = (
        resumo["produtos_ativos"]
        - resumo["ncm_valido"]
    )

    resumo["revisados"] = int(
        df["fiscal_revisado"]
        .fillna(False)
        .sum()
    )

    resumo["nao_revisados"] = (
        resumo["produtos_ativos"]
        - resumo["revisados"]
    )

    resumo["pendentes"] = int(
        (
            df["situacao_fiscal"]
            == "PENDENTE"
        ).sum()
    )

    resumo["revisar"] = int(
        (
            df["situacao_fiscal"]
            == "REVISAR"
        ).sum()
    )

    return resumo

# ==========================================================
# CLASSIFICAR SITUACAO FISCAL PARA RELATORIOS
# ==========================================================

def classificar_situacao_fiscal_produtos(df):
    """
    Acrescenta uma classificacao gerencial ao dataframe
    fiscal sem alterar os dados cadastrados no produto.

    Classificacoes:
    - SEM NCM
    - NCM INADEQUADO
    - A PARAMETRIZAR
    - REVISADO INCOMPLETO
    - APTO
    """

    if df is None or df.empty:
        return pd.DataFrame()

    resultado = df.copy()

    def valor_vazio(valor):

        if valor is None:
            return True

        try:
            if pd.isna(valor):
                return True
        except Exception:
            pass

        texto = str(valor).strip().lower()

        return texto in {
            "",
            "nan",
            "none",
            "null",
        }

    def classificar(linha):

        ncm = linha.get(
            "ncm"
        )

        ncm_valido = bool(
            linha.get(
                "ncm_formato_valido",
                False,
            )
        )

        revisado = bool(
            linha.get(
                "fiscal_revisado",
                False,
            )
        )

        situacao_atual = str(
            linha.get(
                "situacao_fiscal",
                "",
            )
        ).strip().upper()

        if valor_vazio(ncm):
            return "SEM NCM"

        if not ncm_valido:
            return "NCM INADEQUADO"

        if (
            revisado
            and situacao_atual == "PENDENTE"
        ):
            return "REVISADO INCOMPLETO"

        if not revisado:
            return "A PARAMETRIZAR"

        return "APTO"

    resultado[
        "classificacao_fiscal"
    ] = resultado.apply(
        classificar,
        axis=1,
    )

    return resultado


# ==========================================================
# RESUMO SINTETICO DA SITUACAO FISCAL
# ==========================================================

def obter_resumo_situacao_fiscal_produtos():

    df = listar_pendencias_fiscais_produtos(
        somente_ativos=True
    )

    df = classificar_situacao_fiscal_produtos(
        df
    )

    resumo = {
        "produtos_ativos": 0,
        "sem_ncm": 0,
        "ncm_inadequado": 0,
        "a_parametrizar": 0,
        "revisado_incompleto": 0,
        "apto": 0,
        "percentual_apto": 0.0,
    }

    if df.empty:
        return resumo

    resumo["produtos_ativos"] = len(df)

    contagem = (
        df["classificacao_fiscal"]
        .value_counts()
    )

    resumo["sem_ncm"] = int(
        contagem.get(
            "SEM NCM",
            0,
        )
    )

    resumo["ncm_inadequado"] = int(
        contagem.get(
            "NCM INADEQUADO",
            0,
        )
    )

    resumo["a_parametrizar"] = int(
        contagem.get(
            "A PARAMETRIZAR",
            0,
        )
    )

    resumo["revisado_incompleto"] = int(
        contagem.get(
            "REVISADO INCOMPLETO",
            0,
        )
    )

    resumo["apto"] = int(
        contagem.get(
            "APTO",
            0,
        )
    )

    if resumo["produtos_ativos"] > 0:

        resumo["percentual_apto"] = (
            resumo["apto"]
            / resumo["produtos_ativos"]
            * 100
        )

    return resumo
