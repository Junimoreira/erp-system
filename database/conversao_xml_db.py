import pandas as pd

from database.connection import conectar


def listar_conversoes_xml():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:
        query = """
            SELECT
                c.id,
                p.nome AS produto,
                c.produto_id,
                c.codigo_barras,
                c.codigo_fornecedor,
                c.tipo_compra,
                c.unidade_compra,
                c.unidade_estoque,
                c.fator_conversao,
                c.ativo,
                c.observacoes,
                c.atualizado_em
            FROM conversao_produtos_xml c
            LEFT JOIN produtos p
                ON p.id = c.produto_id
            ORDER BY c.id DESC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        print("Erro listar_conversoes_xml:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


def cadastrar_conversao_xml(
    produto_id,
    codigo_barras,
    codigo_fornecedor,
    tipo_compra,
    unidade_compra,
    unidade_estoque,
    fator_conversao,
    ativo=True,
    observacoes=""
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO conversao_produtos_xml (
                produto_id,
                codigo_barras,
                codigo_fornecedor,
                tipo_compra,
                unidade_compra,
                unidade_estoque,
                fator_conversao,
                ativo,
                observacoes,
                atualizado_em
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            int(produto_id),
            codigo_barras,
            codigo_fornecedor,
            tipo_compra,
            unidade_compra,
            unidade_estoque,
            float(fator_conversao),
            bool(ativo),
            observacoes
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro cadastrar_conversao_xml:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


def atualizar_conversao_xml(
    conversao_id,
    produto_id,
    codigo_barras,
    codigo_fornecedor,
    tipo_compra,
    unidade_compra,
    unidade_estoque,
    fator_conversao,
    ativo=True,
    observacoes=""
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE conversao_produtos_xml
            SET
                produto_id = %s,
                codigo_barras = %s,
                codigo_fornecedor = %s,
                tipo_compra = %s,
                unidade_compra = %s,
                unidade_estoque = %s,
                fator_conversao = %s,
                ativo = %s,
                observacoes = %s,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            int(produto_id),
            codigo_barras,
            codigo_fornecedor,
            tipo_compra,
            unidade_compra,
            unidade_estoque,
            float(fator_conversao),
            bool(ativo),
            observacoes,
            int(conversao_id)
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro atualizar_conversao_xml:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


def excluir_conversao_xml(conversao_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM conversao_produtos_xml
            WHERE id = %s
        """, (
            int(conversao_id),
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro excluir_conversao_xml:", erro)
        return False

    finally:
        cursor.close()
        conn.close()