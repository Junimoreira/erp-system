import streamlit as st
from database.contas_receber_db import listar_contas, excluir_conta
from services.finance_service import processar_entrada_financeira


def tela_contas_receber():

    st.title("📥 Contas a Receber")

    df = listar_contas()

    if df.empty:
        st.info("Nenhuma conta cadastrada.")
        return

    st.dataframe(df, use_container_width=True)

    st.divider()

    # ==========================================
    # RECEBIMENTO
    # ==========================================
    st.subheader("💰 Receber Conta")

    pendentes = df[df["status"].str.lower() == "pendente"]

    if not pendentes.empty:

        conta_id = st.selectbox(
            "Selecione a conta",
            pendentes["id"].tolist()
        )

        conta = pendentes[pendentes["id"] == conta_id].iloc[0]

        st.write("📌", conta["descricao"])
        st.write("💲", conta["valor"])

        if st.button("Receber"):

            ok = processar_entrada_financeira(
                valor=conta["valor"],
                descricao=conta["descricao"],
                categoria=conta["categoria"],
                origem="contas_receber",
                referencia_id=conta["id"]
            )

            if ok:
                st.success("Conta recebida com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao processar recebimento")

    else:
        st.info("Nenhuma conta pendente.")