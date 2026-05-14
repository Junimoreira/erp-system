import streamlit as st
from database.clientes_db import (
    listar_clientes,
    cadastrar_cliente,
    atualizar_cliente,
    excluir_cliente
)


def tela_clientes():

    abas = st.tabs([
        "📋 Listar Clientes",
        "➕ Novo Cliente",
        "✏️ Editar Cliente",
        "🗑️ Excluir Cliente"
    ])

    # ==================================================
    # LISTAR CLIENTES
    # ==================================================

    with abas[0]:

        st.subheader("📋 Clientes Cadastrados")

        df = listar_clientes()

        if df.empty:

            st.info("Nenhum cliente cadastrado.")

        else:

            st.dataframe(
                df,
                use_container_width=True
            )

    # ==================================================
    # NOVO CLIENTE
    # ==================================================

    with abas[1]:

        st.subheader("➕ Cadastrar Cliente")

        with st.form("form_cliente"):

           nome = st.text_input(
               "Nome"
           )

           telefone = st.text_input(
               "Telefone"
           )

           email = st.text_input(
               "Email"
           )

           cidade = st.text_input(
               "Cidade",
               key="cidade_novo_cliente"
           )
            

            salvar = st.form_submit_button(
                "💾 Salvar Cliente"
            )

            if salvar:

                if nome == "":

                    st.warning("Informe o nome.")

                else:

                    cadastrar_cliente(
                        nome,
                        telefone,
                        email,
                        cidade
                    )

                    st.success(
                        "Cliente cadastrado com sucesso!"
                    )

                    st.rerun()

    # ==================================================
    # EDITAR CLIENTE
    # ==================================================

    with abas[2]:

        st.subheader("✏️ Editar Cliente")

        df = listar_clientes()

        if df.empty:

            st.info("Nenhum cliente cadastrado.")

        else:

            clientes = {
                f"{row.get('id')} - {row.get('nome')}": row
                for _, row in df.iterrows()
            }

            cliente_selecionado = st.selectbox(
                "Selecione o cliente",
                list(clientes.keys())
            )

            cliente = clientes[cliente_selecionado]

            with st.form("form_editar_cliente"):

                nome = st.text_input(
                    "Nome",
                    value=cliente.get("nome", "")
                )

                telefone = st.text_input(
                    "Telefone",
                    value=cliente.get("telefone", "")
                )

                email = st.text_input(
                    "Email",
                    value=cliente.get("email", "")
                )

                cidade = ""

                if "cidade" in df.columns:

                    cidade = st.text_input(
                        "Cidade",
                        value=cliente.get("cidade", ""),
                        key="cidade_editar_cliente"
                    )

                atualizar = st.form_submit_button(
                    "💾 Atualizar Cliente"
                )

                if atualizar:

                    atualizar_cliente(
                        cliente.get("id"),
                        nome,
                        telefone,
                        email,
                        cidade
                    )

                    st.success(
                        "Cliente atualizado com sucesso!"
                    )

                    st.rerun()

    # ==================================================
    # EXCLUIR CLIENTE
    # ==================================================

    with abas[3]:

        st.subheader("🗑️ Excluir Cliente")

        df = listar_clientes()

        if df.empty:

            st.info("Nenhum cliente cadastrado.")

        else:

            clientes = {
                f"{row.get('id')} - {row.get('nome')}": row
                for _, row in df.iterrows()
            }

            cliente_selecionado = st.selectbox(
                "Selecione o cliente para excluir",
                list(clientes.keys())
            )

            cliente = clientes[cliente_selecionado]

            st.warning(
                f"Tem certeza que deseja excluir o cliente: {cliente.get('nome')}?"
            )

            if st.button("🗑️ Excluir Cliente"):

                try:

                    excluir_cliente(cliente.get("id"))

                    st.success(
                        "Cliente excluído com sucesso!"
                    )

                    st.rerun()

                except Exception:

                    st.error(
                        "Não é possível excluir este cliente porque ele possui vendas vinculadas."
                    )