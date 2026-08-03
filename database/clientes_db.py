import re

import pandas as pd

from database.connection import conectar


# ==================================================
# NORMALIZAÇÕES
# ==================================================
def normalizar_texto(valor):

    if valor is None:
        return ""

    return " ".join(
        str(valor).strip().split()
    )


def normalizar_email(email):

    return normalizar_texto(
        email
    ).lower()


def somente_numeros(valor):

    if valor is None:
        return ""

    return re.sub(
        r"\D",
        "",
        str(valor)
    )


def normalizar_telefone(telefone):

    numeros = somente_numeros(
        telefone
    )

    if (
        numeros.startswith("55")
        and len(numeros) in (12, 13)
    ):
        numeros = numeros[2:]

    return numeros


def normalizar_cpf(cpf):

    return somente_numeros(
        cpf
    )


def normalizar_cnpj(cnpj):
    """
    Mantém somente letras e números.

    O campo permanece preparado para CNPJ
    numérico ou alfanumérico.
    """

    if cnpj is None:
        return ""

    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        str(cnpj)
    ).upper()


def normalizar_cep(cep):

    return somente_numeros(
        cep
    )


def formatar_telefone_brasil(telefone):

    numeros = normalizar_telefone(
        telefone
    )

    if not numeros:
        return ""

    if len(numeros) == 11:

        return (
            f"({numeros[0:2]}) "
            f"{numeros[2:7]}-"
            f"{numeros[7:11]}"
        )

    if len(numeros) == 10:

        return (
            f"({numeros[0:2]}) "
            f"{numeros[2:6]}-"
            f"{numeros[6:10]}"
        )

    return numeros


def formatar_cpf(cpf):

    numeros = normalizar_cpf(
        cpf
    )

    if len(numeros) != 11:
        return numeros

    return (
        f"{numeros[0:3]}."
        f"{numeros[3:6]}."
        f"{numeros[6:9]}-"
        f"{numeros[9:11]}"
    )


def formatar_cnpj(cnpj):

    valor = normalizar_cnpj(
        cnpj
    )

    if len(valor) != 14:
        return valor

    # A máscara padrão é aplicada apenas
    # quando o CNPJ possui 14 caracteres.
    return (
        f"{valor[0:2]}."
        f"{valor[2:5]}."
        f"{valor[5:8]}/"
        f"{valor[8:12]}-"
        f"{valor[12:14]}"
    )


def formatar_cep(cep):

    numeros = normalizar_cep(
        cep
    )

    if len(numeros) != 8:
        return numeros

    return (
        f"{numeros[0:5]}-"
        f"{numeros[5:8]}"
    )


# ==================================================
# LISTAR CLIENTES
# ==================================================
def listar_clientes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                nome,
                telefone,
                email,
                criado_em,
                cidade,
                data_nascimento,
                tipo_pessoa,
                cpf,
                cnpj,
                razao_social,
                nome_fantasia,
                inscricao_estadual,
                inscricao_municipal,
                indicador_ie,
                email_fiscal,
                cep,
                logradouro,
                numero,
                complemento,
                bairro,
                uf,
                codigo_municipio_ibge,
                codigo_pais,
                pais,
                observacoes,
                ativo,
                atualizado_em
            FROM clientes
            ORDER BY nome, id
        """

        return pd.read_sql(
            query,
            conn
        )

    except Exception as erro:

        print(
            "Erro listar clientes:",
            erro
        )

        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# BUSCAR DUPLICIDADE
# ==================================================
def buscar_cliente_duplicado(
    cpf="",
    cnpj="",
    telefone="",
    email="",
    ignorar_cliente_id=None
):

    cpf_normalizado = normalizar_cpf(
        cpf
    )

    cnpj_normalizado = normalizar_cnpj(
        cnpj
    )

    telefone_normalizado = normalizar_telefone(
        telefone
    )

    email_normalizado = normalizar_email(
        email
    )

    if not any([
        cpf_normalizado,
        cnpj_normalizado,
        telefone_normalizado,
        email_normalizado
    ]):
        return None

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        condicoes = []
        parametros = []

        if cpf_normalizado:

            condicoes.append("""
                REGEXP_REPLACE(
                    COALESCE(cpf, ''),
                    '[^0-9]',
                    '',
                    'g'
                ) = %s
            """)

            parametros.append(
                cpf_normalizado
            )

        if cnpj_normalizado:

            condicoes.append("""
                UPPER(
                    REGEXP_REPLACE(
                        COALESCE(cnpj, ''),
                        '[^A-Za-z0-9]',
                        '',
                        'g'
                    )
                ) = %s
            """)

            parametros.append(
                cnpj_normalizado
            )

        if telefone_normalizado:

            condicoes.append("""
                CASE
                    WHEN
                        REGEXP_REPLACE(
                            COALESCE(telefone, ''),
                            '[^0-9]',
                            '',
                            'g'
                        ) LIKE '55%%'
                        AND LENGTH(
                            REGEXP_REPLACE(
                                COALESCE(telefone, ''),
                                '[^0-9]',
                                '',
                                'g'
                            )
                        ) IN (12, 13)
                    THEN SUBSTRING(
                        REGEXP_REPLACE(
                            COALESCE(telefone, ''),
                            '[^0-9]',
                            '',
                            'g'
                        )
                        FROM 3
                    )
                    ELSE REGEXP_REPLACE(
                        COALESCE(telefone, ''),
                        '[^0-9]',
                        '',
                        'g'
                    )
                END = %s
            """)

            parametros.append(
                telefone_normalizado
            )

        if email_normalizado:

            condicoes.append("""
                LOWER(
                    TRIM(
                        COALESCE(email, '')
                    )
                ) = %s
            """)

            parametros.append(
                email_normalizado
            )

        query = f"""
            SELECT
                id,
                nome,
                telefone,
                email,
                tipo_pessoa,
                cpf,
                cnpj,
                razao_social
            FROM clientes
            WHERE (
                {" OR ".join(condicoes)}
            )
        """

        if ignorar_cliente_id is not None:

            query += """
                AND id <> %s
            """

            parametros.append(
                int(ignorar_cliente_id)
            )

        query += """
            ORDER BY id
            LIMIT 1
        """

        cursor.execute(
            query,
            tuple(parametros)
        )

        resultado = cursor.fetchone()

        if resultado is None:
            return None

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        return dict(
            zip(
                colunas,
                resultado
            )
        )

    except Exception as erro:

        print(
            "Erro buscar cliente duplicado:",
            erro
        )

        return None

    finally:
        cursor.close()
        conn.close()


# ==================================================
# CADASTRAR CLIENTE
# ==================================================
def cadastrar_cliente(
    nome,
    telefone="",
    email="",
    cidade="",
    data_nascimento=None,
    tipo_pessoa="PF",
    cpf="",
    cnpj="",
    razao_social="",
    nome_fantasia="",
    inscricao_estadual="",
    inscricao_municipal="",
    indicador_ie=9,
    email_fiscal="",
    cep="",
    logradouro="",
    numero="",
    complemento="",
    bairro="",
    uf="",
    codigo_municipio_ibge="",
    codigo_pais="1058",
    pais="Brasil",
    observacoes="",
    ativo=True
):

    tipo_pessoa = normalizar_texto(
        tipo_pessoa
    ).upper()

    nome = normalizar_texto(
        nome
    )

    telefone = formatar_telefone_brasil(
        telefone
    )

    email = normalizar_email(
        email
    )

    cidade = normalizar_texto(
        cidade
    )

    cpf = formatar_cpf(
        cpf
    )

    cnpj = formatar_cnpj(
        cnpj
    )

    razao_social = normalizar_texto(
        razao_social
    )

    nome_fantasia = normalizar_texto(
        nome_fantasia
    )

    inscricao_estadual = normalizar_texto(
        inscricao_estadual
    )

    inscricao_municipal = normalizar_texto(
        inscricao_municipal
    )

    email_fiscal = normalizar_email(
        email_fiscal
    )

    cep = formatar_cep(
        cep
    )

    logradouro = normalizar_texto(
        logradouro
    )

    numero = normalizar_texto(
        numero
    )

    complemento = normalizar_texto(
        complemento
    )

    bairro = normalizar_texto(
        bairro
    )

    uf = normalizar_texto(
        uf
    ).upper()

    codigo_municipio_ibge = somente_numeros(
        codigo_municipio_ibge
    )

    codigo_pais = somente_numeros(
        codigo_pais
    ) or "1058"

    pais = normalizar_texto(
        pais
    ) or "Brasil"

    observacoes = normalizar_texto(
        observacoes
    )

    if tipo_pessoa == "PF":
        cnpj = ""
        razao_social = ""
        nome_fantasia = ""

    elif tipo_pessoa == "PJ":
        cpf = ""

        if razao_social:
            nome = razao_social

    duplicado = buscar_cliente_duplicado(
        cpf=cpf,
        cnpj=cnpj,
        telefone=telefone,
        email=email
    )

    if duplicado is not None:

        return {
            "status": "duplicado",
            "cliente": duplicado
        }

    conn = conectar()

    if conn is None:

        return {
            "status": "erro",
            "mensagem": "Não foi possível conectar ao banco."
        }

    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO clientes (
                nome,
                telefone,
                email,
                cidade,
                data_nascimento,
                tipo_pessoa,
                cpf,
                cnpj,
                razao_social,
                nome_fantasia,
                inscricao_estadual,
                inscricao_municipal,
                indicador_ie,
                email_fiscal,
                cep,
                logradouro,
                numero,
                complemento,
                bairro,
                uf,
                codigo_municipio_ibge,
                codigo_pais,
                pais,
                observacoes,
                ativo,
                atualizado_em
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP
            )
            RETURNING id
        """, (
            nome,
            telefone,
            email,
            cidade,
            data_nascimento,
            tipo_pessoa,
            cpf or None,
            cnpj or None,
            razao_social or None,
            nome_fantasia or None,
            inscricao_estadual or None,
            inscricao_municipal or None,
            int(indicador_ie),
            email_fiscal or None,
            cep or None,
            logradouro or None,
            numero or None,
            complemento or None,
            bairro or None,
            uf or None,
            codigo_municipio_ibge or None,
            codigo_pais,
            pais,
            observacoes or None,
            bool(ativo)
        ))

        cliente_id = cursor.fetchone()[0]

        conn.commit()

        return {
            "status": "sucesso",
            "cliente_id": cliente_id
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro cadastrar cliente:",
            erro
        )

        return {
            "status": "erro",
            "mensagem": str(erro)
        }

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CLIENTE
# ==================================================
def atualizar_cliente(
    cliente_id,
    nome,
    telefone="",
    email="",
    cidade="",
    data_nascimento=None,
    tipo_pessoa="PF",
    cpf="",
    cnpj="",
    razao_social="",
    nome_fantasia="",
    inscricao_estadual="",
    inscricao_municipal="",
    indicador_ie=9,
    email_fiscal="",
    cep="",
    logradouro="",
    numero="",
    complemento="",
    bairro="",
    uf="",
    codigo_municipio_ibge="",
    codigo_pais="1058",
    pais="Brasil",
    observacoes="",
    ativo=True
):

    tipo_pessoa = normalizar_texto(
        tipo_pessoa
    ).upper()

    nome = normalizar_texto(
        nome
    )

    telefone = formatar_telefone_brasil(
        telefone
    )

    email = normalizar_email(
        email
    )

    cidade = normalizar_texto(
        cidade
    )

    cpf = formatar_cpf(
        cpf
    )

    cnpj = formatar_cnpj(
        cnpj
    )

    razao_social = normalizar_texto(
        razao_social
    )

    nome_fantasia = normalizar_texto(
        nome_fantasia
    )

    inscricao_estadual = normalizar_texto(
        inscricao_estadual
    )

    inscricao_municipal = normalizar_texto(
        inscricao_municipal
    )

    email_fiscal = normalizar_email(
        email_fiscal
    )

    cep = formatar_cep(
        cep
    )

    logradouro = normalizar_texto(
        logradouro
    )

    numero = normalizar_texto(
        numero
    )

    complemento = normalizar_texto(
        complemento
    )

    bairro = normalizar_texto(
        bairro
    )

    uf = normalizar_texto(
        uf
    ).upper()

    codigo_municipio_ibge = somente_numeros(
        codigo_municipio_ibge
    )

    codigo_pais = somente_numeros(
        codigo_pais
    ) or "1058"

    pais = normalizar_texto(
        pais
    ) or "Brasil"

    observacoes = normalizar_texto(
        observacoes
    )

    if tipo_pessoa == "PF":
        cnpj = ""
        razao_social = ""
        nome_fantasia = ""

    elif tipo_pessoa == "PJ":
        cpf = ""

        if razao_social:
            nome = razao_social

    duplicado = buscar_cliente_duplicado(
        cpf=cpf,
        cnpj=cnpj,
        telefone=telefone,
        email=email,
        ignorar_cliente_id=cliente_id
    )

    if duplicado is not None:

        return {
            "status": "duplicado",
            "cliente": duplicado
        }

    conn = conectar()

    if conn is None:

        return {
            "status": "erro",
            "mensagem": "Não foi possível conectar ao banco."
        }

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE clientes
            SET
                nome = %s,
                telefone = %s,
                email = %s,
                cidade = %s,
                data_nascimento = %s,
                tipo_pessoa = %s,
                cpf = %s,
                cnpj = %s,
                razao_social = %s,
                nome_fantasia = %s,
                inscricao_estadual = %s,
                inscricao_municipal = %s,
                indicador_ie = %s,
                email_fiscal = %s,
                cep = %s,
                logradouro = %s,
                numero = %s,
                complemento = %s,
                bairro = %s,
                uf = %s,
                codigo_municipio_ibge = %s,
                codigo_pais = %s,
                pais = %s,
                observacoes = %s,
                ativo = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            nome,
            telefone,
            email,
            cidade,
            data_nascimento,
            tipo_pessoa,
            cpf or None,
            cnpj or None,
            razao_social or None,
            nome_fantasia or None,
            inscricao_estadual or None,
            inscricao_municipal or None,
            int(indicador_ie),
            email_fiscal or None,
            cep or None,
            logradouro or None,
            numero or None,
            complemento or None,
            bairro or None,
            uf or None,
            codigo_municipio_ibge or None,
            codigo_pais,
            pais,
            observacoes or None,
            bool(ativo),
            int(cliente_id)
        ))

        if cursor.rowcount == 0:

            conn.rollback()

            return {
                "status": "nao_encontrado",
                "mensagem": "Cliente não encontrado."
            }

        conn.commit()

        return {
            "status": "sucesso",
            "cliente_id": int(cliente_id)
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro atualizar cliente:",
            erro
        )

        return {
            "status": "erro",
            "mensagem": str(erro)
        }

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CLIENTE
# ==================================================
def excluir_cliente(cliente_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM vendas
            WHERE cliente_id = %s
        """, (
            int(cliente_id),
        ))

        total_vendas = cursor.fetchone()[0]

        if total_vendas > 0:
            return "possui_vendas"

        cursor.execute("""
            SELECT COUNT(*)
            FROM contas_receber
            WHERE cliente_id = %s
        """, (
            int(cliente_id),
        ))

        total_contas = cursor.fetchone()[0]

        if total_contas > 0:
            return "possui_contas"

        cursor.execute("""
            DELETE FROM clientes
            WHERE id = %s
        """, (
            int(cliente_id),
        ))

        if cursor.rowcount == 0:

            conn.rollback()

            return "nao_encontrado"

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao excluir cliente:",
            erro
        )

        return False

    finally:
        cursor.close()
        conn.close()