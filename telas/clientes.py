import streamlit as st
import pandas as pd

from database.connection import conectar


def tela_clientes():

    #st.title("👥 Clientes")

    abas = st.tabs([
    "➕ Novo Cliente",
    "📋 Clientes",
    "✏️ Editar Cliente"
    ])

    # ==========================================
    # NOVO CLIENTE
    # ==========================================

    with abas[0]:

        st.subheader("Cadastrar Cliente")

        with st.form(
            "form_cliente",
            clear_on_submit=True
        ):

            nome = st.text_input("Nome")

            telefone = st.text_input("Telefone")

            email = st.text_input("E-mail")

            salvar = st.form_submit_button(
                "Salvar Cliente"
            )

            if salvar:

                # ==========================================
                # VALIDAÇÃO
                # ==========================================

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

            df = pd.read_sql(
                query,
                conn
            )

            conn.close()

            st.dataframe(
                df,
                use_container_width=True
            )

        except Exception as e:

            st.error(f"Erro: {e}")

# ==================================================
# EDITAR CLIENTE
# ==================================================

with abas[2]:

    st.subheader("Editar Cliente")

    df_clientes = listar_clientes()

    if df_clientes.empty:

        st.warning(
            "Nenhum cliente cadastrado."
        )

    else:

        cliente_nome = st.selectbox(
            "Selecione o Cliente",
            df_clientes["nome"]
        )

        cliente = df_clientes[
            df_clientes["nome"] == cliente_nome
        ].iloc[0]

        nome = st.text_input(
            "Nome",
            value=cliente["nome"]
        )

        telefone = st.text_input(
            "Telefone",
            value=cliente["telefone"]
        )

        email = st.text_input(
            "Email",
            value=cliente["email"]
        )

        cidade = st.text_input(
            "Cidade",
            value=cliente["cidade"]
        )

        if st.button("Salvar Alterações"):

            atualizar_cliente(
                cliente["id"],
                nome,
                telefone,
                email,
                cidade
            )

            st.success(
                "✅ Cliente atualizado!"
            )

            st.rerun()