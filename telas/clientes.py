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

        # ==========================================
        # CONTROLE DOS CAMPOS
        # ==========================================

        if "cliente_nome" not in st.session_state:
           st.session_state["cliente_nome"] = ""

        if "cliente_telefone" not in st.session_state:
           st.session_state["cliente_telefone"] = ""

        if "cliente_email" not in st.session_state:
           st.session_state["cliente_email"] = ""

        # ==========================================
        # CAMPOS
        # ==========================================

        nome = st.text_input(
          "Nome",
          key="cliente_nome"
        )

        telefone = st.text_input(
          "Telefone",
        key="cliente_telefone"
        )

       email = st.text_input(
         "E-mail",
         key="cliente_email"
       )

# ==========================================
# BOTÃO
# ==========================================

       if st.button("Salvar Cliente"):

           # VALIDAÇÃO

           if not nome:

             st.warning("Informe o nome.")
             st.stop()

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

        # LIMPAR CAMPOS

        st.session_state["cliente_nome"] = ""
        st.session_state["cliente_telefone"] = ""
        st.session_state["cliente_email"] = ""

        st.rerun()

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