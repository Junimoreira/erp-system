import streamlit as st
import pandas as pd
from datetime import date

from database.clientes_db import (
    listar_clientes,
    cadastrar_cliente,
    atualizar_cliente,
    excluir_cliente
)

from utils.formatacao import formatar_dataframe_brasil


DATA_MINIMA = date(1900, 1, 1)
DATA_MAXIMA = date.today()
DATA_PADRAO = date(2000, 1, 1)


def tela_clientes():

    abas = st.tabs([
        "📋 Listar Clientes",
        "➕ Novo Cliente",
        "✏️ Editar Cliente",
        "🗑️ Excluir Cliente"
    ])

    with abas[0]:

        st.subheader("📋 Clientes Cadastrados")

        df = listar_clientes()

        if df.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            df_exibicao = formatar_dataframe_brasil(
                df,
                com_hora=False,
                moedas=False
            )

            st.dataframe(df_exibicao, use_container_width=True)

    with abas[1]:

        st.subheader("➕ Cadastrar Cliente")

        with st.form("form_cliente"):

            nome = st.text_input("Nome")
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")
            cidade = st.text_input("Cidade", key="cidade_novo_cliente")

            informar_aniversario = st.checkbox(
                "Informar data de nascimento/aniversário"
            )

            data_nascimento = None

            if informar_aniversario:
                data_nascimento = st.date_input(
                    "Data de nascimento",
                    value=DATA_PADRAO,
                    min_value=DATA_MINIMA,
                    max_value=DATA_MAXIMA,
                    format="DD/MM/YYYY"
                )

            salvar = st.form_submit_button("💾 Salvar Cliente")

            if salvar:

                if nome.strip() == "":
                    st.warning("Informe o nome.")
                else:
                    sucesso = cadastrar_cliente(
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        cidade=cidade,
                        data_nascimento=data_nascimento
                    )

                    if sucesso:
                        st.success("Cliente cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar cliente.")

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
                    value=str(cliente.get("nome", ""))
                )

                telefone = st.text_input(
                    "Telefone",
                    value=str(cliente.get("telefone", ""))
                )

                email = st.text_input(
                    "Email",
                    value=str(cliente.get("email", ""))
                )

                cidade = st.text_input(
                    "Cidade",
                    value=str(cliente.get("cidade", "")),
                    key="cidade_editar_cliente"
                )

                data_atual = cliente.get("data_nascimento", None)

                if pd.isna(data_atual) or data_atual in ["", None]:

                    informar_aniversario = st.checkbox(
                        "Informar data de nascimento/aniversário",
                        value=False,
                        key="editar_informar_aniversario"
                    )

                    data_nascimento = None

                    if informar_aniversario:
                        data_nascimento = st.date_input(
                            "Data de nascimento",
                            value=DATA_PADRAO,
                            min_value=DATA_MINIMA,
                            max_value=DATA_MAXIMA,
                            format="DD/MM/YYYY",
                            key="editar_data_nascimento"
                        )

                else:

                    data_nascimento = pd.to_datetime(data_atual).date()

                    if data_nascimento < DATA_MINIMA:
                        data_nascimento = DATA_MINIMA

                    if data_nascimento > DATA_MAXIMA:
                        data_nascimento = DATA_MAXIMA

                    data_nascimento = st.date_input(
                        "Data de nascimento",
                        value=data_nascimento,
                        min_value=DATA_MINIMA,
                        max_value=DATA_MAXIMA,
                        format="DD/MM/YYYY",
                        key="editar_data_nascimento"
                    )

                atualizar = st.form_submit_button("💾 Atualizar Cliente")

                if atualizar:

                    sucesso = atualizar_cliente(
                        cliente_id=cliente.get("id"),
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        cidade=cidade,
                        data_nascimento=data_nascimento
                    )

                    if sucesso:
                        st.success("Cliente atualizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar cliente.")

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

            confirmar = st.checkbox(
                "Confirmo que desejo excluir este cliente"
            )

            if st.button("🗑️ Excluir Cliente"):

                if not confirmar:
                    st.warning("Marque a confirmação antes de excluir.")
                    return

                resultado = excluir_cliente(cliente.get("id"))

                if resultado is True:
                    st.success("Cliente excluído com sucesso!")
                    st.rerun()

                elif resultado == "possui_vendas":
                    st.error(
                        "Não é possível excluir cliente com vendas vinculadas."
                    )

                else:
                    st.error("Erro ao excluir cliente.")