# telas/caixa.py

import streamlit as st
import pandas as pd
from datetime import datetime

from database.movimentacoes_db import (
    registrar_movimentacao,
    listar_movimentacoes,
    atualizar_movimentacao,
    excluir_movimentacao
)

from database.caixa_db import (
    abrir_caixa,
    fechar_caixa,
    verificar_caixa_aberto,
    listar_historico_caixa
)


# ==================================================
# RESUMO CAIXA (LOCAL - EVITA ERRO DE IMPORT)
# ==================================================
def resumo_caixa(caixa_id):

    try:
        df = listar_movimentacoes()

        if df is None or df.empty:
            return {"entradas": 0, "saidas": 0}

        df = df[df["caixa_id"] == caixa_id]

        entradas = df[df["tipo"] == "entrada"]["valor"].sum()
        saidas = df[df["tipo"] == "saida"]["valor"].sum()

        return {
            "entradas": float(entradas),
            "saidas": float(saidas)
        }

    except Exception as e:
        print("Erro resumo_caixa:", e)
        return {"entradas": 0, "saidas": 0}


# ==================================================
# MOVIMENTAÇÕES DO CAIXA
# ==================================================
def listar_movimentacoes_caixa(caixa_id):

    try:
        df = listar_movimentacoes()

        if df is None or df.empty:
            return pd.DataFrame()

        return df[df["caixa_id"] == caixa_id]

    except Exception as e:
        print("Erro listar_movimentacoes_caixa:", e)
        return pd.DataFrame()


# ==================================================
# TELA CAIXA
# ==================================================
def tela_caixa():

    abas = st.tabs([
    "💰 Caixa",
    "➕ Movimentar Caixa",
    "📊 Relatório Caixa"
    ])

    # ==================================================
    # ABA CAIXA
    # ==================================================
    with abas[0]:

        st.subheader("💰 Controle de Caixa")

        caixa = verificar_caixa_aberto()
        caixa_aberto = caixa is not None

        # ==================================================
        # SEM CAIXA
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

                sucesso = abrir_caixa(usuario, float(valor_inicial))

                if sucesso:
                    st.success("Caixa aberto com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao abrir caixa.")

        # ==================================================
        # CAIXA ABERTO
        # ==================================================
        else:

            caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

            st.success("🟢 Caixa Aberto")

            resumo = resumo_caixa(caixa_id)

            entradas = resumo["entradas"]
            saidas = resumo["saidas"]

            saldo_inicial = float(
                caixa[3] if isinstance(caixa, tuple) else caixa["saldo_inicial"]
            )

            saldo_atual = saldo_inicial + entradas - saidas

            # ==================================================
            # MÉTRICAS
            # ==================================================
            col1, col2, col3 = st.columns(3)

            col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
            col2.metric("Entradas", f"R$ {entradas:,.2f}")
            col3.metric("Saídas", f"R$ {saidas:,.2f}")

            st.metric("💰 Saldo Atual", f"R$ {saldo_atual:,.2f}")

            st.divider()

            # ==================================================
            # MOVIMENTAÇÕES
            # ==================================================
            st.subheader("📋 Movimentações")

            df = listar_movimentacoes_caixa(caixa_id)

            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Nenhuma movimentação registrada.")

            st.divider()

            # ==================================================
            # FECHAR CAIXA
            # ==================================================
            st.subheader("🔒 Fechar Caixa")

            valor_conferido = st.number_input(
                "Valor Conferido",
                min_value=0.0,
                value=float(saldo_atual),
                format="%.2f"
            )

            diferenca = float(valor_conferido) - float(saldo_atual)

            if diferenca != 0:
                st.warning(f"Diferença: R$ {diferenca:,.2f}")
            else:
                st.success("Sem diferenças.")

            if st.button("💾 Fechar Caixa"):

                sucesso = fechar_caixa(
                    caixa_id,
                    float(valor_conferido)
                )

                if sucesso:
                    st.success("Caixa fechado!")
                    st.rerun()
                else:
                    st.error("Erro ao fechar caixa.")

    # ==================================================
    # ABA MOVIMENTAÇÃO
    # ==================================================
    with abas[1]:

        st.subheader("➕ Nova Movimentação")

        caixa = verificar_caixa_aberto()

        if caixa is None:
            st.warning("Abra um caixa primeiro.")
            return

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        tipo = st.selectbox("Tipo", ["entrada", "saida"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")

        if st.button("Registrar"):

            if valor <= 0:
                st.warning("Valor inválido.")
            else:

                sucesso = registrar_movimentacao(
                    caixa_id,
                    tipo,
                    float(valor),
                    descricao,
                    "Ajuste",
                    datetime.now()
                )

                if sucesso:
                    st.success("Movimentação registrada!")
                    st.rerun()
                else:
                    st.error("Erro ao registrar.")

        # ==================================================
    # ABA RELATÓRIO
    # ==================================================
    with abas[2]:

        st.subheader("📊 Relatório Diário de Caixa")

        try:

            historico = listar_historico_caixa()

            if historico is None or historico.empty:

                st.warning(
                    "Nenhum histórico de caixa encontrado."
                )

            else:

                # ==========================================
                # GARANTE DATAFRAME
                # ==========================================
                df_mov = listar_movimentacoes()

                if df_mov is None:
                    df_mov = pd.DataFrame()

                relatorio = []

                # ==========================================
                # PERCORRE CADA CAIXA
                # ==========================================
                for _, caixa in historico.iterrows():

                    caixa_id = caixa["id"]

                    # ==========================================
                    # MOVIMENTAÇÕES DO CAIXA
                    # ==========================================
                    if not df_mov.empty:

                        movimentacoes = df_mov[
                            df_mov["caixa_id"] == caixa_id
                        ]

                    else:

                        movimentacoes = pd.DataFrame()

                    # ==========================================
                    # ENTRADAS
                    # ==========================================
                    entradas = 0

                    if not movimentacoes.empty:

                        entradas = movimentacoes[
                            movimentacoes["tipo"] == "entrada"
                        ]["valor"].sum()

                    # ==========================================
                    # SAÍDAS
                    # ==========================================
                    saidas = 0

                    if not movimentacoes.empty:

                        saidas = movimentacoes[
                            movimentacoes["tipo"] == "saida"
                        ]["valor"].sum()

                    # ==========================================
                    # VALORES
                    # ==========================================
                    saldo_inicial = float(
                        caixa["saldo_inicial"]
                    )

                    saldo_sistema = (
                        saldo_inicial
                        + float(entradas)
                        - float(saidas)
                    )

                    saldo_conferido = float(
                        caixa["saldo_conferido"]
                    )

                    diferenca = float(
                        caixa["diferenca"]
                    )

                    # ==========================================
                    # ADICIONA NO RELATÓRIO
                    # ==========================================
                    relatorio.append({

                        "ID":
                            caixa_id,

                        "Usuário":
                            caixa["usuario"],

                        "Data Abertura":
                            caixa["data_abertura"],

                        "Data Fechamento":
                            caixa["data_fechamento"],

                        "Saldo Inicial":
                            round(saldo_inicial, 2),

                        "Entradas":
                            round(float(entradas), 2),

                        "Saídas":
                            round(float(saidas), 2),

                        "Saldo Sistema":
                            round(saldo_sistema, 2),

                        "Saldo Conferido":
                            round(saldo_conferido, 2),

                        "Diferença":
                            round(diferenca, 2),

                        "Status":
                            caixa["status"]

                    })

                # ==========================================
                # DATAFRAME FINAL
                # ==========================================
                df_relatorio = pd.DataFrame(
                    relatorio
                )

                # ==========================================
                # EXIBE TABELA
                # ==========================================
                st.dataframe(
                    df_relatorio,
                    use_container_width=True,
                    height=500
                )

                st.divider()

                # ==========================================
                # RESUMO
                # ==========================================
                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "💰 Total Entradas",
                        f"R$ {df_relatorio['Entradas'].sum():,.2f}"
                    )

                with col2:

                    st.metric(
                        "💸 Total Saídas",
                        f"R$ {df_relatorio['Saídas'].sum():,.2f}"
                    )

                with col3:

                    st.metric(
                        "🏦 Saldo Total",
                        f"R$ {df_relatorio['Saldo Sistema'].sum():,.2f}"
                    )

        except Exception as erro:

            st.error(
                f"Erro relatório caixa: {erro}"
            )