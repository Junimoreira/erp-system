from datetime import datetime
from pathlib import Path

from requests_pkcs12 import get as pkcs12_get


# ============================================================
# API OFICIAL - CONFORMIDADE FÁCIL / SVRS
#
# IMPORTANTE:
# - somente leitura
# - NÃO altera banco
# - NÃO altera produtos
# - NÃO transmite NF-e/NFC-e
# ============================================================

URL_API_OFICIAL = (
    "https://cff.svrs.rs.gov.br/"
    "api/v1/consultas/classTrib"
)

VERSAO_FONTE = "SVRS_CCLASSTRIB_2026_06_22"

FONTE = "SVRS_CONFORMIDADE_FACIL"


# ============================================================
# NORMALIZAR TEXTO
# ============================================================
def _normalizar_texto(
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

    return texto


# ============================================================
# NORMALIZAR DATA
#
# A API retorna exemplos como:
# 2025-05-05T00:00:00
# ============================================================
def _normalizar_data(
    valor
):

    texto = _normalizar_texto(
        valor
    )

    if texto is None:
        return None

    try:

        return datetime.fromisoformat(
            texto
        ).date()

    except ValueError:

        return None


# ============================================================
# VALIDAR CST + cClassTrib
# ============================================================
def _validar_registro(
    cst,
    cclass_trib
):

    erros = []

    if (
        cst is None
        or
        not cst.isdigit()
        or
        len(
            cst
        ) != 3
    ):

        erros.append(
            "CST IBS/CBS inválido."
        )

    if (
        cclass_trib is None
        or
        not cclass_trib.isdigit()
        or
        len(
            cclass_trib
        ) != 6
    ):

        erros.append(
            "cClassTrib inválido."
        )

    if (
        not erros
        and
        cclass_trib[:3] != cst
    ):

        erros.append(
            (
                "Os três primeiros dígitos do "
                "cClassTrib não correspondem ao CST."
            )
        )

    return erros


# ============================================================
# LOCALIZAR LISTA PRINCIPAL DA API
# ============================================================
def _localizar_lista_principal(
    dados
):

    if isinstance(
        dados,
        list
    ):

        return dados

    if not isinstance(
        dados,
        dict
    ):

        return None

    candidatos = (
        "dados",
        "data",
        "registros",
        "items",
        "result",
        "resultado",
        "content"
    )

    for chave in candidatos:

        valor = dados.get(
            chave
        )

        if isinstance(
            valor,
            list
        ):

            return valor

    # --------------------------------------------------------
    # Se a API mudar o nome da propriedade principal,
    # procura a primeira lista no objeto.
    # --------------------------------------------------------
    for valor in dados.values():

        if isinstance(
            valor,
            list
        ):

            return valor

    return None


# ============================================================
# INTERPRETAR RESPOSTA REAL DA API
#
# Estrutura observada:
#
# [
#     {
#         "CST": "000",
#         "DescricaoCST": "...",
#         "InicioVigencia": "...",
#         "FimVigencia": null,
#         "classificacoesTributarias": [
#             {
#                 "cClassTrib": "000001",
#                 "DescricaoClassTrib": "...",
#                 ...
#             }
#         ]
#     }
# ]
# ============================================================
def interpretar_resposta_api(
    dados
):

    grupos_cst = _localizar_lista_principal(
        dados
    )

    if grupos_cst is None:

        return {
            "sucesso": False,
            "mensagem":
                (
                    "Não foi possível localizar "
                    "a lista de CST na resposta da API."
                ),
            "registros": [],
            "rejeitados": []
        }

    registros = []
    rejeitados = []

    quantidade_grupos_cst = 0

    # --------------------------------------------------------
    # PERCORRER GRUPOS CST
    # --------------------------------------------------------
    for numero_grupo, grupo in enumerate(
        grupos_cst,
        start=1
    ):

        if not isinstance(
            grupo,
            dict
        ):

            rejeitados.append(
                {
                    "tipo":
                        "GRUPO_CST",

                    "registro":
                        numero_grupo,

                    "erros": [
                        (
                            "Grupo CST retornado pela API "
                            "não é um objeto JSON."
                        )
                    ]
                }
            )

            continue

        quantidade_grupos_cst += 1

        cst = _normalizar_texto(
            grupo.get(
                "CST"
            )
        )

        descricao_cst = _normalizar_texto(
            grupo.get(
                "DescricaoCST"
            )
        )

        inicio_vigencia_cst = _normalizar_data(
            grupo.get(
                "InicioVigencia"
            )
        )

        fim_vigencia_cst = _normalizar_data(
            grupo.get(
                "FimVigencia"
            )
        )

        classificacoes = grupo.get(
            "classificacoesTributarias"
        )

        # ----------------------------------------------------
        # SEM LISTA DE CLASSIFICAÇÕES
        # ----------------------------------------------------
        if not isinstance(
            classificacoes,
            list
        ):

            rejeitados.append(
                {
                    "tipo":
                        "GRUPO_CST",

                    "registro":
                        numero_grupo,

                    "cst":
                        cst,

                    "erros": [
                        (
                            "Lista classificacoesTributarias "
                            "não encontrada no grupo CST."
                        )
                    ]
                }
            )

            continue

        # ----------------------------------------------------
        # PERCORRER cClassTrib DO CST
        # ----------------------------------------------------
        for numero_classificacao, classificacao in enumerate(
            classificacoes,
            start=1
        ):

            if not isinstance(
                classificacao,
                dict
            ):

                rejeitados.append(
                    {
                        "tipo":
                            "CCLASSTRIB",

                        "grupo_cst":
                            numero_grupo,

                        "registro":
                            numero_classificacao,

                        "cst":
                            cst,

                        "erros": [
                            (
                                "Classificação tributária "
                                "não é um objeto JSON."
                            )
                        ]
                    }
                )

                continue

            cclass_trib = _normalizar_texto(
                classificacao.get(
                    "cClassTrib"
                )
            )

            erros = _validar_registro(
                cst,
                cclass_trib
            )

            if erros:

                rejeitados.append(
                    {
                        "tipo":
                            "CCLASSTRIB",

                        "grupo_cst":
                            numero_grupo,

                        "registro":
                            numero_classificacao,

                        "cst":
                            cst,

                        "cclass_trib":
                            cclass_trib,

                        "erros":
                            erros
                    }
                )

                continue

            descricao = _normalizar_texto(
                classificacao.get(
                    "DescricaoClassTrib"
                )
            )

            inicio_vigencia = _normalizar_data(
                classificacao.get(
                    "InicioVigencia"
                )
            )

            fim_vigencia = _normalizar_data(
                classificacao.get(
                    "FimVigencia"
                )
            )

            publicacao = _normalizar_data(
                classificacao.get(
                    "Publicacao"
                )
            )

            # ------------------------------------------------
            # REGISTRO NORMALIZADO
            # ------------------------------------------------
            registros.append(
                {
                    "cst":
                        cst,

                    "cclass_trib":
                        cclass_trib,

                    "descricao":
                        descricao,

                    "descricao_cst":
                        descricao_cst,

                    "data_inicio_vigencia":
                        (
                            inicio_vigencia
                            or
                            inicio_vigencia_cst
                        ),

                    "data_fim_vigencia":
                        (
                            fim_vigencia
                            or
                            fim_vigencia_cst
                        ),

                    "data_publicacao":
                        publicacao,

                    "ativo":
                        True,

                    # ----------------------------------------
                    # CAMPOS IMPORTANTES DA TABELA OFICIAL
                    #
                    # Neste momento mantemos no retorno para
                    # auditoria. Ainda não serão gravados
                    # na tabela simplificada do banco.
                    # ----------------------------------------
                    "ind_nfe":
                        classificacao.get(
                            "IndNFe"
                        ),

                    "ind_nfce":
                        classificacao.get(
                            "IndNFCe"
                        ),

                    "ind_ibs_cbs":
                        grupo.get(
                            "IndIBSCBS"
                        ),

                    "tipo_aliquota":
                        _normalizar_texto(
                            classificacao.get(
                                "TipoAliquota"
                            )
                        ),

                    "tipo_receita_bruta_sn":
                        _normalizar_texto(
                            classificacao.get(
                                "TipoReceitaBrutaSN"
                            )
                        ),

                    "percentual_reducao_cbs":
                        classificacao.get(
                            "pRedCBS"
                        ),

                    "percentual_reducao_ibs":
                        classificacao.get(
                            "pRedIBS"
                        ),

                    "link":
                        _normalizar_texto(
                            classificacao.get(
                                "Link"
                            )
                        )
                }
            )

    # --------------------------------------------------------
    # REMOVER DUPLICIDADES
    # --------------------------------------------------------
    registros_unicos = {}

    for registro in registros:

        chave = (
            registro.get(
                "cst"
            ),
            registro.get(
                "cclass_trib"
            )
        )

        registros_unicos[
            chave
        ] = registro

    registros = list(
        registros_unicos.values()
    )

    return {
        "sucesso": True,

        "quantidade_grupos_cst":
            quantidade_grupos_cst,

        "quantidade_registros":
            len(
                registros
            ),

        "quantidade_rejeitados":
            len(
                rejeitados
            ),

        "registros":
            registros,

        "rejeitados":
            rejeitados,

        "versao_fonte":
            VERSAO_FONTE,

        "fonte":
            FONTE
    }


# ============================================================
# COLETAR TABELA OFICIAL COM CERTIFICADO A1
#
# SOMENTE LEITURA.
#
# NÃO:
# - grava banco
# - altera produto
# - transmite NF-e
# ============================================================
def coletar_tabela_oficial(
    caminho_certificado,
    senha
):

    caminho = Path(
        caminho_certificado
    )

    # --------------------------------------------------------
    # CERTIFICADO
    # --------------------------------------------------------
    if not caminho.exists():

        return {
            "sucesso": False,
            "mensagem":
                "Certificado digital não encontrado.",
            "registros": [],
            "rejeitados": []
        }

    if not caminho.is_file():

        return {
            "sucesso": False,
            "mensagem":
                (
                    "O caminho do certificado não "
                    "corresponde a um arquivo."
                ),
            "registros": [],
            "rejeitados": []
        }

    if senha is None:

        return {
            "sucesso": False,
            "mensagem":
                "Senha do certificado não informada.",
            "registros": [],
            "rejeitados": []
        }

    # --------------------------------------------------------
    # REQUISIÇÃO TLS MÚTUO
    # --------------------------------------------------------
    try:

        resposta = pkcs12_get(
            URL_API_OFICIAL,

            pkcs12_filename=str(
                caminho
            ),

            pkcs12_password=str(
                senha
            ),

            headers={
                "Accept":
                    "application/json",

                "User-Agent":
                    (
                        "ERP-Verde-Infancia-Fiscal/1.0"
                    )
            },

            timeout=30
        )

    except Exception as erro:

        return {
            "sucesso": False,

            "mensagem":
                (
                    "Erro ao acessar a API oficial "
                    "com certificado digital."
                ),

            "detalhe_tecnico":
                str(
                    erro
                ),

            "endpoint":
                URL_API_OFICIAL,

            "registros":
                [],

            "rejeitados":
                []
        }

    status_http = resposta.status_code

    content_type = resposta.headers.get(
        "Content-Type"
    )

    # --------------------------------------------------------
    # HTTP DIFERENTE DE 200
    # --------------------------------------------------------
    if status_http != 200:

        return {
            "sucesso": False,

            "mensagem":
                (
                    "API oficial retornou status HTTP "
                    f"{status_http}."
                ),

            "status_http":
                status_http,

            "content_type":
                content_type,

            "endpoint":
                URL_API_OFICIAL,

            "resposta_inicio":
                resposta.text[
                    :500
                ],

            "registros":
                [],

            "rejeitados":
                []
        }

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------
    try:

        dados = resposta.json()

    except Exception as erro:

        return {
            "sucesso": False,

            "mensagem":
                (
                    "A API respondeu, porém o conteúdo "
                    "não pôde ser interpretado como JSON."
                ),

            "detalhe_tecnico":
                str(
                    erro
                ),

            "status_http":
                status_http,

            "content_type":
                content_type,

            "resposta_inicio":
                resposta.text[
                    :500
                ],

            "registros":
                [],

            "rejeitados":
                []
        }

    # --------------------------------------------------------
    # INTERPRETAR
    # --------------------------------------------------------
    resultado = interpretar_resposta_api(
        dados
    )

    resultado[
        "status_http"
    ] = status_http

    resultado[
        "content_type"
    ] = content_type

    resultado[
        "endpoint"
    ] = URL_API_OFICIAL

    return resultado