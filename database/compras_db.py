import pandas as pd
from database.connection import conectar


# ==================================================
# LISTAR COMPRAS
# ==================================================
def listar_compras():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT

                c.id,
                f.razao_social AS fornecedor,
                c.data_compra,
                c.valor_total,
                c.usuario,
                c.status

            FROM compras c

            LEFT JOIN fornecedores f
                ON f.id = c.fornecedor_id

            ORDER BY c.id DESC
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        print("Erro ao listar compras:", erro)

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# BUSCAR COMPRA POR ID
# ==================================================
def buscar_compra_por_id(compra_id):

    conn = conectar()

    if conn is None:
        return None

    try:

        query = """
            SELECT *
            FROM compras
            WHERE id = %s
        """

        df = pd.read_sql(
            query,
            conn,
            params=(int(compra_id),)
        )

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    except Exception as erro:

        print("Erro ao buscar compra:", erro)

        return None

    finally:

        conn.close()


# ==================================================
# BUSCAR ITENS DA COMPRA
# ==================================================
def buscar_itens_compra(compra_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT

                p.nome,
                ic.quantidade,
                ic.custo_unitario,
                ic.subtotal

            FROM itens_compra ic

            LEFT JOIN produtos p
                ON p.id = ic.produto_id

            WHERE ic.compra_id = %s
        """

        df = pd.read_sql(
            query,
            conn,
            params=(int(compra_id),)
        )

        return df

    except Exception as erro:

        print("Erro ao buscar itens:", erro)

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# CADASTRAR COMPRA
# ==================================================
def cadastrar_compra(
    fornecedor_id,
    produtos,
    usuario,
    observacoes=""
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        valor_total = 0

        # ==========================================
        # SOMA TOTAL
        # ==========================================
        for item in produtos:

            subtotal = (
                float(item["quantidade"]) *
                float(item["custo"])
            )

            valor_total += subtotal

        # ==========================================
        # INSERE COMPRA
        # ==========================================
        cursor.execute("""
            INSERT INTO compras (

                fornecedor_id,
                data_compra,
                valor_total,
                observacoes,
                usuario,
                status

            )

            VALUES (

                %s,
                CURRENT_TIMESTAMP,
                %s,
                %s,
                %s,
                'finalizada'

            )

            RETURNING id
        """, (

            int(fornecedor_id),
            float(valor_total),
            observacoes,
            usuario

        ))

        compra_id = cursor.fetchone()[0]

        # ==========================================
        # ITENS + ESTOQUE
        # ==========================================
        for item in produtos:

            produto_id = int(item["produto_id"])

            quantidade = float(item["quantidade"])

            custo = float(item["custo"])

            subtotal = quantidade * custo

            # ======================================
            # ITEM COMPRA
            # ======================================
            cursor.execute("""
                INSERT INTO itens_compra (

                    compra_id,
                    produto_id,
                    quantidade,
                    custo_unitario,
                    subtotal

                )

                VALUES (

                    %s,
                    %s,
                    %s,
                    %s,
                    %s

                )
            """, (

                int(compra_id),
                produto_id,
                quantidade,
                custo,
                subtotal

            ))

            # ======================================
            # ATUALIZA ESTOQUE + CUSTO
            # ======================================
            cursor.execute("""
                UPDATE produtos

                SET

                    estoque = COALESCE(estoque, 0) + %s,
                    custo = %s

                WHERE id = %s
            """, (

                quantidade,
                custo,
                produto_id

            ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao cadastrar compra:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR COMPRA
# ==================================================
def excluir_compra(compra_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # ==========================================
        # REMOVE ITENS
        # ==========================================
        cursor.execute("""
            DELETE FROM itens_compra
            WHERE compra_id = %s
        """, (
            int(compra_id),
        ))

        # ==========================================
        # REMOVE COMPRA
        # ==========================================
        cursor.execute("""
            DELETE FROM compras
            WHERE id = %s
        """, (
            int(compra_id),
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao excluir compra:", erro)

        return False

    finally:

        cursor.close()
        conn.close()