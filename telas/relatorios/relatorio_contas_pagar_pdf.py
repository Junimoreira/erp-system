import streamlit as st
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from database.connection import conectar
import pandas as pd


def gerar_pdf_contas_pagar():

    conn = conectar()

    if conn is None:
        st.error("Erro ao conectar com o banco.")
        return None

    query = """
        SELECT
            id,
            descricao,
            valor,
            vencimento,
            status,
            forma_pagamento
        FROM contas_pagar
        ORDER BY vencimento
    """

    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return None

    if df.empty:
        st.warning("Nenhuma conta encontrada.")
        return None

    nome_arquivo = "relatorio_contas_pagar.pdf"

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    # LOGO
    try:
        logo = Image("assets/Logo1.png", width=120, height=60)
        elementos.append(logo)
    except:
        pass

    # TÍTULO
    elementos.append(Paragraph("📤 RELATÓRIO DE CONTAS A PAGAR", styles["Title"]))
    elementos.append(Spacer(1, 12))

    # DATA
    elementos.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 20))

    # TOTAIS
    total = df["valor"].sum()

    elementos.append(Paragraph(
        f"<b>Total a pagar:</b> R$ {total:.2f}",
        styles["Normal"]
    ))
    elementos.append(Spacer(1, 12))

    # TABELA
    dados = [["ID", "Descrição", "Valor", "Vencimento", "Status"]]

    for _, row in df.iterrows():
        dados.append([
            row["id"],
            row["descricao"],
            f"R$ {row['valor']:.2f}",
            row["vencimento"].strftime("%d/%m/%Y") if row["vencimento"] else "",
            row["status"]
        ])

    tabela = Table(dados)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.red),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elementos.append(tabela)

    doc.build(elementos)

    return nome_arquivo


def tela_relatorio_contas_pagar():

    st.title("📤 Relatório Contas a Pagar")

    arquivo = gerar_pdf_contas_pagar()

    if arquivo:
        with open(arquivo, "rb") as f:
            st.download_button(
                "📥 Baixar PDF",
                f,
                file_name=arquivo,
                mime="application/pdf"
            )