# telas/caixa.py

import streamlit as st
import pandas as pd
from datetime import datetime

from database.movimentacoes_db import registrar_movimentacao

from database.caixa_db import (
    verificar_caixa_aberto,
    abrir_caixa,
    fechar_caixa,
    resumo_caixa,
    listar_movimentacoes_caixa
)


# ==================================================
# TELA CAIXA
# ==================================================
def tela_caixa():

    abas = st.tabs([
        "💰 Caixa",
        "➕ Movimentar Caixa"
    ])

    # ==================================================
    # ABA CAIXA
    # ==================================================
    with abas[0]:

        st.subheader("💰 Controle de Caixa")

        # ==================================================
        # VERIFICA CAIXA
        # ==================================================
        caixa = verificar_caixa_aberto()

        # ==================================================
        # TRATAMENTO SE VIER DATAFRAME
        # ==================================================
        caixa_aberto = False

        if caixa is not None:

            # Se for DataFrame
            if isinstance(caixa, pd.DataFrame):

                if not caixa.empty:

                    caixa = caixa.iloc[0]
                    caixa_aberto = True

            # Se for Series
            elif isinstance(caixa, pd.Series):

                caixa_aberto = True

            # Se for dict
            elif isinstance(caixa, dict):

                if len(caixa) > 0:
                    caixa_aberto = True

        # ==================================================
        # SEM CAIXA ABERTO
        # ==================================================
        if not caixa_aberto:

            st.warning("🔓 Nenhum caixa aberto.")

            valor_inicial = st.number_input(
                "Valor Inicial",
                min_value=0.0,
                value=0.0,
                format="%.2f"
            )

            usuario = st.text_input(
                "Operador",
                value="Administrador"
            )

            if st.button("🚀 Abrir Caixa"):

                sucesso = abrir_caixa(
                    usuario=usuario,
                    saldo_inicial=valor_inicial
                )

                if sucesso:

                    st.success("✅ Caixa aberto com sucesso!")
                    st.rerun()

                else:

                    st.error("❌ Erro ao abrir caixa.")

        # ==================================================
        # CAIXA ABERTO
        # ==================================================
        else:

            caixa_id = caixa["id"]

            st.success("🟢 Caixa Aberto")

            resumo = resumo_caixa(caixa_id)

            # Segurança caso resumo venha vazio
            if resumo is None:
                resumo = {
                    "entradas": 0,
                    "saidas": 0
                }

            entradas = resumo.get("entradas", 0)
            saidas = resumo.get("saidas", 0)

            saldo_inicial = caixa.get("saldo_inicial", 0)

            saldo_atual = (
                saldo_inicial
                + entradas
                - saidas
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Saldo Inicial",
                    f"R$ {saldo_inicial:,.2f}"
                )

            with col2:

                st.metric(
                    "Entradas",
                    f"R$ {entradas:,.2f}"
                )

            with col3:

                st.metric(
                    "Saídas",
                    f"R$ {saidas:,.2f}"
                )

            st.divider()

            st.metric(
                "💰 Saldo Atual",
                f"R$ {saldo_atual:,.2f}"
            )

            # ==================================================
            # MOVIMENTAÇÕES
            # ==================================================
            st.subheader("📋 Movimentações")

            df = listar_movimentacoes_caixa()

            if df is not None and not df.empty:

                df = df.copy()

                if "valor" in df.columns:

                    df["valor"] = df["valor"].apply(
                        lambda x: f"R$ {float(x):,.2f}"
                    )

                if "data_movimentacao" in df.columns:

                    df["data_movimentacao"] = pd.to_datetime(
                        df["data_movimentacao"],
                        errors="coerce"
                    )

                    df["data_movimentacao"] = df[
                        "data_movimentacao"
                    ].dt.strftime("%d/%m/%Y %H:%M")

                st.dataframe(
                    df,
                    use_container_width=True
                )

            else:

                st.info("Nenhuma movimentação registrada.")

            st.divider()

            # ==================================================
            # FECHAMENTO
            # ==================================================
            st.subheader("🔒 Fechar Caixa")

            valor_conferido = st.number_input(
                "Valor Conferido no Caixa",
                min_value=0.0,
                value=float(saldo_atual),
                format="%.2f"
            )

            diferenca = valor_conferido - saldo_atual

            # ==================================================
            # DIFERENÇA
            # ==================================================
            if diferenca == 0:

                st.success("✅ Caixa conferido sem diferenças.")

            elif diferenca > 0:

                st.warning(
                    f"⚠️ Sobra no caixa: R$ {diferenca:,.2f}"
                )

            else:

                st.error(
                    f"❌ Falta no caixa: R$ {abs(diferenca):,.2f}"
                )

            # ==================================================
            # FECHAR CAIXA
            # ==================================================
            if st.button("💾 Fechar Caixa"):

                sucesso = fechar_caixa(
                    caixa_id=caixa_id,
                    total_entradas=entradas,
                    total_saidas=saidas,
                    saldo_final=saldo_atual,
                    valor_conferido=valor_conferido,
                    diferenca=diferenca
                )

                if sucesso:

                    st.success("✅ Caixa fechado com sucesso!")
                    st.rerun()

                else:

                    st.error("❌ Erro ao fechar caixa.")

    # ==================================================
    # ABA MOVIMENTAR CAIXA
    # ==================================================
    with abas[1]:

        st.subheader("➕ Nova Movimentação")

        tipo = st.selectbox(
            "Tipo",
            ["entrada", "saida"]
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            value=0.0,
            format="%.2f"
        )

        descricao = st.text_input(
            "Descrição"
        )

        origem = st.selectbox(
            "Origem",
            [
                "Sangria",
                "Reforço",
                "Despesa",
                "Ajuste"
            ]
        )

        if st.button("💾 Registrar Movimentação"):

            if valor <= 0:

                st.warning("Informe um valor maior que zero.")

            else:

                sucesso = registrar_movimentacao(

                    tipo=tipo,
                    valor=valor,
                    descricao=descricao,
                    origem=origem,
                    data_movimentacao=datetime.now()

                )

                if sucesso:

                    st.success("✅ Movimentação registrada!")
                    st.rerun()

                else:

                    st.error("❌ Erro ao registrar.")