import streamlit as st
import pandas as pd

from database.contas_pagar_db import listar_contas, excluir_conta
from services.finance_service import processar_saida_financeira


def tela_contas_pagar():

    st.title("📄 Contas a Pagar")

    # ==========================================
    # LISTAGEM
    # ==========================================
    df = listar_contas()

    if df.empty:
        st.info("Nenhuma conta cadastrada.")
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()

    # ==========================================
    # CADASTRO SIMPLES (EXEMPLO)
    # ==========================================
    st.subheader("➕ Nova Conta")

    with st.form("form_conta"):

        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0, step=1.0)
        categoria = st.text_input("Categoria")
        vencimento = st.date_input("Vencimento")
        forma_pagamento = st.text_input("Forma de pagamento")
        observacoes = st.text_area("Observações")

        submit = st.form_submit_button("Salvar")

        if submit:

            from database.contas_pagar_db import cadastrar_conta

            ok = cadastrar_conta(
                descricao=descricao,
                valor=valor,
                vencimento=vencimento,
                categoria=categoria,
                forma_pagamento=forma_pagamento,
                observacoes=observacoes
            )

            if ok:
                st.success("Conta cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao cadastrar conta")

    st.divider()

    # ==========================================
    # PAGAMENTO DE CONTA
    # ==========================================
    st.subheader("💰 Pagar Conta")

    contas = df[df["status"].str.lower() == "pendente"]

    if not contas.empty:

        conta_selecionada = st.selectbox(
            "Selecione a conta",
            contas["id"].tolist()
        )

        conta_info = contas[contas["id"] == conta_selecionada].iloc[0]

        st.write("📌", conta_info["descricao"])
        st.write("💲 Valor:", conta_info["valor"])

        if st.button("Pagar Conta"):

            ok = processar_saida_financeira(
                valor=conta_info["valor"],
                descricao=conta_info["descricao"],
                categoria=conta_info["categoria"],
                origem="contas_pagar",
                referencia_id=conta_info["id"]
            )

            if ok:
                st.success("Conta paga com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao processar pagamento")

    else:
        st.info("Não há contas pendentes.")

    st.divider()

    # ==========================================
    # EXCLUSÃO
    # ==========================================
    st.subheader("🗑️ Excluir Conta")

    if not df.empty:

        conta_del = st.selectbox(
            "Selecione para excluir",
            df["id"].tolist(),
            key="del"
        )

        if st.button("Excluir"):

            ok = excluir_conta(conta_del)

            if ok:
                st.success("Conta excluída!")
                st.rerun()
            else:
                st.error("Erro ao excluir")