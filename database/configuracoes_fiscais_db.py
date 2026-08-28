from pathlib import Path

from database.connection import conectar


# ============================================================
# DIRETÓRIOS DO PROJETO
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

PASTA_CERTIFICADOS = (
    BASE_DIR
    / "Documentação"
    / "Certificado"
)


# ============================================================
# NORMALIZAR MODELO
# ============================================================
def _normalizar_modelo(modelo):

    try:
        modelo = int(modelo)

    except (TypeError, ValueError):
        return None

    if modelo not in (
        55,
        65,
    ):
        return None

    return modelo


# ============================================================
# NORMALIZAR INTEIRO POSITIVO
# ============================================================
def _normalizar_inteiro_positivo(valor):

    try:
        numero = int(valor)

    except (TypeError, ValueError):
        return None

    if numero <= 0:
        return None

    return numero


# ============================================================
# NORMALIZAR CAMINHO DO CERTIFICADO
# ============================================================
def _normalizar_caminho_certificado(
    caminho
):

    if caminho is None:
        return None

    texto = str(
        caminho
    ).strip()

    if not texto:
        return None

    return texto


# ============================================================
# RESOLVER CAMINHO PORTÁTIL DO CERTIFICADO
# ============================================================
def _resolver_caminho_certificado(
    caminho
):

    caminho = _normalizar_caminho_certificado(caminho)

    if not caminho:
        return None

    path_salvo = Path(caminho)

    if path_salvo.is_file():
        return path_salvo.resolve()

    if not path_salvo.is_absolute():

        candidato = BASE_DIR / path_salvo

        if candidato.is_file():
            return candidato.resolve()

    candidato = (
        PASTA_CERTIFICADOS
        / path_salvo.name
    )

    if candidato.is_file():
        return candidato.resolve()

    return candidato


# ============================================================
# PREPARAR CAMINHO DO CERTIFICADO PARA GRAVAÇÃO NO BANCO
# ============================================================
def _caminho_certificado_para_banco(
    path
):

    path = Path(path).resolve()

    try:
        relativo = path.relative_to(BASE_DIR)
        return str(relativo)

    except ValueError:
        return str(path)


# ============================================================
# BUSCAR CONFIGURAÇÃO FISCAL ATIVA
# ============================================================
def buscar_configuracao_fiscal():

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                cnpj,
                razao_social,
                nome_fantasia,
                inscricao_estadual,
                crt,

                -- ENDEREÇO DO EMITENTE
                logradouro,
                numero,
                complemento,
                bairro,
                cidade,
                codigo_municipio_ibge,
                uf,
                cep,
                codigo_pais,
                pais,

                -- CONFIGURAÇÃO DO DOCUMENTO
                ambiente,
                serie_nfe,
                proximo_numero_nfe,
                serie_nfce,
                proximo_numero_nfce,
                csc_nfce,
                csc_id_nfce,

                -- CERTIFICADO DIGITAL A1
                certificado_pfx_caminho,
                certificado_atualizado_em,

                ativo

            FROM configuracoes_fiscais
            WHERE ativo = TRUE
            ORDER BY id
            LIMIT 1
            """
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "inscricao_estadual",
            "crt",

            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "codigo_municipio_ibge",
            "uf",
            "cep",
            "codigo_pais",
            "pais",

            "ambiente",
            "serie_nfe",
            "proximo_numero_nfe",
            "serie_nfce",
            "proximo_numero_nfce",
            "csc_nfce",
            "csc_id_nfce",

            "certificado_pfx_caminho",
            "certificado_atualizado_em",

            "ativo",
        ]

        return dict(
            zip(
                colunas,
                registro,
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar configuração fiscal:",
            erro,
        )

        return None

    finally:

        conn.close()


# ============================================================
# BUSCAR CNPJ DA EMPRESA
# ============================================================
def buscar_cnpj_empresa():

    configuracao = (
        buscar_configuracao_fiscal()
    )

    if not configuracao:
        return None

    return configuracao.get(
        "cnpj"
    )


# ============================================================
# BUSCAR CERTIFICADO FISCAL
# ============================================================
def buscar_certificado_fiscal():

    configuracao = buscar_configuracao_fiscal()

    if not configuracao:

        return {
            "sucesso": False,
            "configurado": False,
            "existe": False,
            "caminho": None,
            "caminho_salvo": None,
            "nome_arquivo": None,
            "atualizado_em": None,
            "mensagem": (
                "Configuração fiscal ativa "
                "não encontrada."
            ),
        }

    caminho_salvo = configuracao.get(
        "certificado_pfx_caminho"
    )

    atualizado_em = configuracao.get(
        "certificado_atualizado_em"
    )

    caminho_salvo = _normalizar_caminho_certificado(
        caminho_salvo
    )

    if not caminho_salvo:

        return {
            "sucesso": True,
            "configurado": False,
            "existe": False,
            "caminho": None,
            "caminho_salvo": None,
            "nome_arquivo": None,
            "atualizado_em": atualizado_em,
            "mensagem": (
                "Nenhum certificado digital "
                "configurado."
            ),
        }

    path = _resolver_caminho_certificado(
        caminho_salvo
    )

    existe = bool(
        path
        and
        path.is_file()
    )

    caminho_resolvido = (
        str(path)
        if path
        else None
    )

    nome_arquivo = (
        path.name
        if path
        else Path(caminho_salvo).name
    )

    return {
        "sucesso": True,
        "configurado": True,
        "existe": existe,
        "caminho": caminho_resolvido,
        "caminho_salvo": caminho_salvo,
        "nome_arquivo": nome_arquivo,
        "atualizado_em": atualizado_em,
        "mensagem": (
            "Certificado digital configurado."
            if existe
            else
            (
                "O certificado está configurado, "
                "mas o arquivo não foi encontrado "
                "na pasta de certificados desta máquina."
            )
        ),
    }


# ============================================================
# SALVAR CERTIFICADO FISCAL
# ============================================================
def salvar_certificado_fiscal(
    caminho
):

    caminho = _normalizar_caminho_certificado(
        caminho
    )

    if not caminho:

        return {
            "sucesso": False,
            "mensagem": (
                "Caminho do certificado "
                "não informado."
            ),
        }

    path = Path(caminho)

    if not path.is_absolute():
        path = BASE_DIR / path

    if not path.is_file():

        return {
            "sucesso": False,
            "mensagem": (
                "Arquivo do certificado "
                "não encontrado."
            ),
        }

    path = path.resolve()

    extensao = (
        path.suffix
        .strip()
        .lower()
    )

    if extensao not in (
        ".pfx",
        ".p12",
    ):

        return {
            "sucesso": False,
            "mensagem": (
                "Formato de certificado inválido. "
                "Utilize um arquivo .pfx ou .p12."
            ),
        }

    caminho_banco = _caminho_certificado_para_banco(
        path
    )

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "mensagem": (
                "Não foi possível conectar "
                "ao banco de dados."
            ),
        }

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM configuracoes_fiscais
            WHERE ativo = TRUE
            ORDER BY id
            LIMIT 1
            FOR UPDATE
            """
        )

        registro = cursor.fetchone()

        if registro is None:

            raise ValueError(
                "Configuração fiscal ativa "
                "não encontrada."
            )

        configuracao_id = registro[0]

        cursor.execute(
            """
            UPDATE configuracoes_fiscais
            SET
                certificado_pfx_caminho = %s,
                certificado_atualizado_em =
                    CURRENT_TIMESTAMP,
                atualizado_em =
                    CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                caminho_banco,
                configuracao_id,
            )
        )

        conn.commit()

        return {
            "sucesso": True,
            "caminho": str(path),
            "caminho_salvo": caminho_banco,
            "nome_arquivo": path.name,
            "mensagem": (
                "Certificado digital configurado "
                "com sucesso."
            ),
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao salvar certificado fiscal:",
            erro,
        )

        return {
            "sucesso": False,
            "mensagem": str(erro),
        }

    finally:

        conn.close()


# ============================================================
# REMOVER CERTIFICADO FISCAL
#
# IMPORTANTE:
# - remove apenas a configuração do caminho
# - não apaga o arquivo físico do computador
# ============================================================
def remover_certificado_fiscal():

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "mensagem": (
                "Não foi possível conectar "
                "ao banco de dados."
            ),
        }

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM configuracoes_fiscais
            WHERE ativo = TRUE
            ORDER BY id
            LIMIT 1
            FOR UPDATE
            """
        )

        registro = cursor.fetchone()

        if registro is None:

            raise ValueError(
                "Configuração fiscal ativa "
                "não encontrada."
            )

        configuracao_id = (
            registro[0]
        )

        cursor.execute(
            """
            UPDATE configuracoes_fiscais
            SET
                certificado_pfx_caminho = NULL,
                certificado_atualizado_em =
                    CURRENT_TIMESTAMP,
                atualizado_em =
                    CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                configuracao_id,
            )
        )

        conn.commit()

        return {
            "sucesso": True,
            "mensagem": (
                "Configuração do certificado "
                "removida com sucesso."
            ),
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao remover certificado fiscal:",
            erro,
        )

        return {
            "sucesso": False,
            "mensagem": str(
                erro
            ),
        }

    finally:

        conn.close()


# ============================================================
# AVANÇAR NUMERAÇÃO FISCAL AUTORIZADA
#
# - usa SELECT ... FOR UPDATE para bloquear concorrência
# - valida modelo, série e número autorizado
# - avança somente do número autorizado para o próximo
# - é idempotente se já estiver exatamente no próximo número
# - quando recebe "conn", não faz commit/rollback/close
#   para permitir uso na mesma transação do pós-autorização
# ============================================================
def avancar_numero_fiscal_autorizado(
    modelo,
    serie,
    numero_autorizado,
    conn=None
):

    modelo = _normalizar_modelo(
        modelo
    )

    serie = (
        _normalizar_inteiro_positivo(
            serie
        )
    )

    numero_autorizado = (
        _normalizar_inteiro_positivo(
            numero_autorizado
        )
    )

    if modelo is None:

        return {
            "sucesso": False,
            "avancou": False,
            "ja_avancado": False,
            "mensagem": (
                "Modelo fiscal inválido. "
                "Use 55 ou 65."
            ),
        }

    if serie is None:

        return {
            "sucesso": False,
            "avancou": False,
            "ja_avancado": False,
            "mensagem": (
                "Série fiscal inválida."
            ),
        }

    if numero_autorizado is None:

        return {
            "sucesso": False,
            "avancou": False,
            "ja_avancado": False,
            "mensagem": (
                "Número fiscal autorizado "
                "inválido."
            ),
        }

    conexao_propria = (
        conn is None
    )

    if conexao_propria:

        conn = conectar()

        if conn is None:

            return {
                "sucesso": False,
                "avancou": False,
                "ja_avancado": False,
                "mensagem": (
                    "Não foi possível conectar "
                    "ao banco de dados."
                ),
            }

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                serie_nfe,
                proximo_numero_nfe,
                serie_nfce,
                proximo_numero_nfce
            FROM configuracoes_fiscais
            WHERE ativo = TRUE
            ORDER BY id
            LIMIT 1
            FOR UPDATE
            """
        )

        registro = cursor.fetchone()

        if registro is None:

            raise ValueError(
                "Configuração fiscal ativa "
                "não encontrada."
            )

        (
            configuracao_id,
            serie_nfe,
            proximo_numero_nfe,
            serie_nfce,
            proximo_numero_nfce,
        ) = registro

        if modelo == 55:

            serie_configurada = (
                serie_nfe
            )

            proximo_numero_atual = (
                proximo_numero_nfe
            )

            campo_numero = (
                "proximo_numero_nfe"
            )

        else:

            serie_configurada = (
                serie_nfce
            )

            proximo_numero_atual = (
                proximo_numero_nfce
            )

            campo_numero = (
                "proximo_numero_nfce"
            )

        try:

            serie_configurada = int(
                serie_configurada
            )

            proximo_numero_atual = int(
                proximo_numero_atual
            )

        except (
            TypeError,
            ValueError,
        ) as erro:

            raise ValueError(
                "Configuração de série/numeração "
                "fiscal inválida."
            ) from erro

        if serie_configurada != serie:

            raise ValueError(
                "Série do documento autorizado "
                "não corresponde à série configurada "
                "no ERP. "
                f"Documento={serie}; "
                f"ERP={serie_configurada}."
            )

        proximo_esperado = (
            numero_autorizado
            +
            1
        )

        # ----------------------------------------------------
        # CASO NORMAL
        # ----------------------------------------------------
        if (
            proximo_numero_atual
            ==
            numero_autorizado
        ):

            cursor.execute(
                f"""
                UPDATE configuracoes_fiscais
                SET
                    {campo_numero} = %s,
                    atualizado_em =
                        CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    proximo_esperado,
                    configuracao_id,
                )
            )

            if conexao_propria:
                conn.commit()

            return {
                "sucesso": True,
                "avancou": True,
                "ja_avancado": False,
                "modelo": modelo,
                "serie": serie,
                "numero_autorizado":
                    numero_autorizado,
                "numero_anterior":
                    proximo_numero_atual,
                "proximo_numero":
                    proximo_esperado,
                "mensagem": (
                    "Numeração fiscal avançada "
                    "com sucesso."
                ),
            }

        # ----------------------------------------------------
        # IDEMPOTÊNCIA
        # ----------------------------------------------------
        if (
            proximo_numero_atual
            ==
            proximo_esperado
        ):

            if conexao_propria:
                conn.commit()

            return {
                "sucesso": True,
                "avancou": False,
                "ja_avancado": True,
                "modelo": modelo,
                "serie": serie,
                "numero_autorizado":
                    numero_autorizado,
                "numero_anterior":
                    proximo_numero_atual,
                "proximo_numero":
                    proximo_numero_atual,
                "mensagem": (
                    "Numeração fiscal já havia "
                    "sido avançada."
                ),
            }

        raise ValueError(
            "Sequência fiscal inconsistente. "
            f"Número autorizado={numero_autorizado}; "
            f"próximo número no ERP="
            f"{proximo_numero_atual}. "
            "Nenhuma alteração foi realizada."
        )

    except Exception as erro:

        if conexao_propria:
            conn.rollback()

        return {
            "sucesso": False,
            "avancou": False,
            "ja_avancado": False,
            "modelo": modelo,
            "serie": serie,
            "numero_autorizado":
                numero_autorizado,
            "mensagem": str(
                erro
            ),
        }

    finally:

        if conexao_propria:
            conn.close()