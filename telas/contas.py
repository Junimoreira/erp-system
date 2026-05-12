import streamlit as st
from database.contas_db import (
    listar_contas,
    cadastrar_conta,
    atualizar_conta,
    excluir_conta
)


def tela_contas():

    abas = st.tabs([
        "🏦 Contas Bancárias",
        "➕ Nova Conta",
        "✏️ Editar Conta",
        "🗑️ Excluir Conta"
    ])

    # ==================================================
    # LISTAR CONTAS
    # ==================================================

    with abas[0]:

        st.subheader("🏦 Contas Bancárias")

        df = listar_contas()

        if df.empty:

            st.info("Nenhuma conta cadastrada.")

        else:

            total = df["saldo"].sum()

            col1, col2 = st.columns(2)

            col1.metric(
                "💰 Saldo Total",
                f"R$ {total:,.2f}"
            )

            col2.metric(
                "🏦 Total de Contas",
                len(df)
            )

            st.dataframe(
                df,
                use_container_width=True
            )

    # ==================================================
    # NOVA CONTA
    # ==================================================

    with abas[1]:

        st.subheader("➕ Nova Conta")

        with st.form("form_conta"):

            banco = st.text_input("Banco")

            agencia = st.text_input("Agência")

            conta = st.text_input("Conta")

            tipo_conta = st.selectbox(
                "Tipo da Conta",
                [
                    "Corrente",
                    "Poupança",
                    "Carteira",
                    "Caixa"
                ]
            )

            saldo = st.number_input(
                "Saldo Inicial",
                min_value=0.0,
                format="%.2f"
            )

            salvar = st.form_submit_button(
                "💾 Salvar Conta"
            )

            if salvar:

                cadastrar_conta(
                    banco,
                    agencia,
                    conta,
                    tipo_conta,
                    saldo
                )

                st.success(
                    "Conta cadastrada com sucesso!"
                )

                st.rerun()

    # ==================================================
    # EDITAR CONTA
    # ==================================================

    with abas[2]:

        st.subheader("✏️ Editar Conta")

        df = listar_contas()

        if df.empty:

            st.info("Nenhuma conta cadastrada.")

        else:

            contas = {
                f"{row['id']} - {row['banco']}": row
                for _, row in df.iterrows()
            }

            conta_selecionada = st.selectbox(
               "Selecione a conta",
               list(contas.keys()),
               key="editar_conta"
            )

            conta = contas[conta_selecionada]

            with st.form("form_editar_conta"):

                banco = st.text_input(
                    "Banco",
                    value=conta["banco"]
                )

                agencia = st.text_input(
                    "Agência",
                    value=conta["agencia"]
                )

                numero_conta = st.text_input(
                    "Conta",
                    value=conta["conta"]
                )

                tipo_conta = st.selectbox(
                    "Tipo da Conta",
                    [
                        "Corrente",
                        "Poupança",
                        "Carteira",
                        "Caixa"
                    ]
                )

                saldo = st.number_input(
                    "Saldo",
                    value=float(conta["saldo"]),
                    format="%.2f"
                )

                atualizar = st.form_submit_button(
                    "💾 Atualizar Conta"
                )

                if atualizar:

                    atualizar_conta(
                        conta["id"],
                        banco,
                        agencia,
                        numero_conta,
                        tipo_conta,
                        saldo
                    )

                    st.success(
                        "Conta atualizada com sucesso!"
                    )

                    st.rerun()

    # ==================================================
    # EXCLUIR CONTA
    # ==================================================

    with abas[3]:

        st.subheader("🗑️ Excluir Conta")

        df = listar_contas()

        if df.empty:

            st.info("Nenhuma conta cadastrada.")

        else:

            contas = {
                f"{row['id']} - {row['banco']}": row
                for _, row in df.iterrows()
            }

            conta_selecionada = st.selectbox(
                "Selecione a conta",
                list(contas.keys()),
                key="excluir_conta"
            )

            conta = contas[conta_selecionada]

            st.warning(
                f"Deseja excluir a conta do banco {conta['banco']}?"
            )

            if st.button("🗑️ Excluir Conta"):

                excluir_conta(conta["id"])

                st.success(
                    "Conta excluída com sucesso!"
                )

                st.rerun()