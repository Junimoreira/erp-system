# database/produto_db.py

import pandas as pd
import streamlit as st

from database.connection import conectar


# ==================================================
# CÓDIGOS INTERNOS DE UNIFORMES
# ==================================================

PREFIXO_UNIFORME = "26"


TAMANHOS_UNIFORME = {
    "2": "02",
    "4": "04",
    "6": "06",
    "8": "08",
    "10": "10",
    "12": "12",
    "14": "14",
    "16": "16",
    "P": "21",
    "M": "22",
    "G": "23",
    "GG": "24",
    "EG": "25",
    "EXG": "26",
}


def gerar_codigo_uniforme(
    codigo_escola,
    codigo_modelo,
    tamanho
):
    """
    Gera código interno numérico para uniformes.

    Estrutura:
        26 + escola + modelo + tamanho

    Exemplo:
        26 01 001 08

    Resultado:
        260100108

    Onde:
        26  = prefixo de uniforme
        01  = escola
        001 = modelo/tipo do uniforme
        08  = tamanho
    """

    try:

        # ------------------------------------------
        # ESCOLA
        # ------------------------------------------

        codigo_escola = int(codigo_escola)

        if codigo_escola < 1 or codigo_escola > 99:

            st.error(
                "⚠️ O código da escola deve estar "
                "entre 1 e 99."
            )

            return None

        escola_formatada = f"{codigo_escola:02d}"

        # ------------------------------------------
        # MODELO / TIPO
        # ------------------------------------------

        codigo_modelo = int(codigo_modelo)

        if codigo_modelo < 1 or codigo_modelo > 999:

            st.error(
                "⚠️ O código do modelo deve estar "
                "entre 1 e 999."
            )

            return None

        modelo_formatado = f"{codigo_modelo:03d}"

        # ------------------------------------------
        # TAMANHO
        # ------------------------------------------

        tamanho = str(tamanho).strip().upper()

        if tamanho not in TAMANHOS_UNIFORME:

            st.error(
                f"⚠️ Tamanho de uniforme inválido: {tamanho}"
            )

            return None

        codigo_tamanho = TAMANHOS_UNIFORME[tamanho]

        # ------------------------------------------
        # MONTA O CÓDIGO
        # ------------------------------------------

        codigo = (
            PREFIXO_UNIFORME
            + escola_formatada
            + modelo_formatado
            + codigo_tamanho
        )

        return codigo

    except (ValueError, TypeError):

        st.error(
            "⚠️ Código da escola ou modelo inválido."
        )

        return None


def verificar_codigo_barras_disponivel(codigo_barras):
    """
    Verifica se um código de barras já está sendo
    utilizado por outro produto.
    """

    if not codigo_barras:
        return False

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                nome
            FROM produtos
            WHERE codigo_barras = %s
            LIMIT 1
            """,
            (str(codigo_barras),)
        )

        existente = cursor.fetchone()

        if existente:

            return {
                "disponivel": False,
                "produto_id": existente[0],
                "produto_nome": existente[1]
            }

        return {
            "disponivel": True,
            "produto_id": None,
            "produto_nome": None
        }

    except Exception as erro:

        st.error(
            f"Erro ao verificar código de barras: {erro}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR PRODUTOS
# ==================================================

def listar_produtos():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                nome,
                tamanho,
                sku,
                referencia,
                marca,
                categoria,
                codigo_barras,
                unidade,
                ncm,
                cest,
                cfop_padrao,
                custo,
                preco,
                margem_lucro,
                estoque,
                estoque_minimo,
                localizacao,
                ativo,
                observacoes,
                data_cadastro
            FROM produtos
            ORDER BY id DESC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:

        st.error(f"Erro ao listar produtos: {erro}")

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# BUSCAR PRODUTO POR ID
# ==================================================

def buscar_produto_por_id(produto_id):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                nome,
                tamanho,
                sku,
                referencia,
                marca,
                categoria,
                codigo_barras,
                unidade,
                ncm,
                cest,
                cfop_padrao,
                custo,
                preco,
                margem_lucro,
                estoque,
                estoque_minimo,
                localizacao,
                ativo,
                observacoes,
                data_cadastro
            FROM produtos
            WHERE id = %s
            LIMIT 1
            """,
            (produto_id,)
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        return dict(zip(colunas, registro))

    except Exception as erro:

        st.error(f"Erro ao buscar produto: {erro}")

        return None

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR PRODUTOS SEM CÓDIGO
# ==================================================

def listar_produtos_sem_codigo():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                nome,
                tamanho,
                codigo_barras,
                preco,
                estoque
            FROM produtos
            WHERE codigo_barras IS NULL
               OR codigo_barras = ''
            ORDER BY nome
        """

        return pd.read_sql(query, conn)

    except Exception as erro:

        st.error(
            f"Erro ao listar produtos sem código: {erro}"
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# CADASTRAR PRODUTO
# ==================================================

def cadastrar_produto(
    nome,
    preco,
    estoque,
    codigo_barras,
    sku,
    referencia,
    marca,
    categoria,
    unidade,
    ncm,
    cest,
    cfop_padrao,
    custo,
    margem_lucro,
    estoque_minimo,
    localizacao,
    ativo,
    observacoes,
    tamanho=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # ------------------------------------------
        # VALIDA CÓDIGO DE BARRAS DUPLICADO
        # ------------------------------------------

        if codigo_barras:

            cursor.execute(
                """
                SELECT id
                FROM produtos
                WHERE codigo_barras = %s
                LIMIT 1
                """,
                (codigo_barras,)
            )

            if cursor.fetchone():

                st.error(
                    "⚠️ Já existe produto com este "
                    "código de barras."
                )

                return False

        # ------------------------------------------
        # CADASTRA PRODUTO
        # ------------------------------------------

        cursor.execute(
            """
            INSERT INTO produtos (
                nome,
                tamanho,
                preco,
                estoque,
                codigo_barras,
                sku,
                referencia,
                marca,
                categoria,
                unidade,
                ncm,
                cest,
                cfop_padrao,
                custo,
                margem_lucro,
                estoque_minimo,
                localizacao,
                ativo,
                observacoes
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s
            )
            """,
            (
                nome,
                tamanho,
                preco,
                estoque,
                codigo_barras,
                sku,
                referencia,
                marca,
                categoria,
                unidade,
                ncm,
                cest,
                cfop_padrao,
                custo,
                margem_lucro,
                estoque_minimo,
                localizacao,
                ativo,
                observacoes
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        st.error(
            f"Erro ao cadastrar produto: {erro}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR PRODUTO
# ==================================================

def atualizar_produto(
    id_produto,
    nome,
    preco,
    estoque,
    codigo_barras,
    sku,
    referencia,
    marca,
    categoria,
    unidade,
    ncm,
    cest,
    cfop_padrao,
    custo,
    margem_lucro,
    estoque_minimo,
    localizacao,
    ativo,
    observacoes,
    tamanho=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # ------------------------------------------
        # VALIDA CÓDIGO DUPLICADO
        # ------------------------------------------

        if codigo_barras:

            cursor.execute(
                """
                SELECT id
                FROM produtos
                WHERE codigo_barras = %s
                  AND id <> %s
                LIMIT 1
                """,
                (
                    codigo_barras,
                    id_produto
                )
            )

            if cursor.fetchone():

                st.error(
                    "⚠️ Este código de barras já pertence "
                    "a outro produto."
                )

                return False

        # ------------------------------------------
        # ATUALIZA PRODUTO
        # ------------------------------------------

        cursor.execute(
            """
            UPDATE produtos
            SET
                nome = %s,
                tamanho = %s,
                preco = %s,
                estoque = %s,
                codigo_barras = %s,
                sku = %s,
                referencia = %s,
                marca = %s,
                categoria = %s,
                unidade = %s,
                ncm = %s,
                cest = %s,
                cfop_padrao = %s,
                custo = %s,
                margem_lucro = %s,
                estoque_minimo = %s,
                localizacao = %s,
                ativo = %s,
                observacoes = %s
            WHERE id = %s
            """,
            (
                nome,
                tamanho,
                preco,
                estoque,
                codigo_barras,
                sku,
                referencia,
                marca,
                categoria,
                unidade,
                ncm,
                cest,
                cfop_padrao,
                custo,
                margem_lucro,
                estoque_minimo,
                localizacao,
                ativo,
                observacoes,
                id_produto
            )
        )

        if cursor.rowcount == 0:

            conn.rollback()

            st.warning(
                "Produto não encontrado para atualização."
            )

            return False

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        st.error(
            f"Erro ao atualizar produto: {erro}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CÓDIGO DE BARRAS
# ==================================================

def atualizar_codigo_barras(
    produto_id,
    codigo_barras
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        if not codigo_barras:

            st.warning(
                "Informe o código de barras."
            )

            return False

        # ------------------------------------------
        # VALIDA CÓDIGO DUPLICADO
        # ------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                nome
            FROM produtos
            WHERE codigo_barras = %s
              AND id <> %s
            LIMIT 1
            """,
            (
                codigo_barras,
                produto_id
            )
        )

        existente = cursor.fetchone()

        if existente:

            st.error(
                f"⚠️ Código já cadastrado no produto: "
                f"{existente[1]}"
            )

            return False

        # ------------------------------------------
        # ATUALIZA CÓDIGO
        # ------------------------------------------

        cursor.execute(
            """
            UPDATE produtos
            SET codigo_barras = %s
            WHERE id = %s
            """,
            (
                codigo_barras,
                produto_id
            )
        )

        if cursor.rowcount == 0:

            conn.rollback()

            st.warning(
                "Produto não encontrado para atualização."
            )

            return False

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        st.error(
            f"Erro ao atualizar código de barras: {erro}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR PRODUTO
# ==================================================

def excluir_produto(produto_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # ------------------------------------------
        # VERIFICA SE POSSUI VENDAS
        # ------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM itens_venda
            WHERE produto_id = %s
            """,
            (produto_id,)
        )

        total_vendas = cursor.fetchone()[0]

        if total_vendas > 0:
            return "possui_vendas"

        # ------------------------------------------
        # EXCLUI PRODUTO
        # ------------------------------------------

        cursor.execute(
            """
            DELETE FROM produtos
            WHERE id = %s
            """,
            (produto_id,)
        )

        if cursor.rowcount == 0:

            conn.rollback()

            return False

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        st.error(
            f"Erro ao excluir produto: {erro}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# BUSCAR PRODUTO POR CÓDIGO DE BARRAS
# ==================================================

def buscar_produto_por_codigo(codigo_barras):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                nome,
                tamanho,
                preco,
                estoque,
                codigo_barras,
                custo,
                unidade,
                ncm
            FROM produtos
            WHERE codigo_barras = %s
            LIMIT 1
            """,
            (codigo_barras,)
        )

        resultado = cursor.fetchone()

        if resultado is None:
            return None

        return {
            "id": resultado[0],
            "nome": resultado[1],
            "tamanho": resultado[2],
            "preco": resultado[3],
            "estoque": resultado[4],
            "codigo_barras": resultado[5],
            "custo": resultado[6],
            "unidade": resultado[7],
            "ncm": resultado[8]
        }

    except Exception as erro:

        st.error(
            f"Erro ao buscar produto por código: {erro}"
        )

        return None

    finally:

        cursor.close()
        conn.close()