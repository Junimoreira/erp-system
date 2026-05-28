import streamlit as st
import pandas as pd

from database.contas_pagar_db import (
    listar_contas,
    cadastrar_conta,
    pagar_conta,
    excluir_conta,
    atualizar_conta
)


# ==================================================
# TELA CONTAS A PAGAR
# ==================================================
def tela_contas_pagar():

    st.title("📄 Contas a Pagar")

    # ==========================================
    # LISTAGEM
    # ==========================================
    df = listar_contas()

    if df.empty:
        st.info("Nenhuma conta cadastrada.")
        return

    st.dataframe(df, use_container_width=True)

    st.divider()

    # ==========================================
    # EDITAR CONTA
    # ==========================================
    st.subheader("✏️ Editar Conta")

    if not df.empty:

        conta_edit = st.selectbox(
            "Selecione a conta para editar",
            df["id"].tolist(),
            key="edit_conta"
        )

        conta_info = df[df["id"] == conta_edit].iloc[0]

        with st.form("form_editar_conta"):

            descricao = st.text_input(
                "Descrição",
                value=conta_info["descricao"]
            )

            valor = st.number_input(
                "Valor",
                value=float(conta_info["valor"])
            )

            vencimento = st.date_input(
                "Vencimento",
                value=pd.to_datetime(conta_info["vencimento"])
            )

            categoria = st.text_input(
                "Categoria",
                value=str(conta_info.get("categoria", ""))
            )

            forma_pagamento = st.text_input(
                "Forma de Pagamento",
                value=str(conta_info.get("forma_pagamento", ""))
            )

            observacoes = st.text_area(
                "Observações",
                value=str(conta_info.get("observacoes", ""))
            )

            salvar = st.form_submit_button("Salvar Alterações")

            if salvar:

                ok = atualizar_conta(
                    conta_id=conta_edit,
                    descricao=descricao,
                    valor=valor,
                    vencimento=vencimento,
                    categoria=categoria,
                    forma_pagamento=forma_pagamento,
                    observacoes=observacoes
                )

                if ok:
                    st.success("Conta atualizada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar conta")

    st.divider()

    # ==========================================
    # CADASTRO
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
    # PAGAMENTO
    # ==========================================
    st.subheader("💰 Pagar Conta")

    df["status"] = df["status"].fillna("").astype(str)

    contas_pendentes = df[df["status"].str.lower() == "pendente"]

    if not contas_pendentes.empty:

        conta_id = st.selectbox(
            "Selecione a conta",
            contas_pendentes["id"].tolist(),
            key="pagar_conta"
        )

        conta_info = contas_pendentes[
            contas_pendentes["id"] == conta_id
        ].iloc[0]

        st.write("📌", conta_info["descricao"])
        st.write("💲 Valor:", conta_info["valor"])

        if st.button("Pagar Conta"):

            ok = pagar_conta(conta_id)

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
            key="delete_conta"
        )

        if st.button("Excluir"):

            ok = excluir_conta(conta_del)

            if ok:
                st.success("Conta excluída!")
                st.rerun()
            else:
                st.error("Erro ao excluir conta")