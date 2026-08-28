from database.regras_fiscais_db import (
    carregar_regras_fiscais_ativas
)


# ============================================================
# MOTOR DE REGRAS FISCAIS
# VERDE INFÂNCIA
#
# Esta versão apenas SUGERE classificações fiscais.
# Não altera XML, estoque, compras ou escrituração.
# ============================================================


FINALIDADE_REVENDA = "REVENDA"
FINALIDADE_USO_CONSUMO = "USO_CONSUMO"
FINALIDADE_ATIVO = "ATIVO"


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar(
    valor
):

    if valor is None:
        return ""

    return str(
        valor
    ).strip().upper()


# ============================================================
# IDENTIFICAR OPERAÇÃO INTERESTADUAL
# ============================================================
def operacao_interestadual(
    uf_origem,
    uf_destino
):

    origem = _normalizar(
        uf_origem
    )

    destino = _normalizar(
        uf_destino
    )

    if not origem or not destino:
        return None

    return origem != destino


# ============================================================
# VERIFICAR SE REGRA CORRESPONDE
# ============================================================
def _regra_corresponde(
    regra,
    tipo_operacao,
    finalidade,
    cfop_origem,
    interestadual,
    uf_origem=None,
    uf_destino=None,
    ncm=None,
    cest=None
):

    # --------------------------------------------------------
    # OPERAÇÃO
    # --------------------------------------------------------
    if (
        _normalizar(
            regra.get(
                "tipo_operacao"
            )
        )
        !=
        _normalizar(
            tipo_operacao
        )
    ):
        return False

    # --------------------------------------------------------
    # FINALIDADE
    # --------------------------------------------------------
    regra_finalidade = (
        _normalizar(
            regra.get(
                "finalidade"
            )
        )
    )

    if (
        regra_finalidade
        and
        regra_finalidade
        !=
        _normalizar(
            finalidade
        )
    ):
        return False

    # --------------------------------------------------------
    # CFOP
    # --------------------------------------------------------
    if (
        _normalizar(
            regra.get(
                "cfop_origem"
            )
        )
        !=
        _normalizar(
            cfop_origem
        )
    ):
        return False

    # --------------------------------------------------------
    # INTERESTADUAL
    # --------------------------------------------------------
    regra_interestadual = (
        regra.get(
            "interestadual"
        )
    )

    if (
        regra_interestadual
        is not None
        and
        regra_interestadual
        !=
        interestadual
    ):
        return False

    # --------------------------------------------------------
    # UF ORIGEM
    # --------------------------------------------------------
    regra_uf_origem = (
        _normalizar(
            regra.get(
                "uf_origem"
            )
        )
    )

    if (
        regra_uf_origem
        and
        regra_uf_origem
        !=
        _normalizar(
            uf_origem
        )
    ):
        return False

    # --------------------------------------------------------
    # UF DESTINO
    # --------------------------------------------------------
    regra_uf_destino = (
        _normalizar(
            regra.get(
                "uf_destino"
            )
        )
    )

    if (
        regra_uf_destino
        and
        regra_uf_destino
        !=
        _normalizar(
            uf_destino
        )
    ):
        return False

    # --------------------------------------------------------
    # NCM
    # --------------------------------------------------------
    regra_ncm = (
        _normalizar(
            regra.get(
                "ncm_prefixo"
            )
        )
    )

    ncm_item = (
        _normalizar(
            ncm
        )
    )

    if regra_ncm:

        if not ncm_item.startswith(
            regra_ncm
        ):
            return False

    # --------------------------------------------------------
    # CEST
    # --------------------------------------------------------
    regra_cest = (
        _normalizar(
            regra.get(
                "cest"
            )
        )
    )

    cest_item = (
        _normalizar(
            cest
        )
    )

    if (
        regra_cest
        and
        regra_cest
        !=
        cest_item
    ):
        return False

    return True


# ============================================================
# CALCULAR ESPECIFICIDADE DA REGRA
# ============================================================
def _pontuacao_regra(
    regra
):

    pontos = 0

    if _normalizar(
        regra.get(
            "uf_origem"
        )
    ):
        pontos += 10

    if _normalizar(
        regra.get(
            "uf_destino"
        )
    ):
        pontos += 10

    if _normalizar(
        regra.get(
            "ncm_prefixo"
        )
    ):
        pontos += 20

    if _normalizar(
        regra.get(
            "cest"
        )
    ):
        pontos += 30

    if _normalizar(
        regra.get(
            "cst_origem"
        )
    ):
        pontos += 10

    return pontos


# ============================================================
# ENCONTRAR MELHOR REGRA EM MEMÓRIA
# ============================================================
def encontrar_regra_fiscal(
    regras,
    tipo_operacao,
    finalidade,
    cfop_origem,
    interestadual,
    uf_origem=None,
    uf_destino=None,
    ncm=None,
    cest=None
):

    candidatas = []

    for regra in regras:

        if not _regra_corresponde(
            regra=regra,
            tipo_operacao=tipo_operacao,
            finalidade=finalidade,
            cfop_origem=cfop_origem,
            interestadual=interestadual,
            uf_origem=uf_origem,
            uf_destino=uf_destino,
            ncm=ncm,
            cest=cest
        ):
            continue

        candidatas.append(
            regra
        )

    if not candidatas:
        return None

    candidatas.sort(
        key=lambda regra: (
            -_pontuacao_regra(
                regra
            ),
            regra.get(
                "prioridade"
            ) or 100,
            regra.get(
                "id"
            ) or 0
        )
    )

    return candidatas[0]


# ============================================================
# SUGERIR CFOP DE ENTRADA
# ============================================================
def sugerir_cfop_entrada(
    cfop_fornecedor,
    uf_fornecedor,
    uf_empresa,
    finalidade=FINALIDADE_REVENDA,
    ncm=None,
    cest=None,
    regras=None
):

    cfop = _normalizar(
        cfop_fornecedor
    )

    finalidade = _normalizar(
        finalidade
    )

    ncm = _normalizar(
        ncm
    )

    cest = _normalizar(
        cest
    )

    if not ncm:
        ncm = None

    if not cest:
        cest = None

    interestadual = (
        operacao_interestadual(
            uf_fornecedor,
            uf_empresa
        )
    )

    resultado = {
        "cfop_fornecedor": cfop,
        "cfop_sugerido": None,
        "finalidade": finalidade,
        "interestadual": interestadual,
        "regra_aplicada": None,
        "regra_id": None,
        "confianca": "BAIXA",
        "requer_revisao": True,
        "origem_regra": None,
        "observacao": None
    }

    # --------------------------------------------------------
    # CFOP AUSENTE
    # --------------------------------------------------------
    if not cfop:

        resultado[
            "origem_regra"
        ] = "NAO_ENCONTRADA"

        resultado[
            "observacao"
        ] = (
            "CFOP do fornecedor não informado."
        )

        return resultado

    # --------------------------------------------------------
    # UF AUSENTE
    # --------------------------------------------------------
    if interestadual is None:

        resultado[
            "origem_regra"
        ] = "NAO_ENCONTRADA"

        resultado[
            "observacao"
        ] = (
            "Não foi possível determinar se a operação "
            "é interna ou interestadual."
        )

        return resultado

    # --------------------------------------------------------
    # CARREGAR REGRAS CASO NÃO TENHAM SIDO PASSADAS
    # --------------------------------------------------------
    if regras is None:

        regras = (
            carregar_regras_fiscais_ativas()
        )

    # --------------------------------------------------------
    # LOCALIZAR MELHOR REGRA
    # --------------------------------------------------------
    regra = encontrar_regra_fiscal(
        regras=regras,
        tipo_operacao="ENTRADA",
        finalidade=finalidade,
        cfop_origem=cfop,
        interestadual=interestadual,
        uf_origem=uf_fornecedor,
        uf_destino=uf_empresa,
        ncm=ncm,
        cest=cest
    )

    # --------------------------------------------------------
    # REGRA ENCONTRADA
    # --------------------------------------------------------
    if regra:

        resultado.update(
            {
                "cfop_sugerido":
                    regra.get(
                        "cfop_destino"
                    ),

                "regra_aplicada":
                    regra.get(
                        "nome"
                    ),

                "regra_id":
                    regra.get(
                        "id"
                    ),

                "confianca":
                    regra.get(
                        "confianca"
                    ) or "MEDIA",

                "requer_revisao":
                    regra.get(
                        "requer_revisao",
                        True
                    ),

                "origem_regra":
                    "BANCO_DADOS",

                "observacao":
                    regra.get(
                        "observacao"
                    )
            }
        )

        return resultado

    # --------------------------------------------------------
    # SEM REGRA
    # --------------------------------------------------------
    resultado[
        "origem_regra"
    ] = "NAO_ENCONTRADA"

    resultado[
        "observacao"
    ] = (
        "Nenhuma regra fiscal cadastrada foi encontrada "
        "para esta combinação."
    )

    return resultado


# ============================================================
# ANALISAR ITEM DE ENTRADA
# ============================================================
def analisar_item_entrada(
    item,
    uf_fornecedor,
    uf_empresa,
    finalidade=FINALIDADE_REVENDA,
    regras=None
):

    resultado_cfop = (
        sugerir_cfop_entrada(
            cfop_fornecedor=item.get(
                "cfop"
            ),
            uf_fornecedor=uf_fornecedor,
            uf_empresa=uf_empresa,
            finalidade=finalidade,
            ncm=item.get(
                "ncm"
            ),
            cest=item.get(
                "cest"
            ),
            regras=regras
        )
    )

    return {
        "numero_item":
            item.get(
                "numero_item"
            ),

        "codigo_produto":
            item.get(
                "codigo_produto"
            ),

        "descricao":
            item.get(
                "descricao"
            ),

        "ncm":
            item.get(
                "ncm"
            ),

        "cest":
            item.get(
                "cest"
            ),

        "cfop_fornecedor":
            item.get(
                "cfop"
            ),

        "cfop_entrada_sugerido":
            resultado_cfop.get(
                "cfop_sugerido"
            ),

        "cst_fornecedor":
            item.get(
                "cst_icms"
            ),

        "csosn_fornecedor":
            item.get(
                "csosn"
            ),

        "cst_ibs_cbs":
            item.get(
                "cst_ibs_cbs"
            ),

        "classificacao_tributaria":
            item.get(
                "classificacao_tributaria"
            ),

        "regra_aplicada":
            resultado_cfop.get(
                "regra_aplicada"
            ),

        "regra_id":
            resultado_cfop.get(
                "regra_id"
            ),

        "origem_regra":
            resultado_cfop.get(
                "origem_regra"
            ),

        "confianca":
            resultado_cfop.get(
                "confianca"
            ),

        "requer_revisao":
            resultado_cfop.get(
                "requer_revisao"
            ),

        "observacao":
            resultado_cfop.get(
                "observacao"
            )
    }


# ============================================================
# ANALISAR NF-e COMPLETA DE FORNECEDOR
# ============================================================
def analisar_nota_entrada(
    nota,
    uf_empresa,
    finalidade=FINALIDADE_REVENDA
):

    emitente = nota.get(
        "emitente",
        {}
    )

    uf_fornecedor = (
        emitente.get(
            "uf"
        )
    )

    # --------------------------------------------------------
    # CARREGAR TODAS AS REGRAS UMA ÚNICA VEZ
    # --------------------------------------------------------
    regras = (
        carregar_regras_fiscais_ativas()
    )

    itens_analisados = []

    for item in nota.get(
        "itens",
        []
    ):

        itens_analisados.append(
            analisar_item_entrada(
                item=item,
                uf_fornecedor=uf_fornecedor,
                uf_empresa=uf_empresa,
                finalidade=finalidade,
                regras=regras
            )
        )

    total_revisao = sum(
        1
        for item in itens_analisados
        if item.get(
            "requer_revisao"
        )
    )

    total_regras_banco = sum(
        1
        for item in itens_analisados
        if item.get(
            "origem_regra"
        ) == "BANCO_DADOS"
    )

    total_sem_regra = sum(
        1
        for item in itens_analisados
        if item.get(
            "origem_regra"
        ) == "NAO_ENCONTRADA"
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

        "fornecedor":
            emitente.get(
                "razao_social"
            ),

        "cnpj_fornecedor":
            emitente.get(
                "cnpj"
            ),

        "uf_fornecedor":
            uf_fornecedor,

        "uf_empresa":
            uf_empresa,

        "finalidade":
            finalidade,

        "quantidade_regras_carregadas":
            len(
                regras
            ),

        "quantidade_itens":
            len(
                itens_analisados
            ),

        "itens_revisao":
            total_revisao,

        "itens_com_regra_banco":
            total_regras_banco,

        "itens_sem_regra":
            total_sem_regra,

        "itens":
            itens_analisados
    }