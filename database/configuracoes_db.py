import pandas as pd
from database.connection import conectar


# ==================================================
# BUSCAR CONFIGURAÇÕES FINANCEIRAS
# ==================================================
def buscar_configuracoes_financeiras():

    conn = conectar()

    try:

        query = """
            SELECT *
            FROM configuracoes_financeiras
            ORDER BY id DESC
            LIMIT 1
        """

        df = pd.read_sql(query, conn)

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    except Exception as erro:
        print("ERRO AO BUSCAR CONFIGURAÇÕES:", erro)
        return None

    finally:
        conn.close()


# ==================================================
# SALVAR CONFIGURAÇÕES FINANCEIRAS (POSTGRES + SQLITE COMPATÍVEL)
# ==================================================
def salvar_configuracoes_financeiras(
    imposto,
    frete,
    taxa_cartao,
    margem,
    desconto_maximo=0.0
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==================================================
        # VERIFICA SE JÁ EXISTE REGISTRO
        # ==================================================
        cursor.execute("""
            SELECT id
            FROM configuracoes_financeiras
            ORDER BY id DESC
            LIMIT 1
        """)

        resultado = cursor.fetchone()

        # ==================================================
        # DEFINE PLACEHOLDER AUTOMATICAMENTE
        # ==================================================
        # detecta tipo de banco pelo driver
        placeholder = "%s"
        if "sqlite" in str(type(conn)).lower():
            placeholder = "?"

        # ==================================================
        # INSERT
        # ==================================================
        if resultado is None:

            query = f"""
                INSERT INTO configuracoes_financeiras (
                    imposto_padrao,
                    frete_padrao,
                    taxa_cartao_padrao,
                    margem_lucro_padrao,
                    desconto_maximo
                )
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """

            cursor.execute(query, (
                imposto,
                frete,
                taxa_cartao,
                margem,
                desconto_maximo
            ))

        # ==================================================
        # UPDATE
        # ==================================================
        else:

            query = f"""
                UPDATE configuracoes_financeiras
                SET
                    imposto_padrao = {placeholder},
                    frete_padrao = {placeholder},
                    taxa_cartao_padrao = {placeholder},
                    margem_lucro_padrao = {placeholder},
                    desconto_maximo = {placeholder}
                WHERE id = {placeholder}
            """

            cursor.execute(query, (
                imposto,
                frete,
                taxa_cartao,
                margem,
                desconto_maximo,
                resultado[0]
            ))

        conn.commit()
        return True

    except Exception as erro:

        conn.rollback()

        print("ERRO CONFIGURAÇÕES FINANCEIRAS:", erro)

        # mostra no Streamlit se estiver rodando lá
        try:
            import streamlit as st
            st.error(f"Erro ao salvar configurações: {erro}")
        except:
            pass

        return False

    finally:
        cursor.close()
        conn.close()