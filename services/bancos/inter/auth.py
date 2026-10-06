import requests

from services.bancos.inter.config import carregar_config_inter


TOKEN_URL = "https://cdpj.partners.bancointer.com.br/oauth/v2/token"

SCOPE_EXTRATO = "extrato.read"


class InterAuthError(RuntimeError):
    pass


def _erro_seguro_oauth(resposta):
    """
    Extrai somente informacoes de erro OAuth consideradas seguras.
    Nunca retorna token, credenciais, headers ou corpo completo.
    """
    try:
        payload = resposta.json()
    except ValueError:
        return "Resposta sem detalhes OAuth em JSON."

    campos_permitidos = (
        "error",
        "error_description",
        "message",
    )

    detalhes = []

    for campo in campos_permitidos:
        valor = payload.get(campo)

        if valor:
            detalhes.append(
                f"{campo}={valor}"
            )

    if not detalhes:
        return "Resposta sem detalhes OAuth reconhecidos."

    return "; ".join(detalhes)


def obter_token_inter():
    config = carregar_config_inter()

    dados = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "grant_type": "client_credentials",
        "scope": SCOPE_EXTRATO,
    }

    try:
        resposta = requests.post(
            TOKEN_URL,
            data=dados,
            cert=(
                str(config.certificado),
                str(config.chave_privada),
            ),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=30,
        )

    except requests.RequestException as erro:
        raise InterAuthError(
            f"Falha de comunicacao com o Banco Inter: {erro}"
        ) from erro

    if resposta.status_code != 200:
        detalhe = _erro_seguro_oauth(
            resposta
        )

        raise InterAuthError(
            "Banco Inter recusou a autenticacao. "
            f"HTTP {resposta.status_code}. "
            f"Detalhe seguro: {detalhe}"
        )

    try:
        payload = resposta.json()

    except ValueError as erro:
        raise InterAuthError(
            "Banco Inter retornou uma resposta que nao e JSON."
        ) from erro

    access_token = payload.get(
        "access_token"
    )

    if not access_token:
        raise InterAuthError(
            "Resposta do Banco Inter nao contem access_token."
        )

    return {
        "access_token": access_token,
        "token_type": payload.get("token_type"),
        "expires_in": payload.get("expires_in"),
        "scope": payload.get("scope"),
    }
