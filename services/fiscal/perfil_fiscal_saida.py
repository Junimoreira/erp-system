from decimal import Decimal, InvalidOperation

from database.connection import conectar

from database.configuracoes_fiscais_db import (
    buscar_configuracao_fiscal
)

from services.fiscal.ibs_cbs_classificacao import (
    validar_classificacao_oficial_ibs_cbs
)


# ============================================================
# PERFIL FISCAL DE SAÍDA
# VERDE INFÂNCIA
#
# RESPONSABILIDADE:
# - Ler a configuração fiscal do produto
# - Identificar operação interna / interestadual
# - Selecionar CFOP e CSOSN correspondentes
# - Ler configuração de PIS / COFINS do produto
# - Validar classificação IBS/CBS quando configurada
# - Validar compatibilidade IBS/CBS com NF-e / NFC-e
# - Validar se o produto está apto para emissão
#
# IMPORTANTE:
# Esta versão NÃO:
# - altera produtos
# - altera vendas
# - gera XML
# - transmite para SEFAZ
# ============================================================


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar(
    valor
):

    if valor is None:
        return ""

    texto = str(
        valor
    ).strip()

    if texto.upper() in (
        "",
        "NAN",
        "NONE",
        "NULL",
        "<NA>"
    ):

        return ""

    return texto.upper()


# ============================================================
# NORMALIZAR MODELO
# ============================================================
def _normalizar_modelo(
    modelo
):

    if modelo is None:
        return None

    try:

        modelo = int(
            modelo
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    if modelo not in (
        55,
        65
    ):

        return None

    return modelo


# ============================================================
# NORMALIZAR ALÍQUOTA
#
# Decimal("0") é válido e não representa ausência.
# ============================================================
def _normalizar_aliquota(
    valor
):

    if valor is None:
        return None

    texto = str(
        valor
    ).strip()

    if texto.upper() in (
        "",
        "NAN",
        "NONE",
        "NULL",
        "<NA>"
    ):

        return None

    texto = texto.replace(
        ",",
        "."
    )

    try:

        return Decimal(
            texto
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError
    ) as erro:

        raise ValueError(
            "Alíquota inválida."
        ) from erro


# ============================================================
# VALIDAR FORMATO CST PIS / COFINS
#
# Nesta etapa validamos somente o formato: 2 dígitos.
# ============================================================
def _validar_formato_cst(
    cst
):

    if not cst:
        return True

    return (
        len(
            cst
        ) == 2
        and
        cst.isdigit()
    )


# ============================================================
# BUSCAR PRODUTO FISCAL
# ============================================================
def buscar_produto_fiscal(
    produto_id
):

    conn = conectar()

    if conn is None:
        return None

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
                origem_mercadoria,
                perfil_icms,

                cfop_saida_interna,
                csosn_saida_interna,

                cfop_saida_interestadual,
                csosn_saida_interestadual,

                cst_pis_saida,
                aliquota_pis_saida,
                cst_cofins_saida,
                aliquota_cofins_saida,

                cst_ibs_cbs_saida,
                classificacao_tributaria_saida,

                fiscal_revisado,
                fiscal_fonte,
                fiscal_confianca,
                fiscal_observacao,
                fiscal_atualizado_em

            FROM produtos
            WHERE id = %s
            LIMIT 1
            """,
            (
                produto_id,
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "nome",
            "codigo_barras",
            "ncm",
            "cest",
            "origem_mercadoria",
            "perfil_icms",
            "cfop_saida_interna",
            "csosn_saida_interna",
            "cfop_saida_interestadual",
            "csosn_saida_interestadual",

            "cst_pis_saida",
            "aliquota_pis_saida",
            "cst_cofins_saida",
            "aliquota_cofins_saida",

            "cst_ibs_cbs_saida",
            "classificacao_tributaria_saida",
            "fiscal_revisado",
            "fiscal_fonte",
            "fiscal_confianca",
            "fiscal_observacao",
            "fiscal_atualizado_em"
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar produto fiscal:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# IDENTIFICAR TIPO DA OPERAÇÃO
# ============================================================
def identificar_operacao(
    uf_empresa,
    uf_destino
):

    uf_empresa = _normalizar(
        uf_empresa
    )

    uf_destino = _normalizar(
        uf_destino
    )

    if not uf_empresa:

        return {
            "sucesso": False,
            "operacao": None,
            "interestadual": None,
            "mensagem":
                "UF da empresa não informada."
        }

    if not uf_destino:

        return {
            "sucesso": False,
            "operacao": None,
            "interestadual": None,
            "mensagem":
                "UF do destinatário não informada."
        }

    if uf_empresa == uf_destino:

        return {
            "sucesso": True,
            "operacao": "INTERNA",
            "interestadual": False,
            "mensagem":
                "Operação interna."
        }

    return {
        "sucesso": True,
        "operacao": "INTERESTADUAL",
        "interestadual": True,
        "mensagem":
            "Operação interestadual."
    }


# ============================================================
# MONTAR PERFIL FISCAL DE SAÍDA
#
# modelo:
# - None -> mantém compatibilidade com fluxos antigos
# - 55   -> NF-e
# - 65   -> NFC-e
# ============================================================
def montar_perfil_fiscal_saida(
    produto_id,
    uf_destino,
    modelo=None
):

    erros = []
    avisos = []

    validacao_ibs_cbs = None

    modelo_normalizado = _normalizar_modelo(
        modelo
    )

    # --------------------------------------------------------
    # MODELO INFORMADO, MAS INVÁLIDO
    # --------------------------------------------------------
    if (
        modelo is not None
        and
        modelo_normalizado is None
    ):

        erros.append(
            "Modelo fiscal inválido. Use 55 ou 65."
        )

    # --------------------------------------------------------
    # CONFIGURAÇÃO DA EMPRESA
    # --------------------------------------------------------
    configuracao = (
        buscar_configuracao_fiscal()
    )

    if not configuracao:

        return {
            "sucesso": False,
            "pode_emitir": False,
            "produto_id": produto_id,
            "modelo": modelo_normalizado,
            "erros": [
                (
                    "Configuração fiscal da empresa "
                    "não encontrada."
                )
            ],
            "avisos": []
        }

    uf_empresa = _normalizar(
        configuracao.get(
            "uf"
        )
    )

    # --------------------------------------------------------
    # PRODUTO
    # --------------------------------------------------------
    produto = buscar_produto_fiscal(
        produto_id
    )

    if not produto:

        return {
            "sucesso": False,
            "pode_emitir": False,
            "produto_id": produto_id,
            "modelo": modelo_normalizado,
            "erros": [
                "Produto não encontrado."
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # OPERAÇÃO
    # --------------------------------------------------------
    operacao = identificar_operacao(
        uf_empresa=uf_empresa,
        uf_destino=uf_destino
    )

    if not operacao.get(
        "sucesso"
    ):

        erros.append(
            operacao.get(
                "mensagem"
            )
        )

    interestadual = operacao.get(
        "interestadual"
    )

    # --------------------------------------------------------
    # SELECIONAR CFOP / CSOSN
    # --------------------------------------------------------
    if interestadual is False:

        cfop = _normalizar(
            produto.get(
                "cfop_saida_interna"
            )
        )

        csosn = _normalizar(
            produto.get(
                "csosn_saida_interna"
            )
        )

    elif interestadual is True:

        cfop = _normalizar(
            produto.get(
                "cfop_saida_interestadual"
            )
        )

        csosn = _normalizar(
            produto.get(
                "csosn_saida_interestadual"
            )
        )

    else:

        cfop = ""
        csosn = ""

    # --------------------------------------------------------
    # DADOS DO PRODUTO
    # --------------------------------------------------------
    ncm = _normalizar(
        produto.get(
            "ncm"
        )
    )

    cest = _normalizar(
        produto.get(
            "cest"
        )
    )

    origem_mercadoria = _normalizar(
        produto.get(
            "origem_mercadoria"
        )
    )

    perfil_icms = _normalizar(
        produto.get(
            "perfil_icms"
        )
    )

    # ========================================================
    # PIS / COFINS
    # ========================================================
    cst_pis = _normalizar(
        produto.get(
            "cst_pis_saida"
        )
    )

    cst_cofins = _normalizar(
        produto.get(
            "cst_cofins_saida"
        )
    )

    try:

        aliquota_pis = _normalizar_aliquota(
            produto.get(
                "aliquota_pis_saida"
            )
        )

    except ValueError:

        aliquota_pis = None

        erros.append(
            "Alíquota PIS de saída inválida."
        )

    try:

        aliquota_cofins = _normalizar_aliquota(
            produto.get(
                "aliquota_cofins_saida"
            )
        )

    except ValueError:

        aliquota_cofins = None

        erros.append(
            "Alíquota COFINS de saída inválida."
        )

    cst_ibs_cbs = _normalizar(
        produto.get(
            "cst_ibs_cbs_saida"
        )
    )

    classificacao_tributaria = _normalizar(
        produto.get(
            "classificacao_tributaria_saida"
        )
    )

    fiscal_revisado = bool(
        produto.get(
            "fiscal_revisado"
        )
    )

    fiscal_confianca = _normalizar(
        produto.get(
            "fiscal_confianca"
        )
    )

    # --------------------------------------------------------
    # VALIDAÇÕES BÁSICAS
    # --------------------------------------------------------
    if not ncm:

        erros.append(
            "Produto sem NCM."
        )

    if not perfil_icms:

        erros.append(
            "Produto sem perfil ICMS."
        )

    if not cfop:

        if interestadual:

            erros.append(
                (
                    "Produto sem CFOP de saída "
                    "interestadual."
                )
            )

        else:

            erros.append(
                "Produto sem CFOP de saída interna."
            )

    if not csosn:

        if interestadual:

            erros.append(
                (
                    "Produto sem CSOSN de saída "
                    "interestadual."
                )
            )

        else:

            erros.append(
                "Produto sem CSOSN de saída interna."
            )

    # --------------------------------------------------------
    # REVISÃO FISCAL
    # --------------------------------------------------------
    if not fiscal_revisado:

        erros.append(
            (
                "Configuração fiscal do produto "
                "ainda não foi revisada."
            )
        )

    # --------------------------------------------------------
    # CONFIANÇA
    # --------------------------------------------------------
    if fiscal_confianca != "ALTA":

        avisos.append(
            (
                "A configuração fiscal do produto "
                "não possui confiança ALTA."
            )
        )

    # --------------------------------------------------------
    # ORIGEM DA MERCADORIA
    # --------------------------------------------------------
    if not origem_mercadoria:

        avisos.append(
            (
                "Origem da mercadoria ainda não "
                "está preenchida."
            )
        )

    # ========================================================
    # PIS / COFINS
    #
    # Nesta etapa os campos entram no motor fiscal. Enquanto
    # o cadastro existente estiver sendo revisado, ausência
    # de PIS/COFINS gera aviso e não bloqueia a emissão.
    # ========================================================

    if not cst_pis:

        avisos.append(
            (
                "CST PIS de saída ainda "
                "não está configurado."
            )
        )

    elif not _validar_formato_cst(
        cst_pis
    ):

        erros.append(
            (
                "CST PIS de saída inválido. "
                "Informe 2 dígitos."
            )
        )

    if aliquota_pis is None:

        avisos.append(
            (
                "Alíquota PIS de saída ainda "
                "não está configurada."
            )
        )

    elif aliquota_pis < 0:

        erros.append(
            "Alíquota PIS de saída não pode ser negativa."
        )

    if not cst_cofins:

        avisos.append(
            (
                "CST COFINS de saída ainda "
                "não está configurado."
            )
        )

    elif not _validar_formato_cst(
        cst_cofins
    ):

        erros.append(
            (
                "CST COFINS de saída inválido. "
                "Informe 2 dígitos."
            )
        )

    if aliquota_cofins is None:

        avisos.append(
            (
                "Alíquota COFINS de saída ainda "
                "não está configurada."
            )
        )

    elif aliquota_cofins < 0:

        erros.append(
            "Alíquota COFINS de saída não pode ser negativa."
        )

    # ========================================================
    # IBS / CBS
    # ========================================================

    # --------------------------------------------------------
    # NENHUM INFORMADO
    # --------------------------------------------------------
    if (
        not cst_ibs_cbs
        and
        not classificacao_tributaria
    ):

        avisos.append(
            (
                "CST IBS/CBS de saída ainda "
                "não está configurado."
            )
        )

        avisos.append(
            (
                "Classificação tributária de saída "
                "ainda não está configurada."
            )
        )

    # --------------------------------------------------------
    # SOMENTE CST
    # --------------------------------------------------------
    elif (
        cst_ibs_cbs
        and
        not classificacao_tributaria
    ):

        erros.append(
            (
                "CST IBS/CBS informado, mas a "
                "classificação tributária cClassTrib "
                "não está configurada."
            )
        )

    # --------------------------------------------------------
    # SOMENTE cClassTrib
    # --------------------------------------------------------
    elif (
        not cst_ibs_cbs
        and
        classificacao_tributaria
    ):

        erros.append(
            (
                "Classificação tributária cClassTrib "
                "informada, mas o CST IBS/CBS "
                "não está configurado."
            )
        )

    # --------------------------------------------------------
    # AMBOS INFORMADOS
    # --------------------------------------------------------
    else:

        validacao_ibs_cbs = (
            validar_classificacao_oficial_ibs_cbs(
                cst=cst_ibs_cbs,
                classificacao=
                    classificacao_tributaria,
                modelo=
                    modelo_normalizado
            )
        )

        if not validacao_ibs_cbs.get(
            "valido"
        ):

            for erro in validacao_ibs_cbs.get(
                "erros",
                []
            ):

                erros.append(
                    (
                        "IBS/CBS: "
                        f"{erro}"
                    )
                )

        for aviso in validacao_ibs_cbs.get(
            "avisos",
            []
        ):

            avisos.append(
                (
                    "IBS/CBS: "
                    f"{aviso}"
                )
            )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    pode_emitir = (
        len(
            erros
        ) == 0
    )

    return {
        "sucesso": True,

        "pode_emitir":
            pode_emitir,

        "modelo":
            modelo_normalizado,

        "produto_id":
            produto.get(
                "id"
            ),

        "produto_nome":
            produto.get(
                "nome"
            ),

        "codigo_barras":
            produto.get(
                "codigo_barras"
            ),

        "uf_empresa":
            uf_empresa,

        "uf_destino":
            _normalizar(
                uf_destino
            ),

        "operacao":
            operacao.get(
                "operacao"
            ),

        "interestadual":
            interestadual,

        "ncm":
            ncm or None,

        "cest":
            cest or None,

        "origem_mercadoria":
            origem_mercadoria or None,

        "perfil_icms":
            perfil_icms or None,

        "cfop":
            cfop or None,

        "csosn":
            csosn or None,

        # ----------------------------------------------------
        # PIS / COFINS
        # ----------------------------------------------------
        "cst_pis":
            cst_pis or None,

        "aliquota_pis":
            aliquota_pis,

        "cst_cofins":
            cst_cofins or None,

        "aliquota_cofins":
            aliquota_cofins,

        "cst_ibs_cbs":
            cst_ibs_cbs or None,

        "classificacao_tributaria":
            classificacao_tributaria or None,

        # ----------------------------------------------------
        # IBS / CBS
        # ----------------------------------------------------
        "ibs_cbs_validado":
            (
                validacao_ibs_cbs.get(
                    "valido"
                )
                if validacao_ibs_cbs
                else False
            ),

        "ibs_cbs_existe_na_tabela":
            (
                validacao_ibs_cbs.get(
                    "existe_na_tabela"
                )
                if validacao_ibs_cbs
                else False
            ),

        "ibs_cbs_vigente":
            (
                validacao_ibs_cbs.get(
                    "vigente"
                )
                if validacao_ibs_cbs
                else False
            ),

        "ibs_cbs_permitido_modelo":
            (
                validacao_ibs_cbs.get(
                    "permitido_modelo"
                )
                if validacao_ibs_cbs
                else False
            ),

        "ibs_cbs_ind_nfe":
            (
                validacao_ibs_cbs.get(
                    "ind_nfe"
                )
                if validacao_ibs_cbs
                else None
            ),

        "ibs_cbs_ind_nfce":
            (
                validacao_ibs_cbs.get(
                    "ind_nfce"
                )
                if validacao_ibs_cbs
                else None
            ),

        "ibs_cbs_descricao":
            (
                validacao_ibs_cbs.get(
                    "descricao"
                )
                if validacao_ibs_cbs
                else None
            ),

        "ibs_cbs_fonte":
            (
                validacao_ibs_cbs.get(
                    "fonte"
                )
                if validacao_ibs_cbs
                else None
            ),

        "ibs_cbs_versao_fonte":
            (
                validacao_ibs_cbs.get(
                    "versao_fonte"
                )
                if validacao_ibs_cbs
                else None
            ),

        "validacao_ibs_cbs":
            validacao_ibs_cbs,

        # ----------------------------------------------------
        # CONTROLE FISCAL
        # ----------------------------------------------------
        "fiscal_revisado":
            fiscal_revisado,

        "fiscal_fonte":
            produto.get(
                "fiscal_fonte"
            ),

        "fiscal_confianca":
            produto.get(
                "fiscal_confianca"
            ),

        "fiscal_atualizado_em":
            produto.get(
                "fiscal_atualizado_em"
            ),

        "erros":
            erros,

        "avisos":
            avisos
    }