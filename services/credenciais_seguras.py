import os

from cryptography.fernet import Fernet, InvalidToken


def _obter_fernet():
    chave = str(
        os.getenv("ERP_ENCRYPTION_KEY") or ""
    ).strip()

    if not chave:
        raise RuntimeError(
            "ERP_ENCRYPTION_KEY nao configurada."
        )

    try:
        return Fernet(chave.encode("utf-8"))

    except (ValueError, TypeError) as erro:
        raise RuntimeError(
            "ERP_ENCRYPTION_KEY invalida."
        ) from erro


def criptografar_texto(valor):
    valor = str(
        valor or ""
    )

    if not valor:
        return None

    fernet = _obter_fernet()

    return fernet.encrypt(
        valor.encode("utf-8")
    ).decode("utf-8")


def descriptografar_texto(valor_criptografado):
    valor_criptografado = str(
        valor_criptografado or ""
    ).strip()

    if not valor_criptografado:
        return None

    fernet = _obter_fernet()

    try:
        return fernet.decrypt(
            valor_criptografado.encode("utf-8")
        ).decode("utf-8")

    except InvalidToken as erro:
        raise RuntimeError(
            "Nao foi possivel descriptografar "
            "a credencial armazenada."
        ) from erro
