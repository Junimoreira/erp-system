# ============================================================
# ORIGEM DA MERCADORIA
#
# RESPONSABILIDADE:
# - Validar o código fiscal de origem da mercadoria
# - Traduzir o código para descrição
# - Impedir valores inválidos
#
# IMPORTANTE:
# - NÃO determina automaticamente a origem
# - NÃO altera produto
# - NÃO altera banco
# - NÃO gera XML
# ============================================================


# ============================================================
# CÓDIGOS OFICIAIS DE ORIGEM DA MERCADORIA
# Campo "orig" do grupo ICMS
# ============================================================
ORIGENS_MERCADORIA = {

    "0": (
        "Nacional, exceto as indicadas "
        "nos códigos 3, 4, 5 e 8"
    ),

    "1": (
        "Estrangeira - Importação direta, "
        "exceto a indicada no código 6"
    ),

    "2": (
        "Estrangeira - Adquirida no mercado interno, "
        "exceto a indicada no código 7"
    ),

    "3": (
        "Nacional, mercadoria ou bem com Conteúdo "
        "de Importação superior a 40% e inferior "
        "ou igual a 70%"
    ),

    "4": (
        "Nacional, cuja produção tenha sido feita "
        "em conformidade com os processos produtivos "
        "básicos previstos na legislação"
    ),

    "5": (
        "Nacional, mercadoria ou bem com Conteúdo "
        "de Importação inferior ou igual a 40%"
    ),

    "6": (
        "Estrangeira - Importação direta, sem similar "
        "nacional, constante em lista específica, "
        "ou gás natural"
    ),

    "7": (
        "Estrangeira - Adquirida no mercado interno, "
        "sem similar nacional, constante em lista "
        "específica, ou gás natural"
    ),

    "8": (
        "Nacional, mercadoria ou bem com Conteúdo "
        "de Importação superior a 70%"
    )
}


# ============================================================
# NORMALIZAR
# ============================================================
def _normalizar(
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
# LISTAR ORIGENS VÁLIDAS
# ============================================================
def listar_origens_mercadoria():

    return [
        {
            "codigo":
                codigo,

            "descricao":
                descricao
        }

        for codigo, descricao
        in ORIGENS_MERCADORIA.items()
    ]


# ============================================================
# VALIDAR ORIGEM
# ============================================================
def validar_origem_mercadoria(
    origem
):

    codigo = _normalizar(
        origem
    )

    # --------------------------------------------------------
    # NÃO INFORMADA
    # --------------------------------------------------------
    if codigo is None:

        return {
            "sucesso": False,
            "valido": False,
            "codigo": None,
            "descricao": None,
            "erros": [
                (
                    "Origem da mercadoria não informada. "
                    "É necessária revisão fiscal."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # CÓDIGO INVÁLIDO
    # --------------------------------------------------------
    if codigo not in ORIGENS_MERCADORIA:

        return {
            "sucesso": False,
            "valido": False,
            "codigo":
                codigo,

            "descricao":
                None,

            "erros": [
                (
                    f"Código de origem da mercadoria "
                    f"inválido: {codigo}."
                )
            ],

            "avisos": []
        }

    # --------------------------------------------------------
    # CÓDIGO VÁLIDO
    # --------------------------------------------------------
    return {
        "sucesso": True,
        "valido": True,

        "codigo":
            codigo,

        "descricao":
            ORIGENS_MERCADORIA.get(
                codigo
            ),

        "erros": [],
        "avisos": []
    }


# ============================================================
# OBTER DESCRIÇÃO
# ============================================================
def descricao_origem_mercadoria(
    origem
):

    codigo = _normalizar(
        origem
    )

    if codigo is None:
        return None

    return ORIGENS_MERCADORIA.get(
        codigo
    )