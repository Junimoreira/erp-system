import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# ==================================================
# NORMALIZAR CEP
# ==================================================
def normalizar_cep(cep):
    """
    Mantém somente os números do CEP.
    """

    return re.sub(
        r"\D",
        "",
        str(cep or "")
    )


# ==================================================
# CONSULTAR CEP
# ==================================================
def consultar_cep(cep):
    """
    Consulta o ViaCEP.

    Retornos possíveis:

    {
        "status": "sucesso",
        "dados": {...}
    }

    {
        "status": "invalido",
        "mensagem": "..."
    }

    {
        "status": "nao_encontrado",
        "mensagem": "..."
    }

    {
        "status": "erro",
        "mensagem": "..."
    }
    """

    cep_numeros = normalizar_cep(cep)

    if len(cep_numeros) != 8:
        return {
            "status": "invalido",
            "mensagem": "O CEP deve possuir 8 dígitos."
        }

    url = (
        f"https://viacep.com.br/ws/"
        f"{cep_numeros}/json/"
    )

    requisicao = Request(
        url,
        headers={
            "User-Agent": (
                "ERP-Verde-Infancia/1.0"
            )
        }
    )

    try:

        with urlopen(
            requisicao,
            timeout=10
        ) as resposta:

            conteudo = resposta.read().decode(
                "utf-8"
            )

            dados = json.loads(
                conteudo
            )

        if dados.get("erro") is True:
            return {
                "status": "nao_encontrado",
                "mensagem": (
                    "CEP não encontrado. "
                    "Confira o número informado."
                )
            }

        return {
            "status": "sucesso",
            "dados": {
                "cep": dados.get(
                    "cep",
                    ""
                ),
                "logradouro": dados.get(
                    "logradouro",
                    ""
                ),
                "complemento": dados.get(
                    "complemento",
                    ""
                ),
                "bairro": dados.get(
                    "bairro",
                    ""
                ),
                "cidade": dados.get(
                    "localidade",
                    ""
                ),
                "uf": dados.get(
                    "uf",
                    ""
                ),
                "codigo_municipio_ibge": dados.get(
                    "ibge",
                    ""
                )
            }
        }

    except HTTPError as erro:

        if erro.code == 400:
            return {
                "status": "invalido",
                "mensagem": (
                    "CEP inválido. Informe exatamente "
                    "8 números."
                )
            }

        return {
            "status": "erro",
            "mensagem": (
                f"Erro HTTP ao consultar o CEP: "
                f"{erro.code}."
            )
        }

    except URLError:

        return {
            "status": "erro",
            "mensagem": (
                "Não foi possível acessar o serviço "
                "de CEP. Verifique a conexão com a internet."
            )
        }

    except TimeoutError:

        return {
            "status": "erro",
            "mensagem": (
                "A consulta do CEP demorou mais que "
                "o esperado. Tente novamente."
            )
        }

    except json.JSONDecodeError:

        return {
            "status": "erro",
            "mensagem": (
                "O serviço de CEP retornou uma "
                "resposta inválida."
            )
        }

    except Exception as erro:

        print(
            "Erro ao consultar CEP:",
            erro
        )

        return {
            "status": "erro",
            "mensagem": (
                "Não foi possível consultar o CEP."
            )
        }