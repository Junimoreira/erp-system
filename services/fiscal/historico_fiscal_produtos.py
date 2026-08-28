from database.connection import conectar


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar(valor):

    if valor is None:
        return ""

    return str(
        valor
    ).strip().upper()


# ============================================================
# NORMALIZAR CÓDIGO DE BARRAS
# ============================================================
def _normalizar_codigo_barras(valor):

    valor = _normalizar(
        valor
    )

    if valor in (
        "",
        "SEM GTIN",
        "SEMGTIN"
    ):
        return None

    return valor


# ============================================================
# CARREGAR PRODUTOS DO ERP
# UMA ÚNICA CONEXÃO
# ============================================================
def carregar_produtos_para_analise():

    conn = conectar()

    if conn is None:
        return {
            "por_id": {},
            "por_codigo_barras": {}
        }

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                codigo_barras,
                ncm,
                cest,
                perfil_icms,
                cfop_saida_interna,
                csosn_saida_interna,
                fiscal_revisado,
                fiscal_fonte,
                fiscal_confianca
            FROM produtos
            """
        )

        registros = (
            cursor.fetchall()
        )

        por_id = {}
        por_codigo_barras = {}

        for registro in registros:

            produto = {
                "id": registro[0],
                "nome": registro[1],
                "codigo_barras": registro[2],
                "ncm": registro[3],
                "cest": registro[4],
                "perfil_icms": registro[5],
                "cfop_saida_interna": registro[6],
                "csosn_saida_interna": registro[7],
                "fiscal_revisado": registro[8],
                "fiscal_fonte": registro[9],
                "fiscal_confianca": registro[10]
            }

            produto_id = produto[
                "id"
            ]

            if produto_id is not None:

                por_id[
                    str(
                        produto_id
                    )
                ] = produto

            codigo_barras = (
                _normalizar_codigo_barras(
                    produto.get(
                        "codigo_barras"
                    )
                )
            )

            if codigo_barras:

                por_codigo_barras[
                    codigo_barras
                ] = produto

        return {
            "por_id": por_id,
            "por_codigo_barras":
                por_codigo_barras
        }

    except Exception as erro:

        print(
            "Erro ao carregar produtos para análise:",
            erro
        )

        return {
            "por_id": {},
            "por_codigo_barras": {}
        }

    finally:

        conn.close()


# ============================================================
# LOCALIZAR PRODUTO COM SEGURANÇA
# ============================================================
def localizar_produto_historico(
    item,
    indices_produtos
):

    codigo_barras = (
        _normalizar_codigo_barras(
            item.get(
                "codigo_barras"
            )
        )
    )

    codigo_produto = (
        _normalizar(
            item.get(
                "codigo_produto"
            )
        )
    )

    # --------------------------------------------------------
    # 1º - CÓDIGO DE BARRAS
    # VÍNCULO MAIS SEGURO
    # --------------------------------------------------------
    if codigo_barras:

        produto = (
            indices_produtos[
                "por_codigo_barras"
            ].get(
                codigo_barras
            )
        )

        if produto:

            return {
                "produto":
                    produto,

                "encontrado_por":
                    "CODIGO_BARRAS",

                "confianca_vinculo":
                    "ALTA"
            }

    # --------------------------------------------------------
    # 2º - ID / CÓDIGO INTERNO
    #
    # Apenas candidato.
    # Não consideramos vínculo seguro.
    # --------------------------------------------------------
    if codigo_produto.isdigit():

        produto = (
            indices_produtos[
                "por_id"
            ].get(
                codigo_produto
            )
        )

        if produto:

            return {
                "produto":
                    produto,

                "encontrado_por":
                    "ID_CANDIDATO",

                "confianca_vinculo":
                    "BAIXA"
            }

    return {
        "produto":
            None,

        "encontrado_por":
            None,

        "confianca_vinculo":
            "NENHUMA"
    }


# ============================================================
# SUGERIR PERFIL PELO HISTÓRICO
# ============================================================
def sugerir_perfil_icms(
    item
):

    cfop = _normalizar(
        item.get(
            "cfop"
        )
    )

    csosn = _normalizar(
        item.get(
            "csosn"
        )
    )

    # --------------------------------------------------------
    # HISTÓRICO ST
    # --------------------------------------------------------
    if (
        cfop == "5405"
        and
        csosn == "500"
    ):

        return {
            "perfil_icms_sugerido":
                "ST_SUBSTITUIDO",

            "cfop_saida_interna_sugerido":
                "5405",

            "csosn_saida_interna_sugerido":
                "500",

            "confianca_historico":
                "ALTA",

            "motivo":
                (
                    "A NF-e histórica apresentou "
                    "CFOP 5405 e CSOSN 500."
                )
        }

    # --------------------------------------------------------
    # HISTÓRICO NORMAL
    # --------------------------------------------------------
    if (
        cfop == "5102"
        and
        csosn == "102"
    ):

        return {
            "perfil_icms_sugerido":
                "NORMAL",

            "cfop_saida_interna_sugerido":
                "5102",

            "csosn_saida_interna_sugerido":
                "102",

            "confianca_historico":
                "ALTA",

            "motivo":
                (
                    "A NF-e histórica apresentou "
                    "CFOP 5102 e CSOSN 102."
                )
        }

    # --------------------------------------------------------
    # NÃO MAPEADO
    # --------------------------------------------------------
    return {
        "perfil_icms_sugerido":
            None,

        "cfop_saida_interna_sugerido":
            None,

        "csosn_saida_interna_sugerido":
            None,

        "confianca_historico":
            "BAIXA",

        "motivo":
            (
                "Combinação histórica ainda não "
                "mapeada pelo motor fiscal."
            )
    }


# ============================================================
# DEFINIR SE PODE SER CANDIDATO A APLICAÇÃO
# ============================================================
def _avaliar_aplicabilidade(
    vinculo,
    sugestao
):

    produto = vinculo.get(
        "produto"
    )

    confianca_vinculo = (
        vinculo.get(
            "confianca_vinculo"
        )
    )

    confianca_historico = (
        sugestao.get(
            "confianca_historico"
        )
    )

    perfil_sugerido = (
        sugestao.get(
            "perfil_icms_sugerido"
        )
    )

    # --------------------------------------------------------
    # SEM PRODUTO ASSOCIADO
    # --------------------------------------------------------
    if produto is None:

        return {
            "apto_para_aplicar":
                False,

            "motivo_bloqueio":
                (
                    "Produto do ERP não localizado "
                    "com segurança."
                )
        }

    # --------------------------------------------------------
    # VÍNCULO NÃO CONFIÁVEL
    # --------------------------------------------------------
    if confianca_vinculo != "ALTA":

        return {
            "apto_para_aplicar":
                False,

            "motivo_bloqueio":
                (
                    "Vínculo com o produto não possui "
                    "confiança suficiente."
                )
        }

    # --------------------------------------------------------
    # HISTÓRICO NÃO CONFIÁVEL
    # --------------------------------------------------------
    if confianca_historico != "ALTA":

        return {
            "apto_para_aplicar":
                False,

            "motivo_bloqueio":
                (
                    "Histórico fiscal não possui "
                    "confiança suficiente."
                )
        }

    # --------------------------------------------------------
    # SEM PERFIL
    # --------------------------------------------------------
    if not perfil_sugerido:

        return {
            "apto_para_aplicar":
                False,

            "motivo_bloqueio":
                (
                    "Nenhum perfil fiscal foi sugerido."
                )
        }

    # --------------------------------------------------------
    # PRODUTO JÁ REVISADO
    # --------------------------------------------------------
    if produto.get(
        "fiscal_revisado"
    ):

        return {
            "apto_para_aplicar":
                False,

            "motivo_bloqueio":
                (
                    "Produto já possui configuração "
                    "fiscal revisada."
                )
        }

    return {
        "apto_para_aplicar":
            True,

        "motivo_bloqueio":
            None
    }


# ============================================================
# ANALISAR ITEM HISTÓRICO
# ============================================================
def analisar_item_historico(
    item,
    indices_produtos
):

    vinculo = (
        localizar_produto_historico(
            item,
            indices_produtos
        )
    )

    sugestao = (
        sugerir_perfil_icms(
            item
        )
    )

    aplicabilidade = (
        _avaliar_aplicabilidade(
            vinculo,
            sugestao
        )
    )

    produto = vinculo.get(
        "produto"
    )

    return {
        "numero_item":
            item.get(
                "numero_item"
            ),

        "codigo_xml":
            item.get(
                "codigo_produto"
            ),

        "codigo_barras_xml":
            item.get(
                "codigo_barras"
            ),

        "descricao_xml":
            item.get(
                "descricao"
            ),

        "ncm_xml":
            item.get(
                "ncm"
            ),

        "cest_xml":
            item.get(
                "cest"
            ),

        "cfop_historico":
            item.get(
                "cfop"
            ),

        "csosn_historico":
            item.get(
                "csosn"
            ),

        # ----------------------------------------------------
        # ORIGEM DA MERCADORIA
        #
        # O xml_fiscal_reader.py já extrai a tag <orig>
        # e disponibiliza como "origem_icms".
        #
        # histórico:
        # valor exatamente encontrado na NF-e.
        #
        # sugerida:
        # replica o histórico para futura aprovação antes
        # de qualquer aplicação ao cadastro do produto.
        # ----------------------------------------------------
        "origem_mercadoria_historico":
            item.get(
                "origem_icms"
            ),

        "origem_mercadoria_sugerida":
            item.get(
                "origem_icms"
            ),

        "produto_encontrado":
            produto is not None,

        "produto":
            produto,

        "encontrado_por":
            vinculo.get(
                "encontrado_por"
            ),

        "confianca_vinculo":
            vinculo.get(
                "confianca_vinculo"
            ),

        "perfil_icms_sugerido":
            sugestao.get(
                "perfil_icms_sugerido"
            ),

        "cfop_saida_interna_sugerido":
            sugestao.get(
                "cfop_saida_interna_sugerido"
            ),

        "csosn_saida_interna_sugerido":
            sugestao.get(
                "csosn_saida_interna_sugerido"
            ),

        "confianca_historico":
            sugestao.get(
                "confianca_historico"
            ),

        "motivo_sugestao":
            sugestao.get(
                "motivo"
            ),

        "apto_para_aplicar":
            aplicabilidade.get(
                "apto_para_aplicar"
            ),

        "motivo_bloqueio":
            aplicabilidade.get(
                "motivo_bloqueio"
            ),

        "acao_realizada":
            "NENHUMA"
    }


# ============================================================
# ANALISAR NF-e HISTÓRICA
# ============================================================
def analisar_nota_historica(
    nota
):

    # --------------------------------------------------------
    # CARREGAR PRODUTOS UMA ÚNICA VEZ
    # --------------------------------------------------------
    indices_produtos = (
        carregar_produtos_para_analise()
    )

    resultados = []

    for item in nota.get(
        "itens",
        []
    ):

        resultados.append(
            analisar_item_historico(
                item,
                indices_produtos
            )
        )

    encontrados = sum(
        1
        for item in resultados
        if item.get(
            "produto_encontrado"
        )
    )

    encontrados_seguros = sum(
        1
        for item in resultados
        if item.get(
            "confianca_vinculo"
        ) == "ALTA"
    )

    aptos = sum(
        1
        for item in resultados
        if item.get(
            "apto_para_aplicar"
        )
    )

    sugestoes_st = sum(
        1
        for item in resultados
        if item.get(
            "perfil_icms_sugerido"
        ) == "ST_SUBSTITUIDO"
    )

    sugestoes_normal = sum(
        1
        for item in resultados
        if item.get(
            "perfil_icms_sugerido"
        ) == "NORMAL"
    )

    return {
        "numero_nota":
            nota.get(
                "numero"
            ),

        "chave_acesso":
            nota.get(
                "chave_acesso"
            ),

        "quantidade_itens":
            len(
                resultados
            ),

        "produtos_encontrados":
            encontrados,

        "vinculos_seguros":
            encontrados_seguros,

        "produtos_nao_encontrados":
            len(
                resultados
            ) - encontrados,

        "sugestoes_normal":
            sugestoes_normal,

        "sugestoes_st":
            sugestoes_st,

        "aptos_para_aplicar":
            aptos,

        "itens":
            resultados
    }