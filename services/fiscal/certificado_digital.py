from datetime import datetime, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID, ObjectIdentifier


# ============================================================
# CERTIFICADO DIGITAL A1
#
# RESPONSABILIDADE:
# - Ler arquivo .pfx / .p12
# - Validar senha
# - Confirmar existência da chave privada
# - Ler titular, emissor, validade e número de série
# - Tentar identificar CNPJ ICP-Brasil
#
# IMPORTANTE:
# - NÃO transmite para SEFAZ
# - NÃO altera banco
# - NÃO grava certificado
# - NÃO grava senha
# - NÃO exporta chave privada
# ============================================================


# OID ICP-Brasil para CNPJ de pessoa jurídica
OID_CNPJ_ICP_BRASIL = ObjectIdentifier(
    "2.16.76.1.3.3"
)


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
        "NONE",
        "NULL",
        "NAN",
        "<NA>"
    ):

        return None

    return texto


# ============================================================
# SOMENTE NÚMEROS
# ============================================================
def _somente_numeros(
    valor
):

    texto = _normalizar_texto(
        valor
    )

    if texto is None:
        return None

    numeros = "".join(
        caractere
        for caractere in texto
        if caractere.isdigit()
    )

    return (
        numeros
        if numeros
        else None
    )


# ============================================================
# FORMATAR NOME X509
# ============================================================
def _nome_x509_para_texto(
    nome
):

    if nome is None:
        return None

    partes = []

    for atributo in nome:

        oid_nome = (
            getattr(
                atributo.oid,
                "_name",
                None
            )
            or
            atributo.oid.dotted_string
        )

        partes.append(
            f"{oid_nome}={atributo.value}"
        )

    return ", ".join(
        partes
    )


# ============================================================
# BUSCAR COMMON NAME
# ============================================================
def _buscar_common_name(
    certificado
):

    try:

        atributos = (
            certificado.subject.get_attributes_for_oid(
                NameOID.COMMON_NAME
            )
        )

        if atributos:
            return atributos[0].value

    except Exception:
        pass

    return None


# ============================================================
# BUSCAR CNPJ NO SUBJECT ALTERNATIVE NAME
#
# Certificados ICP-Brasil PJ podem carregar o CNPJ
# no otherName OID 2.16.76.1.3.3.
# ============================================================
def _buscar_cnpj_san(
    certificado
):

    try:

        extensao = (
            certificado.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            )
        )

    except x509.ExtensionNotFound:

        return None

    except Exception:

        return None

    try:

        outros_nomes = (
            extensao.value.get_values_for_type(
                x509.OtherName
            )
        )

    except Exception:

        return None

    for outro_nome in outros_nomes:

        if outro_nome.type_id != OID_CNPJ_ICP_BRASIL:
            continue

        valor = outro_nome.value

        # ----------------------------------------------------
        # O conteúdo de OtherName é DER codificado.
        #
        # Nesta etapa fazemos somente uma extração
        # conservadora dos dígitos presentes no conteúdo.
        # Não usamos isso para assinatura/transmissão.
        # ----------------------------------------------------
        try:

            texto = valor.decode(
                "latin-1",
                errors="ignore"
            )

        except Exception:

            texto = str(
                valor
            )

        numeros = _somente_numeros(
            texto
        )

        if numeros:

            # O CNPJ possui 14 dígitos.
            # Se houver conteúdo adicional, procuramos
            # uma sequência de exatamente 14 dígitos.
            for inicio in range(
                0,
                max(
                    1,
                    len(numeros) - 13
                )
            ):

                candidato = numeros[
                    inicio:
                    inicio + 14
                ]

                if len(
                    candidato
                ) == 14:

                    return candidato

    return None


# ============================================================
# BUSCAR CNPJ NO COMMON NAME
#
# Algumas AC apresentam CNPJ no CN.
# Usamos apenas como informação auxiliar.
# ============================================================
def _buscar_cnpj_common_name(
    common_name
):

    texto = _normalizar_texto(
        common_name
    )

    if texto is None:
        return None

    numeros = _somente_numeros(
        texto
    )

    if not numeros:
        return None

    # Procurar sequências possíveis de 14 dígitos.
    for inicio in range(
        0,
        max(
            1,
            len(numeros) - 13
        )
    ):

        candidato = numeros[
            inicio:
            inicio + 14
        ]

        if len(
            candidato
        ) == 14:

            return candidato

    return None


# ============================================================
# NORMALIZAR DATETIME DO CERTIFICADO
# ============================================================
def _normalizar_datetime(
    valor
):

    if valor is None:
        return None

    if valor.tzinfo is None:

        return valor.replace(
            tzinfo=timezone.utc
        )

    return valor.astimezone(
        timezone.utc
    )


# ============================================================
# CARREGAR CERTIFICADO A1
#
# IMPORTANTE:
# O caminho do certificado NÃO deve ficar fixo neste módulo.
# Ele é recebido pelo parâmetro caminho_certificado.
#
# Isso permite:
# - teste local
# - configuração futura pelo ERP
# - ambiente de produção
# - troca do certificado sem alterar este código
# ============================================================
def carregar_certificado_a1(
    caminho_certificado,
    senha
):

    erros = []
    avisos = []

    # --------------------------------------------------------
    # VALIDAR CAMINHO INFORMADO
    # --------------------------------------------------------
    if caminho_certificado is None:

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                "Caminho do certificado não informado."
            ],
            "avisos": []
        }

    try:

        caminho = Path(
            caminho_certificado
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                (
                    "Caminho do certificado inválido: "
                    f"{erro}"
                )
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # VALIDAR ARQUIVO
    # --------------------------------------------------------
    if not caminho.exists():

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                (
                    "Arquivo de certificado "
                    "não encontrado."
                )
            ],
            "avisos": []
        }

    if not caminho.is_file():

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                (
                    "O caminho informado não "
                    "é um arquivo."
                )
            ],
            "avisos": []
        }

    extensao = caminho.suffix.lower()

    if extensao not in (
        ".pfx",
        ".p12"
    ):

        avisos.append(
            (
                "A extensão do arquivo não é "
                ".pfx ou .p12."
            )
        )

    # --------------------------------------------------------
    # SENHA
    # --------------------------------------------------------
    if senha is None:

        senha_bytes = None

    elif isinstance(
        senha,
        bytes
    ):

        senha_bytes = senha

    else:

        senha_bytes = str(
            senha
        ).encode(
            "utf-8"
        )

    # --------------------------------------------------------
    # LER ARQUIVO
    # --------------------------------------------------------
    try:

        conteudo = caminho.read_bytes()

    except Exception as erro:

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                (
                    "Não foi possível ler o "
                    f"certificado: {erro}"
                )
            ],
            "avisos":
                avisos
        }

    if not conteudo:

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                "O arquivo do certificado está vazio."
            ],
            "avisos":
                avisos
        }

    # --------------------------------------------------------
    # ABRIR PKCS#12
    # --------------------------------------------------------
    try:

        (
            chave_privada,
            certificado,
            certificados_adicionais
        ) = pkcs12.load_key_and_certificates(
            conteudo,
            senha_bytes
        )

    except Exception as erro:

        return {
            "sucesso": False,
            "valido": False,
            "erros": [
                (
                    "Não foi possível abrir o certificado. "
                    "Verifique se o arquivo é A1/PKCS#12 "
                    "e se a senha está correta."
                )
            ],
            "detalhe_tecnico":
                str(
                    erro
                ),
            "avisos":
                avisos
        }

    # --------------------------------------------------------
    # CERTIFICADO PRINCIPAL
    # --------------------------------------------------------
    if certificado is None:

        erros.append(
            (
                "O arquivo PKCS#12 não possui "
                "certificado principal."
            )
        )

    if chave_privada is None:

        erros.append(
            (
                "O arquivo PKCS#12 não possui "
                "chave privada."
            )
        )

    if certificado is None:

        return {
            "sucesso": False,
            "valido": False,
            "possui_chave_privada":
                chave_privada is not None,
            "erros":
                erros,
            "avisos":
                avisos
        }

    # --------------------------------------------------------
    # VALIDADE
    # --------------------------------------------------------
    try:

        inicio_validade = (
            certificado.not_valid_before_utc
        )

        fim_validade = (
            certificado.not_valid_after_utc
        )

    except AttributeError:

        inicio_validade = (
            certificado.not_valid_before
        )

        fim_validade = (
            certificado.not_valid_after
        )

    inicio_validade = _normalizar_datetime(
        inicio_validade
    )

    fim_validade = _normalizar_datetime(
        fim_validade
    )

    agora = datetime.now(
        timezone.utc
    )

    ainda_nao_valido = (
        inicio_validade is not None
        and
        agora < inicio_validade
    )

    expirado = (
        fim_validade is not None
        and
        agora > fim_validade
    )

    if ainda_nao_valido:

        erros.append(
            "Certificado ainda não está válido."
        )

    if expirado:

        erros.append(
            "Certificado está vencido."
        )

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
    # --------------------------------------------------------
    common_name = _buscar_common_name(
        certificado
    )

    cnpj_san = _buscar_cnpj_san(
        certificado
    )

    cnpj_cn = _buscar_cnpj_common_name(
        common_name
    )

    cnpj = (
        cnpj_san
        or
        cnpj_cn
    )

    if cnpj is None:

        avisos.append(
            (
                "Não foi possível identificar "
                "automaticamente o CNPJ no certificado."
            )
        )

    # --------------------------------------------------------
    # EMISSOR
    # --------------------------------------------------------
    emissor = _nome_x509_para_texto(
        certificado.issuer
    )

    titular = _nome_x509_para_texto(
        certificado.subject
    )

    # --------------------------------------------------------
    # ALGORITMO DE ASSINATURA
    # --------------------------------------------------------
    try:

        algoritmo_assinatura = (
            certificado.signature_algorithm_oid.dotted_string
        )

    except Exception:

        algoritmo_assinatura = None

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    valido = (
        len(
            erros
        ) == 0
    )

    return {
        "sucesso":
            valido,

        "valido":
            valido,

        "arquivo":
            caminho.name,

        "extensao":
            extensao,

        "possui_chave_privada":
            chave_privada is not None,

        "quantidade_certificados_adicionais":
            len(
                certificados_adicionais
                or []
            ),

        "titular":
            titular,

        "common_name":
            common_name,

        "cnpj":
            cnpj,

        "cnpj_encontrado_por":
            (
                "SUBJECT_ALTERNATIVE_NAME"
                if cnpj_san
                else
                "COMMON_NAME"
                if cnpj_cn
                else
                None
            ),

        "emissor":
            emissor,

        "numero_serie":
            str(
                certificado.serial_number
            ),

        "inicio_validade":
            inicio_validade,

        "fim_validade":
            fim_validade,

        "ainda_nao_valido":
            ainda_nao_valido,

        "expirado":
            expirado,

        "algoritmo_assinatura":
            algoritmo_assinatura,

        "erros":
            erros,

        "avisos":
            avisos
    }