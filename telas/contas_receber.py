import streamlit as st
import pandas as pd
from datetime import datetime

from database.contas_receber_db import (
    listar_contas,
    receber_conta,
    atualizar_conta_receber,
    excluir_conta_receber
)


# ==================================================
# TRATAMENTO
# ==================================================
def tratar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


# ==================================================
# TELA CONTAS A RECEBER
# ==================================================
def tela_contas_receber():

    st.title("💰 Contas a Receber")

    df = listar_contas()

    if df is None or df.empty:
        st.warning("Nenhuma conta cadastrada.")
        return

    df = df.fillna("")

    # ==================================================
    # LISTAGEM
    # ==================================================
    st.subheader("📋 Lista de Contas")

    st.dataframe(df, use_container_width=True, height=300)

    st.divider()

    # ==================================================
    # RECEBER CONTA
    # ==================================================
    st.subheader("💵 Receber Conta")

    contas_pendentes = df[df["status"].str.lower() != "recebido"]

    if contas_pendentes.empty:
        st.info("Nenhuma conta pendente.")
    else:

        conta_id = st.selectbox(
            "Selecione a conta",
            contas_pendentes["id"].tolist(),
            key="receber_id"
        )

        origem = st.selectbox(
            "Origem do recebimento",
            ["CAIXA", "BANCO"],
            key="receber_origem"
        )

        conta_banco = None

        if origem == "BANCO":
            conta_banco = st.number_input(
                "ID Conta Bancária",
                step=1,
                key="receber_banco"
            )

        if st.button("💾 Confirmar Recebimento"):

            sucesso = receber_conta(
                conta_id=conta_id,
                origem_financeira=origem,
                conta_bancaria_id=conta_banco
            )

            if sucesso:
                st.success("Conta recebida com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao receber conta.")

    st.divider()

    # ==================================================
    # EDITAR CONTA
    # ==================================================
    st.subheader("✏️ Editar Conta")

    conta_id = st.selectbox(
        "Selecione a conta para editar",
        df["id"].tolist(),
        key="editar_id"
    )

    conta = df[df["id"] == conta_id].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        nova_descricao = st.text_input(
            "Descrição",
            value=tratar_texto(conta["descricao"])
        )

        novo_valor = st.number_input(
            "Valor",
            value=float(conta["valor"])
        )

    with col2:
        novo_vencimento = st.date_input(
            "Vencimento",
            value=pd.to_datetime(conta["vencimento"]).date()
        )

        novo_status = st.selectbox(
            "Status",
            ["Pendente", "Recebido"],
            index=0 if tratar_texto(conta["status"]).lower() == "pendente" else 1
        )

    # ⚠️ ALERTA VISUAL DE ESTORNO
    status_atual = tratar_texto(conta["status"]).lower()

    if status_atual == "recebido" and novo_status == "Pendente":
        st.warning("⚠️ Essa ação irá ESTORNAR o valor do caixa/banco!")

    if st.button("💾 Atualizar Conta"):

        sucesso = atualizar_conta_receber(
            conta_id=conta_id,
            descricao=nova_descricao,
            valor=float(novo_valor),
            vencimento=novo_vencimento,
            status=novo_status
        )

        if sucesso:
            st.success("Conta atualizada com sucesso!")
            st.rerun()
        else:
            st.error("Erro ao atualizar conta.")

    st.divider()

    # ==================================================
    # EXCLUIR CONTA
    # ==================================================
    st.subheader("🗑️ Excluir Conta")

    conta_excluir = st.selectbox(
        "Selecione a conta para excluir",
        df["id"].tolist(),
        key="excluir_id"
    )

    if st.button("❌ Excluir Conta"):

        resultado = excluir_conta_receber(conta_excluir)

        if resultado is True:
            st.success("Conta excluída com sucesso!")
            st.rerun()

        elif resultado == "recebido":
            st.warning("Não é possível excluir conta já recebida.")

        else:
            st.error("Erro ao excluir conta.")