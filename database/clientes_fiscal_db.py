from database.connection import conectar


# ============================================================
# BUSCAR CLIENTE PARA EMISSÃO FISCAL
# ============================================================
def buscar_cliente_fiscal(
    cliente_id
):

    if cliente_id is None:
        return None

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                nome,
                telefone,
                email,
                cidade,
                tipo_pessoa,
                cpf,
                cnpj,
                razao_social,
                nome_fantasia,
                inscricao_estadual,
                inscricao_municipal,
                indicador_ie,
                cep,
                logradouro,
                numero,
                complemento,
                bairro,
                uf,
                codigo_municipio_ibge,
                email_fiscal,
                codigo_pais,
                pais,
                ativo

            FROM clientes

            WHERE id = %s

            LIMIT 1
            """,
            (
                cliente_id,
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "nome",
            "telefone",
            "email",
            "cidade",
            "tipo_pessoa",
            "cpf",
            "cnpj",
            "razao_social",
            "nome_fantasia",
            "inscricao_estadual",
            "inscricao_municipal",
            "indicador_ie",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "uf",
            "codigo_municipio_ibge",
            "email_fiscal",
            "codigo_pais",
            "pais",
            "ativo"
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar cliente fiscal:",
            erro
        )

        return None

    finally:

        conn.close()