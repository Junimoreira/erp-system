from datetime import datetime

from database.empresa_db import buscar_empresa
from database.configuracoes_fiscais_db import (
    buscar_configuracao_fiscal,
)


# ============================================================
# FORMATAÇÕES
# ============================================================

def formatar_cnpj(cnpj):
    if not cnpj:
        return ""

    numeros = "".join(
        c for c in str(cnpj)
        if c.isdigit()
    )

    if len(numeros) != 14:
        return str(cnpj)

    return (
        f"{numeros[0:2]}."
        f"{numeros[2:5]}."
        f"{numeros[5:8]}/"
        f"{numeros[8:12]}-"
        f"{numeros[12:14]}"
    )


def formatar_cep(cep):
    if not cep:
        return ""

    numeros = "".join(
        c for c in str(cep)
        if c.isdigit()
    )

    if len(numeros) != 8:
        return str(cep)

    return (
        f"{numeros[0:5]}-"
        f"{numeros[5:8]}"
    )


def formatar_moeda(valor):
    try:
        valor = float(valor or 0)
    except Exception:
        valor = 0

    texto = f"{valor:,.2f}"

    texto = (
        texto
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"R$ {texto}"


def formatar_data(data):
    if not data:
        return ""

    try:
        return data.strftime("%d/%m/%Y")
    except Exception:
        return str(data)


def formatar_data_hora(data):
    if not data:
        return ""

    try:
        return data.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(data)


# ============================================================
# ENDEREÇO
# ============================================================

def montar_endereco(configuracao):
    if not configuracao:
        return ""

    partes = []

    logradouro = configuracao.get("logradouro")
    numero = configuracao.get("numero")
    complemento = configuracao.get("complemento")
    bairro = configuracao.get("bairro")
    cidade = configuracao.get("cidade")
    uf = configuracao.get("uf")
    cep = configuracao.get("cep")

    linha = ""

    if logradouro:
        linha = str(logradouro).strip()

    if numero:
        linha = (
            f"{linha}, {numero}"
            if linha
            else str(numero)
        )

    if complemento:
        linha = (
            f"{linha} - {complemento}"
            if linha
            else str(complemento)
        )

    if linha:
        partes.append(linha)

    if bairro:
        partes.append(
            str(bairro).strip()
        )

    cidade_uf = ""

    if cidade:
        cidade_uf = str(cidade).strip()

    if uf:
        cidade_uf = (
            f"{cidade_uf}/{uf}"
            if cidade_uf
            else str(uf)
        )

    if cidade_uf:
        partes.append(cidade_uf)

    if cep:
        partes.append(
            f"CEP {formatar_cep(cep)}"
        )

    return " - ".join(partes)


# ============================================================
# DADOS INSTITUCIONAIS
# ============================================================

def obter_dados_cabecalho():

    empresa = buscar_empresa() or {}
    fiscal = buscar_configuracao_fiscal() or {}

    razao_social = (
        fiscal.get("razao_social")
        or empresa.get("nome")
        or ""
    )

    nome_fantasia = (
        fiscal.get("nome_fantasia")
        or empresa.get("nome")
        or ""
    )

    cnpj = (
        fiscal.get("cnpj")
        or empresa.get("cnpj")
        or ""
    )

    return {
        "razao_social": razao_social,
        "nome_fantasia": nome_fantasia,

        "cnpj": cnpj,
        "cnpj_formatado": formatar_cnpj(
            cnpj
        ),

        "inscricao_estadual": (
            fiscal.get(
                "inscricao_estadual"
            )
            or ""
        ),

        "crt": fiscal.get("crt"),

        "endereco": montar_endereco(
            fiscal
        ),

        "telefone": (
            empresa.get("telefone")
            or ""
        ),

        "email": (
            empresa.get("email")
            or ""
        ),

        "logo": empresa.get("logo"),

        "cidade": (
            fiscal.get("cidade")
            or ""
        ),

        "uf": (
            fiscal.get("uf")
            or ""
        ),

        "gerado_em": datetime.now(),
    }