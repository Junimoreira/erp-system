import streamlit as st

from database.contas_receber_db import (
    listar_contas,
    excluir_conta_receber,
    receber_conta
)

from database.contas_bancarias import listar_contas as listar_bancos


# ==================================================
# TELA CONTAS A RECEBER
# ==================================================
def tela_contas_receber():

    st.title("📥 Contas a Receber")

    df = listar_contas()
    df_bancos = listar_bancos()

    if df.empty:
        st.info("Nenhuma conta cadastrada.")
        return

    # ==========================================
    # TABELA
    # ==========================================
    st.dataframe(df, use_container_width=True)

    st.divider()

    # ==========================================
    # RECEBER CONTA
    # ==========================================
    st.subheader("💰 Receber Conta")

    df["status"] = df["status"].fillna("").astype(str)

    pendentes = df[df["status"].str.lower() == "pendente"]

    if not pendentes.empty:

        conta_id = st.selectbox(
            "Selecione a conta",
            pendentes["id"].tolist(),
            key="receber_conta"
        )

        conta = pendentes[pendentes["id"] == conta_id].iloc[0]

        st.write("📌", conta["descricao"])
        st.write("💲 R$", float(conta["valor"]))

        # ==========================================
        # ORIGEM FINANCEIRA
        # ==========================================
        origem = st.radio(
            "Receber em:",
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

        if st.button("💰 Receber Conta", use_container_width=True):

            ok = receber_conta(
                conta_id=conta_id,
                origem_financeira=origem,
                conta_bancaria_id=conta_bancaria_id
            )

            if ok:
                st.success("Conta recebida com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao receber conta.")

    else:
        st.info("Nenhuma conta pendente.")

    st.divider()

    # ==========================================
    # EXCLUIR CONTA
    # ==========================================
    st.subheader("🗑️ Excluir Conta")

    conta_excluir = st.selectbox(
        "Selecione a conta para excluir",
        df["id"].tolist(),
        key="excluir_conta_receber"
    )

    if st.button("🗑️ Excluir Conta", use_container_width=True):

        resultado = excluir_conta_receber(conta_excluir)

        if resultado is True:
            st.success("Conta excluída com sucesso!")
            st.rerun()

        elif resultado == "recebido":
            st.warning("Não é permitido excluir contas já recebidas.")

        else:
            st.error("Erro ao excluir conta.")