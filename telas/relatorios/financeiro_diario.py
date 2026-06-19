import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

from database.movimentacoes_db import (
    listar_movimentacoes_periodo,
    resumo_por_periodo
)

from services.pdf_service import gerar_pdf_relatorio


def tela_relatorios():

    st.title("📊 Relatórios")

    abas = st.tabs([
        "📈 Financeiro Diário"
    ])

    with abas[0]:

        st.subheader("📈 Relatório Financeiro Diário")

        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input(
                "Data Inicial",
                value=date.today()
            )

        with col2:
            data_fim = st.date_input(
                "Data Final",
                value=date.today()
            )

        if data_inicio > data_fim:
            st.error("A data inicial não pode ser maior que a data final.")
            return

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

        col3.metric("📥 Entradas", f"R$ {resumo['entradas']:,.2f}")
        col4.metric("📤 Saídas", f"R$ {resumo['saidas']:,.2f}")
        col5.metric("💰 Saldo", f"R$ {resumo['saldo']:,.2f}")

        st.divider()

        if df.empty:
            st.info("Nenhuma movimentação encontrada no período.")
            return

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

        if "valor" in df_relatorio.columns:
            df_relatorio["valor"] = df_relatorio["valor"].astype(float)

        st.dataframe(
            df_relatorio,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        resumo_pdf = {
            "Período": f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}",
            "Entradas": f"R$ {resumo['entradas']:,.2f}",
            "Saídas": f"R$ {resumo['saidas']:,.2f}",
            "Saldo": f"R$ {resumo['saldo']:,.2f}"
        }

        pdf = gerar_pdf_relatorio(
            titulo="Relatório Financeiro Diário",
            df=df_relatorio,
            resumo=resumo_pdf
        )

        excel_buffer = BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_relatorio.to_excel(
                writer,
                index=False,
                sheet_name="Financeiro Diário"
            )

        excel_buffer.seek(0)

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
                data=excel_buffer,
                file_name="relatorio_financeiro_diario.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )