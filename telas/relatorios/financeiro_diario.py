import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

from database.movimentacoes_db import (
    listar_movimentacoes_periodo,
    resumo_por_periodo
)

from database.contas_pagar_db import listar_contas as listar_contas_pagar
from database.contas_receber_db import listar_contas as listar_contas_receber

from services.pdf_service import gerar_pdf_relatorio


# ==================================================
# EXCEL
# ==================================================
def gerar_excel(df, nome_aba):

    excel_buffer = BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name=nome_aba
        )

    excel_buffer.seek(0)

    return excel_buffer


# ==================================================
# FORMATAR MOEDA
# ==================================================
def formatar_moeda(valor):

    try:
        return f"R$ {float(valor):,.2f}"
    except Exception:
        return "R$ 0,00"


# ==================================================
# FILTRAR PERÍODO
# ==================================================
def filtrar_periodo(df, coluna_data, data_inicio, data_fim):

    if df.empty or coluna_data not in df.columns:
        return df

    df = df.copy()

    df[coluna_data] = pd.to_datetime(
        df[coluna_data],
        errors="coerce"
    )

    df = df[
        (df[coluna_data].dt.date >= data_inicio)
        &
        (df[coluna_data].dt.date <= data_fim)
    ]

    return df


# ==================================================
# TELA RELATÓRIOS
# ==================================================
def tela_relatorios():

    st.title("📊 Relatórios")

    abas = st.tabs([
        "📈 Financeiro Diário",
        "📤 Contas a Pagar",
        "📥 Contas a Receber"
    ])

    # ==================================================
    # FINANCEIRO DIÁRIO
    # ==================================================
    with abas[0]:

        st.subheader("📈 Relatório Financeiro Diário")

        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data Inicial",
                value=date.today(),
                key="fin_data_inicio"
            )

        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=date.today(),
                key="fin_data_fim"
            )

        if data_inicio > data_fim:
            st.error("A data inicial não pode ser maior que a data final.")
        else:

            df = listar_movimentacoes_periodo(
                data_inicio,
                data_fim
            )

            resumo = resumo_por_periodo(
                data_inicio,
                data_fim
            )

            st.divider()

            col3, col4, col5 = st.columns(3)

            col3.metric("📥 Entradas", formatar_moeda(resumo["entradas"]))
            col4.metric("📤 Saídas", formatar_moeda(resumo["saidas"]))
            col5.metric("💰 Saldo", formatar_moeda(resumo["saldo"]))

            st.divider()

            if df.empty:
                st.info("Nenhuma movimentação encontrada no período.")
            else:

                colunas = [
                    "data_movimentacao",
                    "tipo",
                    "descricao",
                    "categoria",
                    "origem",
                    "meio",
                    "valor"
                ]

                colunas_existentes = [
                    coluna for coluna in colunas if coluna in df.columns
                ]

                df_relatorio = df[colunas_existentes].copy()

                if "data_movimentacao" in df_relatorio.columns:
                    df_relatorio["data_movimentacao"] = pd.to_datetime(
                        df_relatorio["data_movimentacao"],
                        errors="coerce"
                    ).dt.strftime("%d/%m/%Y %H:%M")

                st.dataframe(
                    df_relatorio,
                    use_container_width=True,
                    hide_index=True
                )

                resumo_pdf = {
                    "Período": f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}",
                    "Entradas": formatar_moeda(resumo["entradas"]),
                    "Saídas": formatar_moeda(resumo["saidas"]),
                    "Saldo": formatar_moeda(resumo["saldo"])
                }

                pdf = gerar_pdf_relatorio(
                    titulo="Relatório Financeiro Diário",
                    df=df_relatorio,
                    resumo=resumo_pdf
                )

                excel = gerar_excel(
                    df_relatorio,
                    "Financeiro Diário"
                )

                col6, col7 = st.columns(2)

                with col6:
                    st.download_button(
                        "📄 Baixar PDF",
                        data=pdf,
                        file_name="relatorio_financeiro_diario.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                with col7:
                    st.download_button(
                        "📊 Baixar Excel",
                        data=excel,
                        file_name="relatorio_financeiro_diario.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

    # ==================================================
    # CONTAS A PAGAR
    # ==================================================
    with abas[1]:

        st.subheader("📤 Relatório de Contas a Pagar")

        df = listar_contas_pagar()

        if df.empty:
            st.info("Nenhuma conta a pagar encontrada.")
        else:

            col1, col2, col3 = st.columns(3)

            with col1:
                data_inicio = st.date_input(
                    "Data Inicial",
                    value=date.today().replace(day=1),
                    key="pagar_data_inicio"
                )

            with col2:
                data_fim = st.date_input(
                    "Data Final",
                    value=date.today(),
                    key="pagar_data_fim"
                )

            with col3:
                status_opcoes = ["TODOS"] + sorted(
                    df["status"].astype(str).str.upper().unique().tolist()
                )

                status = st.selectbox(
                    "Status",
                    status_opcoes,
                    key="pagar_status"
                )

            df_relatorio = filtrar_periodo(
                df,
                "vencimento",
                data_inicio,
                data_fim
            )

            if status != "TODOS":
                df_relatorio = df_relatorio[
                    df_relatorio["status"]
                    .astype(str)
                    .str.upper()
                    == status
                ]

            if "categoria" in df_relatorio.columns:
                categoria_opcoes = ["TODAS"] + sorted(
                    df["categoria"]
                    .fillna("")
                    .astype(str)
                    .str.upper()
                    .unique()
                    .tolist()
                )

                categoria = st.selectbox(
                    "Categoria",
                    categoria_opcoes,
                    key="pagar_categoria"
                )

                if categoria != "TODAS":
                    df_relatorio = df_relatorio[
                        df_relatorio["categoria"]
                        .astype(str)
                        .str.upper()
                        == categoria
                    ]

            if "tipo" in df_relatorio.columns:
                tipo_opcoes = ["TODOS"] + sorted(
                    df["tipo"]
                    .fillna("")
                    .astype(str)
                    .str.upper()
                    .unique()
                    .tolist()
                )

                tipo = st.selectbox(
                    "Tipo",
                    tipo_opcoes,
                    key="pagar_tipo"
                )

                if tipo != "TODOS":
                    df_relatorio = df_relatorio[
                        df_relatorio["tipo"]
                        .astype(str)
                        .str.upper()
                        == tipo
                    ]

            total = (
                df_relatorio["valor"].astype(float).sum()
                if not df_relatorio.empty and "valor" in df_relatorio.columns
                else 0
            )

            st.metric("Total Contas a Pagar", formatar_moeda(total))

            st.dataframe(
                df_relatorio,
                use_container_width=True,
                hide_index=True
            )

            resumo_pdf = {
                "Período": f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}",
                "Status": status,
                "Total": formatar_moeda(total)
            }

            pdf = gerar_pdf_relatorio(
                titulo="Relatório de Contas a Pagar",
                df=df_relatorio,
                resumo=resumo_pdf
            )

            excel = gerar_excel(
                df_relatorio,
                "Contas a Pagar"
            )

            col4, col5 = st.columns(2)

            with col4:
                st.download_button(
                    "📄 Baixar PDF",
                    data=pdf,
                    file_name="relatorio_contas_pagar.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with col5:
                st.download_button(
                    "📊 Baixar Excel",
                    data=excel,
                    file_name="relatorio_contas_pagar.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

    # ==================================================
    # CONTAS A RECEBER
    # ==================================================
    with abas[2]:

        st.subheader("📥 Relatório de Contas a Receber")

        df = listar_contas_receber()

        if df.empty:
            st.info("Nenhuma conta a receber encontrada.")
        else:

            col1, col2, col3 = st.columns(3)

            with col1:
                data_inicio = st.date_input(
                    "Data Inicial",
                    value=date.today().replace(day=1),
                    key="receber_data_inicio"
                )

            with col2:
                data_fim = st.date_input(
                    "Data Final",
                    value=date.today(),
                    key="receber_data_fim"
                )

            with col3:
                status_opcoes = ["TODOS"] + sorted(
                    df["status"].astype(str).str.upper().unique().tolist()
                )

                status = st.selectbox(
                    "Status",
                    status_opcoes,
                    key="receber_status"
                )

            df_relatorio = filtrar_periodo(
                df,
                "vencimento",
                data_inicio,
                data_fim
            )

            if status != "TODOS":
                df_relatorio = df_relatorio[
                    df_relatorio["status"]
                    .astype(str)
                    .str.upper()
                    == status
                ]

            total = (
                df_relatorio["valor"].astype(float).sum()
                if not df_relatorio.empty and "valor" in df_relatorio.columns
                else 0
            )

            st.metric("Total Contas a Receber", formatar_moeda(total))

            st.dataframe(
                df_relatorio,
                use_container_width=True,
                hide_index=True
            )

            resumo_pdf = {
                "Período": f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}",
                "Status": status,
                "Total": formatar_moeda(total)
            }

            pdf = gerar_pdf_relatorio(
                titulo="Relatório de Contas a Receber",
                df=df_relatorio,
                resumo=resumo_pdf
            )

            excel = gerar_excel(
                df_relatorio,
                "Contas a Receber"
            )

            col4, col5 = st.columns(2)

            with col4:
                st.download_button(
                    "📄 Baixar PDF",
                    data=pdf,
                    file_name="relatorio_contas_receber.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            with col5:
                st.download_button(
                    "📊 Baixar Excel",
                    data=excel,
                    file_name="relatorio_contas_receber.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )