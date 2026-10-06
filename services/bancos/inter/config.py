from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InterConfig:
    client_id: str
    client_secret: str
    certificado: Path
    chave_privada: Path


def _pasta_credenciais() -> Path:
    return (
        Path.home()
        / ".erp_verde_infancia"
        / "banco_inter"
    )


def _ler_client_credentials(arquivo: Path) -> tuple[str, str]:
    if not arquivo.is_file():
        raise RuntimeError(
            f"Arquivo de credenciais do Banco Inter nao encontrado: {arquivo}"
        )

    with arquivo.open(
        "r",
        encoding="utf-8-sig",
    ) as handle:
        linhas = [
            linha.strip()
            for linha in handle
            if linha.strip()
        ]

    if len(linhas) != 2:
        raise RuntimeError(
            "Arquivo de credenciais do Banco Inter deve conter "
            "exatamente duas linhas nao vazias: "
            "Client ID na primeira e Client Secret na segunda."
        )

    client_id = linhas[0]
    client_secret = linhas[1]

    if not client_id:
        raise RuntimeError(
            "Client ID do Banco Inter nao encontrado."
        )

    if not client_secret:
        raise RuntimeError(
            "Client Secret do Banco Inter nao encontrado."
        )

    return client_id, client_secret


def carregar_config_inter() -> InterConfig:
    pasta = _pasta_credenciais()

    arquivo_credenciais = (
        pasta / "ClienteSecret_Atualizado.txt"
    )
    certificado = (
        pasta / "Inter API_Certificado.crt"
    )
    chave_privada = (
        pasta / "Inter API_Chave.key"
    )

    if not certificado.is_file():
        raise RuntimeError(
            f"Certificado do Banco Inter nao encontrado: {certificado}"
        )

    if not chave_privada.is_file():
        raise RuntimeError(
            f"Chave privada do Banco Inter nao encontrada: {chave_privada}"
        )

    client_id, client_secret = _ler_client_credentials(
        arquivo_credenciais
    )

    return InterConfig(
        client_id=client_id,
        client_secret=client_secret,
        certificado=certificado,
        chave_privada=chave_privada,
    )
