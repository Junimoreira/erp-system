import streamlit as st
import pandas as pd

from database.contas_pagar_db import (
    listar_contas,
    cadastrar_conta,
    pagar_conta,
    excluir_conta,
    atualizar_conta
)

from database.contas_bancarias import listar_contas as listar_bancos


# ==================================================
# TELA CONTAS A PAGAR
# ==================================================
def tela_contas_pagar():

    st.title("📄 Contas a Pagar")

    # ==================================================
    # CARREGA DADOS
    # ==================================================
    df = listar_contas()

    df_bancos = listar_bancos()

    if df.empty:
        st.info("Nenhuma conta cadastrada.")
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()

    # ==================================================
    # EDITAR CONTA
    # ==================================================
    if not df.empty:

        st.subheader("✏️ Editar Conta")

        conta_edit = st.selectbox(
            "Selecione a conta para editar",
            df["id"].tolist(),
            key="edit_conta"
        )

        conta_info = df[df["id"] == conta_edit].iloc[0]

        with st.form("form_editar_conta"):

            descricao = st.text_input(
                "Descrição",
                value=str(conta_info["descricao"])
            )

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                value=float(conta_info["valor"])
            )

            vencimento = st.date_input(
                "Vencimento",
                value=pd.to_datetime(conta_info["vencimento"]).date()
            )

            categoria = st.text_input(
                "Categoria",
                value=str(conta_info.get("categoria", ""))
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
                    forma_pagamento=None,
                    observacoes=observacoes
                )

                if ok:
                    st.success("Conta atualizada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar conta.")

        st.divider()

    # ==================================================
    # NOVA CONTA
    # ==================================================
    st.subheader("➕ Nova Conta")

    with st.form("form_conta"):

        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor", min_value=0.0, step=1.0)
        categoria = st.text_input("Categoria")
        vencimento = st.date_input("Vencimento")
        observacoes = st.text_area("Observações")

        salvar = st.form_submit_button("Salvar")

        if salvar:

            ok = cadastrar_conta(
                descricao=descricao,
                valor=valor,
                vencimento=vencimento,
                categoria=categoria,
                forma_pagamento=None,
                observacoes=observacoes
            )

            if ok:
                st.success("Conta cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao cadastrar conta.")

    st.divider()

    # ==================================================
    # PAGAR CONTA
    # ==================================================
    st.subheader("💰 Pagar Conta")

    if not df.empty:

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
            st.write("💲 Valor:", f"R$ {float(conta_info['valor']):,.2f}")

            # ==========================================
            # NOVA REGRA: ORIGEM FINANCEIRA
            # ==========================================
            origem = st.radio(
                "Origem do pagamento",
                ["CAIXA", "BANCO"]
            )

            conta_bancaria_id = None

            if origem == "BANCO":

                if df_bancos.empty:
                    st.error("Nenhuma conta bancária cadastrada.")
                else:

                    conta_bancaria_id = st.selectbox(
                        "Selecione a conta bancária",
                        df_bancos["id"].tolist(),
                        format_func=lambda x:
                            df_bancos[df_bancos["id"] == x]["banco"].values[0]
                    )

            if st.button("Pagar Conta", key="btn_pagar"):

                ok = pagar_conta(
                    conta_id=conta_id,
                    origem_financeira=origem,
                    conta_bancaria_id=conta_bancaria_id
                )

                if ok:
                    st.success("Conta paga com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao processar pagamento.")

        else:
            st.info("Não há contas pendentes.")

    st.divider()

    # ==================================================
    # EXCLUIR CONTA
    # ==================================================
    if not df.empty:

        st.subheader("🗑️ Excluir Conta")

        conta_del = st.selectbox(
            "Selecione a conta para excluir",
            df["id"].tolist(),
            key="delete_conta"
        )

        if st.button("Excluir Conta", key="btn_excluir"):

            ok = excluir_conta(conta_del)

            if ok:
                st.success("Conta excluída com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao excluir conta.")