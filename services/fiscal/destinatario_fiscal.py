from database.clientes_fiscal_db import (
    buscar_cliente_fiscal
)

from utils.validacoes_documentos import (
    validar_cpf
)


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

    return texto


# ============================================================
# SOMENTE NÚMEROS
# ============================================================
def _somente_numeros(
    valor
):

    texto = _normalizar(
        valor
    )

    return "".join(
        caractere
        for caractere in texto
        if caractere.isdigit()
    )


# ============================================================
# IDENTIFICAR CONSUMIDOR GENÉRICO
# ============================================================
def _cliente_generico(
    cliente
):

    if not cliente:
        return True

    cpf = _somente_numeros(
        cliente.get(
            "cpf"
        )
    )

    cnpj = _somente_numeros(
        cliente.get(
            "cnpj"
        )
    )

    nome = _normalizar(
        cliente.get(
            "nome"
        )
    ).upper()

    if (
        not cpf
        and
        not cnpj
        and
        nome in (
            "CONSUMIDOR",
            "CONSUMIDOR FINAL",
            "CLIENTE PADRÃO",
            "CLIENTE PADRAO"
        )
    ):

        return True

    return False


# ============================================================
# MONTAR DESTINATÁRIO FISCAL
# ============================================================
def montar_destinatario_fiscal(
    cliente_id,
    modelo
):

    # --------------------------------------------------------
    # SEM CLIENTE
    # --------------------------------------------------------
    if cliente_id is None:

        if modelo == 65:

            return {
                "sucesso": True,
                "identificado": False,
                "tipo": "CONSUMIDOR_NAO_IDENTIFICADO",
                "destinatario": None,
                "erros": [],
                "avisos": []
            }

        return {
            "sucesso": False,
            "identificado": False,
            "tipo": None,
            "destinatario": None,
            "erros": [
                (
                    "NF-e modelo 55 exige tratamento "
                    "do destinatário antes da emissão."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # BUSCAR CLIENTE
    # --------------------------------------------------------
    cliente = buscar_cliente_fiscal(
        cliente_id
    )

    if not cliente:

        return {
            "sucesso": False,
            "identificado": False,
            "tipo": None,
            "destinatario": None,
            "erros": [
                "Cliente não encontrado."
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # CLIENTE GENÉRICO
    # --------------------------------------------------------
    if _cliente_generico(
        cliente
    ):

        if modelo == 65:

            return {
                "sucesso": True,
                "identificado": False,
                "tipo": "CONSUMIDOR_NAO_IDENTIFICADO",
                "destinatario": None,
                "erros": [],
                "avisos": [
                    (
                        "Cliente genérico tratado como "
                        "consumidor não identificado."
                    )
                ]
            }

        return {
            "sucesso": False,
            "identificado": False,
            "tipo": None,
            "destinatario": None,
            "erros": [
                (
                    "Cliente genérico não pode ser tratado "
                    "como destinatário identificado da NF-e."
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
    # --------------------------------------------------------
    tipo_pessoa = _normalizar(
        cliente.get(
            "tipo_pessoa"
        )
    ).upper()

    cpf = _somente_numeros(
        cliente.get(
            "cpf"
        )
    )

    cnpj = _somente_numeros(
        cliente.get(
            "cnpj"
        )
    )

    erros = []
    avisos = []

    if tipo_pessoa == "PJ":

        if len(
            cnpj
        ) != 14:

            erros.append(
                "Cliente PJ sem CNPJ válido."
            )

    else:

        if not validar_cpf(
            cpf
        ):

            erros.append(
                "Cliente PF sem CPF válido."
            )

    nome = (
        _normalizar(
            cliente.get(
                "razao_social"
            )
        )
        or
        _normalizar(
            cliente.get(
                "nome"
            )
        )
    )

    if not nome:

        erros.append(
            "Destinatário sem nome/razão social."
        )

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------
    endereco = {
        "cep":
            _somente_numeros(
                cliente.get(
                    "cep"
                )
            ) or None,

        "logradouro":
            _normalizar(
                cliente.get(
                    "logradouro"
                )
            ) or None,

        "numero":
            _normalizar(
                cliente.get(
                    "numero"
                )
            ) or None,

        "complemento":
            _normalizar(
                cliente.get(
                    "complemento"
                )
            ) or None,

        "bairro":
            _normalizar(
                cliente.get(
                    "bairro"
                )
            ) or None,

        "cidade":
            _normalizar(
                cliente.get(
                    "cidade"
                )
            ) or None,

        "uf":
            _normalizar(
                cliente.get(
                    "uf"
                )
            ).upper() or None,

        "codigo_municipio_ibge":
            _normalizar(
                cliente.get(
                    "codigo_municipio_ibge"
                )
            ) or None,

        "codigo_pais":
            _normalizar(
                cliente.get(
                    "codigo_pais"
                )
            ) or "1058",

        "pais":
            _normalizar(
                cliente.get(
                    "pais"
                )
            ) or "Brasil"
    }

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    return {
        "sucesso":
            len(
                erros
            ) == 0,

        "identificado":
            True,

        "tipo":
            tipo_pessoa or "PF",

        "destinatario": {
            "cliente_id":
                cliente.get(
                    "id"
                ),

            "nome":
                nome,

            "cpf":
                cpf or None,

            "cnpj":
                cnpj or None,

            "inscricao_estadual":
                _normalizar(
                    cliente.get(
                        "inscricao_estadual"
                    )
                ) or None,

            "indicador_ie":
                cliente.get(
                    "indicador_ie"
                ),

            "email":
                (
                    _normalizar(
                        cliente.get(
                            "email_fiscal"
                        )
                    )
                    or
                    _normalizar(
                        cliente.get(
                            "email"
                        )
                    )
                    or
                    None
                ),

            "endereco":
                endereco
        },

        "erros":
            erros,

        "avisos":
            avisos
    }