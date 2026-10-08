from datetime import date, datetime
from typing import Any

import requests

from services.bancos.inter.auth import obter_token_inter
from services.bancos.inter.config import carregar_config_inter


EXTRATO_URL = "https://cdpj.partners.bancointer.com.br/banking/v2/extrato"


def _normalizar_data(valor: date | datetime | str) -> str:
    """
    Converte a data para o formato exigido pelo Banco Inter: YYYY-MM-DD.
    """
    if isinstance(valor, datetime):
        return valor.date().isoformat()

    if isinstance(valor, date):
        return valor.isoformat()

    if isinstance(valor, str):
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date().isoformat()
        except ValueError as exc:
            raise ValueError(
                "Data inválida. Utilize o formato YYYY-MM-DD."
            ) from exc

    raise TypeError("A data deve ser date, datetime ou string YYYY-MM-DD.")


def consultar_extrato(
    data_inicio: date | datetime | str,
    data_fim: date | datetime | str,
    conta_corrente: str | None = None,
) -> dict[str, Any]:
    """
    Consulta o extrato do Banco Inter.

    Esta função é somente leitura:
    - não grava no banco de dados;
    - não altera saldo do ERP;
    - não registra movimentações financeiras.
    """

    inicio = _normalizar_data(data_inicio)
    fim = _normalizar_data(data_fim)

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
    fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()

    if inicio_dt > fim_dt:
        raise ValueError("dataInicio não pode ser posterior a dataFim.")

    if (fim_dt - inicio_dt).days > 90:
        raise ValueError(
            "O Banco Inter permite consultar no máximo 90 dias por período."
        )

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

    parametros = {
        "dataInicio": inicio,
        "dataFim": fim,
    }

    resposta = requests.get(
        EXTRATO_URL,
        headers=headers,
        params=parametros,
        cert=(
            str(config.certificado),
            str(config.chave_privada),
        ),
        timeout=30,
    )

    if resposta.status_code != 200:
        mensagem = f"Falha ao consultar extrato do Banco Inter. HTTP {resposta.status_code}"

        try:
            dados_erro = resposta.json()

            detalhes_seguros = {}

            for campo in ("error", "error_description", "message", "title"):
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
            "Banco Inter retornou uma resposta que não é JSON válido."
        ) from exc

EXTRATO_COMPLETO_URL = (
    "https://cdpj.partners.bancointer.com.br/banking/v2/extrato/completo"
)


def consultar_extrato_enriquecido(
    data_inicio: date | datetime | str,
    data_fim: date | datetime | str,
    pagina: int = 0,
    tamanho_pagina: int = 50,
    conta_corrente: str | None = None,
) -> dict[str, Any]:
    """
    Consulta o extrato enriquecido do Banco Inter.

    Somente leitura:
    - não grava no PostgreSQL;
    - não altera saldo do ERP;
    - não cria movimentações financeiras.
    """

    inicio = _normalizar_data(data_inicio)
    fim = _normalizar_data(data_fim)

    inicio_dt = datetime.strptime(inicio, "%Y-%m-%d").date()
    fim_dt = datetime.strptime(fim, "%Y-%m-%d").date()

    if inicio_dt > fim_dt:
        raise ValueError("dataInicio não pode ser posterior a dataFim.")

    if (fim_dt - inicio_dt).days > 90:
        raise ValueError(
            "O Banco Inter permite consultar no máximo 90 dias por período."
        )

    if pagina < 0:
        raise ValueError("pagina não pode ser negativa.")

    if not 1 <= tamanho_pagina <= 10000:
        raise ValueError(
            "tamanhoPagina deve estar entre 1 e 10000."
        )

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

    parametros = {
        "dataInicio": inicio,
        "dataFim": fim,
        "pagina": pagina,
        "tamanhoPagina": tamanho_pagina,
    }

    resposta = requests.get(
        EXTRATO_COMPLETO_URL,
        headers=headers,
        params=parametros,
        cert=(
            str(config.certificado),
            str(config.chave_privada),
        ),
        timeout=30,
    )

    if resposta.status_code != 200:
        mensagem = (
            "Falha ao consultar extrato enriquecido do Banco Inter. "
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
            "Banco Inter retornou uma resposta que não é JSON válido."
        ) from exc