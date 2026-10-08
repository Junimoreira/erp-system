from typing import Any

import requests

from services.bancos.inter.auth import obter_token_inter
from services.bancos.inter.config import carregar_config_inter


SALDO_URL = "https://cdpj.partners.bancointer.com.br/banking/v2/saldo"


def consultar_saldo(
    conta_corrente: str | None = None,
) -> dict[str, Any]:
    """
    Consulta o saldo da conta no Banco Inter.

    Somente leitura:
    - não grava no PostgreSQL;
    - não altera o saldo cadastrado no ERP;
    - não cria movimentações financeiras.
    """

    config = carregar_config_inter()
    token = obter_token_inter()

    access_token = token.get("access_token")

    if not access_token:
        raise RuntimeError("Banco Inter não retornou access_token.")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    if conta_corrente:
        conta = "".join(filter(str.isdigit, str(conta_corrente)))

        if not conta:
            raise ValueError("Conta corrente inválida.")

        headers["x-conta-corrente"] = conta

    resposta = requests.get(
        SALDO_URL,
        headers=headers,
        cert=(
            str(config.certificado),
            str(config.chave_privada),
        ),
        timeout=30,
    )

    if resposta.status_code != 200:
        mensagem = (
            "Falha ao consultar saldo do Banco Inter. "
            f"HTTP {resposta.status_code}"
        )

        try:
            dados_erro = resposta.json()
            detalhes_seguros = {}

            for campo in (
                "error",
                "error_description",
                "message",
                "title",
            ):
                if campo in dados_erro:
                    detalhes_seguros[campo] = dados_erro[campo]

            if detalhes_seguros:
                mensagem += f" - {detalhes_seguros}"

        except ValueError:
            pass

        raise RuntimeError(mensagem)

    try:
        return resposta.json()
    except ValueError as exc:
        raise RuntimeError(
            "Banco Inter retornou uma resposta de saldo "
            "que não é JSON válido."
        ) from exc