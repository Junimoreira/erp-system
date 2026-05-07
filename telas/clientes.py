import streamlit as st
import pandas as pd

from database.connection import conectar


def tela_clientes():

    st.title("👥 Clientes")

    abas = st.tabs([
        "➕ Novo Cliente",
        "📋 Listar Clientes"
    ])

    # ==========================================
    # NOVO CLIENTE
    # ==========================================

    with abas[0]:

        st.subheader("Cadastrar Cliente")

        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")

        if st.button("Salvar Cliente"):

            try:

                conn = conectar()
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO clientes
                    (nome, telefone, email)

                    VALUES (%s, %s, %s)
                """, (nome, telefone, email))

                conn.commit()

                cur.close()
                conn.close()

                st.success("✅ Cliente cadastrado!")

            except Exception as e:
                st.error(f"Erro: {e}")

    # ==========================================
    # LISTAR CLIENTES
    # ==========================================

    with abas[1]:

        st.subheader("Clientes Cadastrados")

        try:

            conn = conectar()

            query = """
                SELECT
                    id,
                    nome,
                    telefone,
                    email,
                    criado_em
                FROM clientes
                ORDER BY id DESC
            """

            df = pd.read_sql(query, conn)

            conn.close()

            st.dataframe(
                df,
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Erro: {e}")