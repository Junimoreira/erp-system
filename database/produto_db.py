# database/produto_db.py

from database.connection import conectar
import pandas as pd
import streamlit as st


def listar_produtos():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                id,
                nome,
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


def listar_produtos_sem_codigo():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                id,
                nome,
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
        st.error(f"Erro ao listar produtos sem código: {erro}")
        return pd.DataFrame()

    finally:
        conn.close()


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
    observacoes
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        if codigo_barras:
            cursor.execute("""
                SELECT id
                FROM produtos
                WHERE codigo_barras = %s
                LIMIT 1
            """, (codigo_barras,))

            if cursor.fetchone():
                st.error("⚠️ Já existe produto com este código de barras.")
                return False

        cursor.execute("""
            INSERT INTO produtos (
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
                observacoes
            )
            VALUES (
                %s,%s,%s,%s,
                %s,%s,%s,%s,
                %s,%s,%s,%s,
                %s,%s,
                %s,%s,
                %s,%s
            )
        """, (
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
            observacoes
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        st.error(f"Erro ao cadastrar produto: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()


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
    observacoes
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        if codigo_barras:
            cursor.execute("""
                SELECT id
                FROM produtos
                WHERE codigo_barras = %s
                  AND id <> %s
                LIMIT 1
            """, (codigo_barras, id_produto))

            if cursor.fetchone():
                st.error("⚠️ Este código de barras já pertence a outro produto.")
                return False

        cursor.execute("""
            UPDATE produtos
            SET
                nome = %s,
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
        """, (
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
            id_produto
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        st.error(f"Erro ao atualizar produto: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()


def atualizar_codigo_barras(produto_id, codigo_barras):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        if not codigo_barras:
            st.warning("Informe o código de barras.")
            return False

        cursor.execute("""
            SELECT id, nome
            FROM produtos
            WHERE codigo_barras = %s
              AND id <> %s
            LIMIT 1
        """, (codigo_barras, produto_id))

        existente = cursor.fetchone()

        if existente:
            st.error(
                f"⚠️ Código já cadastrado no produto: {existente[1]}"
            )
            return False

        cursor.execute("""
            UPDATE produtos
            SET codigo_barras = %s
            WHERE id = %s
        """, (codigo_barras, produto_id))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        st.error(f"Erro ao atualizar código de barras: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()


def excluir_produto(produto_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM itens_venda
            WHERE produto_id = %s
        """, (produto_id,))

        total_vendas = cursor.fetchone()[0]

        if total_vendas > 0:
            return "possui_vendas"

        cursor.execute("""
            DELETE FROM produtos
            WHERE id = %s
        """, (produto_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        st.error(f"Erro ao excluir produto: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()


def buscar_produto_por_codigo(codigo_barras):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                id,
                nome,
                preco,
                estoque,
                codigo_barras,
                custo,
                unidade,
                ncm
            FROM produtos
            WHERE codigo_barras = %s
            LIMIT 1
        """, (codigo_barras,))

        return cursor.fetchone()

    except Exception as erro:
        st.error(f"Erro ao buscar produto por código: {erro}")
        return None

    finally:
        cursor.close()
        conn.close()