import streamlit as st
import pandas as pd

from database.contas_receber_db import (
    listar_contas,
    cadastrar_conta,
    receber_conta,
    excluir_conta,
    atualizar_conta
)

from database.contas_bancarias import listar_contas as listar_bancos


def tela_contas_receber():

    st.title("📥 Contas a Receber")

    df = listar_contas()
    df_bancos = listar_bancos()

    if df.empty:
        st.info("Nenhuma conta a receber cadastrada.")
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()

    st.subheader("➕ Cadastrar Conta a Receber")

    with st.form("form_cadastrar_conta_receber"):

        cliente = st.text_input("Cliente")
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0, step=0.01)
        vencimento = st.date_input("Vencimento")

        forma_pagamento = st.selectbox(
            "Forma de pagamento",
            [
                "DINHEIRO",
                "PIX",
                "CARTÃO DÉBITO",
                "CARTÃO CRÉDITO",
                "BOLETO",
                "TRANSFERÊNCIA",
                "OUTROS"
            ]
        )

        observacoes = st.text_area("Observações")

        enviar = st.form_submit_button("Cadastrar")

        if enviar:
            if not descricao or valor <= 0:
                st.warning("Informe descrição e valor válido.")
            else:
                sucesso = cadastrar_conta(
                    descricao=descricao,
                    valor=valor,
                    vencimento=vencimento,
                    cliente=cliente,
                    observacoes=observacoes,
                    forma_pagamento=forma_pagamento
                )

                if sucesso:
                    st.success("Conta cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao cadastrar conta.")

    st.divider()

    if not df.empty:

        st.subheader("✏️ Editar Conta")

        conta_edit = st.selectbox(
            "Selecione a conta para editar",
            df["id"].tolist(),
            key="edit_conta_receber"
        )

        conta_info = df[df["id"] == conta_edit].iloc[0]

        with st.form("form_editar_conta_receber"):

            novo_cliente = st.text_input(
                "Cliente",
                value=str(conta_info.get("cliente", ""))
            )

            nova_descricao = st.text_input(
                "Descrição",
                value=str(conta_info.get("descricao", ""))
            )

            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=0.01,
                value=float(conta_info.get("valor", 0))
            )

            novo_vencimento = st.date_input(
                "Vencimento",
                value=pd.to_datetime(conta_info.get("vencimento")).date()
            )

            novo_status = st.selectbox(
                "Status",
                ["PENDENTE", "RECEBIDO"],
                index=0 if conta_info.get("status", "PENDENTE") != "RECEBIDO" else 1
            )

            nova_forma_pagamento = st.selectbox(
                "Forma de pagamento",
                [
                    "DINHEIRO",
                    "PIX",
                    "CARTÃO DÉBITO",
                    "CARTÃO CRÉDITO",
                    "BOLETO",
                    "TRANSFERÊNCIA",
                    "OUTROS"
                ]
            )

            novas_observacoes = st.text_area(
                "Observações",
                value=str(conta_info.get("observacoes", ""))
            )

            salvar_edicao = st.form_submit_button("Salvar Alterações")

            if salvar_edicao:
                sucesso = atualizar_conta(
                    conta_id=conta_edit,
                    descricao=nova_descricao,
                    valor=novo_valor,
                    vencimento=novo_vencimento,
                    cliente=novo_cliente,
                    status=novo_status,
                    observacoes=novas_observacoes,
                    forma_pagamento=nova_forma_pagamento
                )

                if sucesso:
                    st.success("Conta atualizada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar conta.")

    st.divider()

    if not df.empty:

        st.subheader("💰 Receber Conta")

        contas_pendentes = df[df["status"] != "RECEBIDO"]

        if contas_pendentes.empty:
            st.info("Nenhuma conta pendente para receber.")
        else:
            conta_receber_id = st.selectbox(
                "Selecione a conta para receber",
                contas_pendentes["id"].tolist(),
                key="receber_conta"
            )

            origem_financeira = st.selectbox(
                "Origem do Recebimento",
                [
                    "CAIXA",
                    "BANCO",
                    "PIX",
                    "DINHEIRO",
                    "CARTÃO",
                    "BOLETO",
                    "TRANSFERÊNCIA"
                ]
            )

            conta_bancaria_id = None
            caixa_id = None

            if origem_financeira == "BANCO":
                if df_bancos.empty:
                    st.warning("Nenhuma conta bancária cadastrada.")
                else:
                    conta_bancaria_id = st.selectbox(
                        "Conta Bancária",
                        df_bancos["id"].tolist(),
                        key="conta_bancaria_receber"
                    )

            if st.button("Confirmar Recebimento"):
                sucesso = receber_conta(
                    conta_id=conta_receber_id,
                    origem_financeira=origem_financeira,
                    conta_bancaria_id=conta_bancaria_id,
                    caixa_id=caixa_id
                )

                if sucesso:
                    st.success("Conta recebida com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao receber conta.")

    st.divider()

    if not df.empty:

        st.subheader("🗑️ Excluir Conta")

        conta_excluir = st.selectbox(
            "Selecione a conta para excluir",
            df["id"].tolist(),
            key="excluir_conta_receber"
        )

        if st.button("Excluir Conta"):
            sucesso = excluir_conta(conta_excluir)

            if sucesso:
                st.success("Conta excluída com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao excluir conta.")