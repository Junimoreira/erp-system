# database/produto_db.py

from database.connection import conectar
import pandas as pd
import streamlit as st


# =====================================
# LISTAR PRODUTOS
# =====================================
def listar_produtos():

    conn = conectar()

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

    df = pd.read_sql(query, conn)
    conn.close()

    return df


# =====================================
# CADASTRAR PRODUTO (COM PROTEÇÃO DUPLICIDADE)
# =====================================
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
    cursor = conn.cursor()

    try:

        # =====================================
        # CHECAGEM ANTES DE INSERIR
        # =====================================
        if codigo_barras:
            cursor.execute("""
                SELECT id FROM produtos
                WHERE codigo_barras = %s
                LIMIT 1
            """, (codigo_barras,))

            if cursor.fetchone():
                st.error("⚠️ Já existe produto com este código de barras.")
                return False

        query = """
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
        """

        cursor.execute(query, (
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

        erro_texto = str(erro)

        if "unique" in erro_texto.lower() and "codigo_barras" in erro_texto:
            st.error("⚠️ Código de barras já cadastrado.")
        else:
            st.error(f"Erro ao cadastrar produto: {erro}")

        return False

    finally:
        cursor.close()
        conn.close()


# =====================================
# ATUALIZAR PRODUTO
# =====================================
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
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE produtos
            SET
                nome=%s,
                preco=%s,
                estoque=%s,
                codigo_barras=%s,
                sku=%s,
                referencia=%s,
                marca=%s,
                categoria=%s,
                unidade=%s,
                ncm=%s,
                cest=%s,
                cfop_padrao=%s,
                custo=%s,
                margem_lucro=%s,
                estoque_minimo=%s,
                localizacao=%s,
                ativo=%s,
                observacoes=%s
            WHERE id=%s
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


# =====================================
# EXCLUIR PRODUTO
# =====================================
def excluir_produto(produto_id):

    conn = conectar()
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


# =====================================
# BUSCAR PRODUTO POR CÓDIGO DE BARRAS
# =====================================
def buscar_produto_por_codigo(codigo_barras):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, preco, estoque, codigo_barras,
               custo, unidade, ncm
        FROM produtos
        WHERE codigo_barras = %s
        LIMIT 1
    """, (codigo_barras,))

    produto = cursor.fetchone()

    cursor.close()
    conn.close()

    return produto