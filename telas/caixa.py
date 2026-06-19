# telas/caixa.py

import streamlit as st
import pandas as pd
from datetime import datetime

from database.movimentacoes_db import (
    registrar_movimentacao,
    listar_movimentacoes_caixa as db_listar_movimentacoes_caixa,
    excluir_movimentacao,
    resumo_caixa as db_resumo_caixa
)

from database.caixa_db import (
    abrir_caixa,
    fechar_caixa,
    verificar_caixa_aberto,
    listar_historico_caixa,
    saldo_caixa_atual
)


# ==================================================
# VALOR SEGURO
# ==================================================
def valor_seguro(valor):
    try:
        if valor is None:
            return 0.0

        if pd.isna(valor):
            return 0.0

        return float(valor)

    except Exception:
        return 0.0


# ==================================================
# TRATAMENTO TEXTO
# ==================================================
def tratar_texto(valor):
    try:
        if valor is None:
            return ""

        if pd.isna(valor):
            return ""

        return str(valor).strip()

    except Exception:
        return ""


# ==================================================
# IDENTIFICA COLUNA DATA
# ==================================================
def identificar_coluna_data(df):

    if df is None or df.empty:
        return None

    if "data_movimentacao" in df.columns:
        return "data_movimentacao"

    if "data" in df.columns:
        return "data"

    return None


# ==================================================
# OBTER ID DO CAIXA
# ==================================================
def obter_caixa_id(caixa):

    if caixa is None:
        return None

    if isinstance(caixa, tuple):
        return caixa[0]

    return caixa.get("id")


# ==================================================
# OBTER SALDO INICIAL
# ==================================================
def obter_saldo_inicial(caixa):

    if caixa is None:
        return 0.0

    if isinstance(caixa, tuple):
        try:
            return valor_seguro(caixa[4])
        except Exception:
            return 0.0

    return valor_seguro(caixa.get("saldo_inicial", 0))


# ==================================================
# LISTAR MOVIMENTAÇÕES CAIXA
# ==================================================
def obter_movimentacoes_caixa(caixa_id):

    try:
        df = db_listar_movimentacoes_caixa(caixa_id)

        if df is None or df.empty:
            return pd.DataFrame()

        if "caixa_id" not in df.columns:
            return pd.DataFrame()

        return df[df["caixa_id"] == caixa_id]

    except Exception as erro:
        print("Erro listar_movimentacoes_caixa:", erro)
        return pd.DataFrame()


# ==================================================
# ORDENAÇÃO SEGURA
# ==================================================
def ordenar_dataframe(df):

    try:
        if df is None or df.empty:
            return df

        coluna_data = identificar_coluna_data(df)

        if coluna_data:
            df[coluna_data] = pd.to_datetime(
                df[coluna_data],
                errors="coerce"
            )

            df = df.sort_values(
                by=coluna_data,
                ascending=False
            )

        return df

    except Exception as erro:
        print("Erro ordenação:", erro)
        return df


# ==================================================
# TELA CAIXA
# ==================================================
def tela_caixa():

    abas = st.tabs([
        "💰 Caixa",
        "➕ Movimentar Caixa",
        "📋 Consulta Caixa",
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

            usuario_padrao = st.session_state.get(
                "usuario",
                "Administrador"
            )

            usuario = st.text_input(
                "Operador",
                value=usuario_padrao
            )

            if st.button("🚀 Abrir Caixa"):

                sucesso = abrir_caixa(
                    usuario,
                    float(valor_inicial)
                )

                if sucesso:
                    st.success("Caixa aberto com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao abrir caixa.")

        # ==================================================
        # CAIXA ABERTO
        # ==================================================
        else:

            caixa_id = obter_caixa_id(caixa)
            saldo_inicial = obter_saldo_inicial(caixa)

            resumo = db_resumo_caixa(caixa_id)

            entradas = valor_seguro(
                resumo.get("entradas", 0)
            )

            saidas = valor_seguro(
                resumo.get("saidas", 0)
            )

            saldo_atual = valor_seguro(
                saldo_caixa_atual(caixa_id)
            )

            st.success("🟢 Caixa Aberto")

            col1, col2, col3, col4 = st.columns(4)

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

            with col4:
                st.metric(
                    "Saldo Atual",
                    f"R$ {saldo_atual:,.2f}"
                )

            st.divider()

            # ==================================================
            # MOVIMENTAÇÕES
            # ==================================================
            st.subheader("📋 Últimas Movimentações")

            df = db_listar_movimentacoes_caixa(caixa_id)

            if df is not None and not df.empty:

                df = df.fillna("")
                df = ordenar_dataframe(df)

                st.dataframe(
                    df,
                    use_container_width=True,
                    height=300
                )

                st.divider()

                st.subheader("🗑️ Excluir Movimentação")

                st.warning(
                    "Atenção: excluir movimentação pode alterar a conferência do caixa."
                )

                if "id" in df.columns:

                    movimentacao_id = st.selectbox(
                        "Selecione a movimentação",
                        df["id"].tolist()
                    )

                    confirmar_exclusao = st.checkbox(
                        "Confirmo que desejo excluir esta movimentação",
                        key="confirmar_excluir_mov_caixa"
                    )

                    if st.button("❌ Excluir Movimentação"):

                        if not confirmar_exclusao:
                            st.warning(
                                "Marque a confirmação antes de excluir."
                            )
                            return

                        sucesso = excluir_movimentacao(
                            movimentacao_id
                        )

                        if sucesso:
                            st.success(
                                "Movimentação excluída com sucesso!"
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Erro ao excluir movimentação."
                            )

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

            confirmar_fechamento = st.checkbox(
                "Confirmo o fechamento deste caixa",
                key="confirmar_fechamento_caixa"
            )

            if st.button("💾 Fechar Caixa"):

                if not confirmar_fechamento:
                    st.warning(
                        "Marque a confirmação antes de fechar o caixa."
                    )
                    return

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

        else:

            caixa_id = obter_caixa_id(caixa)

            col1, col2 = st.columns(2)

            with col1:
                tipo = st.selectbox(
                    "Tipo",
                    ["entrada", "saida"]
                )

            with col2:
                categoria = st.selectbox(
                    "Categoria",
                    [
                        "Venda",
                        "Sangria",
                        "Suprimento",
                        "Pagamento",
                        "Ajuste"
                    ]
                )

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                format="%.2f"
            )

            descricao = st.text_input("Descrição")

            if st.button("💾 Registrar Movimentação"):

                if valor <= 0:
                    st.warning("Valor inválido.")

                else:
                    try:
                        sucesso = registrar_movimentacao(
                            caixa_id=caixa_id,
                            tipo=tipo,
                            valor=float(valor),
                            descricao=tratar_texto(descricao),
                            categoria=categoria,
                            data_movimentacao=datetime.now(),
                            origem="CAIXA",
                            meio="CAIXA"
                        )

                        if sucesso:
                            st.success("Movimentação registrada!")
                            st.rerun()
                        else:
                            st.error("Erro ao registrar.")

                    except Exception as erro:
                        st.error(f"Erro movimentação: {erro}")

    # ==================================================
    # ABA CONSULTA CAIXA
    # ==================================================
    with abas[2]:

        st.subheader("📋 Consulta Caixa")

        caixa = verificar_caixa_aberto()

        if caixa is None:
            st.info("Nenhum caixa aberto para consulta.")

        else:

            caixa_id = obter_caixa_id(caixa)

            busca = st.text_input("🔎 Buscar movimentação")

            df = obter_movimentacoes_caixa(caixa_id)

            if df is None or df.empty:
                st.info("Nenhuma movimentação encontrada.")

            else:

                df = df.fillna("")

                col1, col2 = st.columns(2)

                with col1:
                    filtro_tipo = st.selectbox(
                        "Tipo",
                        ["Todos", "entrada", "saida"]
                    )

                with col2:
                    filtro_data = st.date_input("Data")

                if busca and "descricao" in df.columns:
                    df = df[
                        df["descricao"]
                        .astype(str)
                        .str.contains(
                            busca,
                            case=False,
                            na=False
                        )
                    ]

                if filtro_tipo != "Todos":
                    df = df[
                        df["tipo"]
                        .astype(str)
                        .str.lower()
                        == filtro_tipo
                    ]

                coluna_data = identificar_coluna_data(df)

                if coluna_data:

                    df[coluna_data] = pd.to_datetime(
                        df[coluna_data],
                        errors="coerce"
                    )

                    df = df[
                        df[coluna_data]
                        .dt.date
                        == filtro_data
                    ]

                df = ordenar_dataframe(df)

                st.dataframe(
                    df,
                    use_container_width=True,
                    height=500
                )

    # ==================================================
    # ABA RELATÓRIO
    # ==================================================
    with abas[3]:

        st.subheader("📊 Relatório Diário de Caixa")

        historico = listar_historico_caixa()

        if historico is None or historico.empty:
            st.warning("Nenhum histórico encontrado.")
        else:
            st.dataframe(
                historico,
                use_container_width=True,
                height=500
            )