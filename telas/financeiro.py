import streamlit as st
from database.financeiro_db import *
from datetime import date


def tela_financeiro():

    st.title("💰 Financeiro")

    abas = st.tabs([
        "➕ Novo Lançamento",
        "📋 Movimentações",
        "✏️ Editar"
    ])

    # ==========================================
    # NOVO LANÇAMENTO
    # ==========================================
    with abas[0]:

        st.subheader("Novo Lançamento")

        descricao = st.text_input("Descrição")

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            format="%.2f"
        )

        tipo = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"],
            key="tipo_cadastro"
        )

        categoria = st.text_input("Categoria")

        data_lancamento = st.date_input(
            "Data",
            value=date.today(),
            key="data_cadastro"
        )

        if st.button("Salvar Lançamento"):

            cadastrar_movimentacao(
                descricao,
                valor,
                tipo,
                categoria,
                data_lancamento
            )

            st.success("✅ Lançamento cadastrado!")

            st.rerun()

    # ==========================================
    # LISTAGEM
    # ==========================================
    with abas[1]:

        st.subheader("Movimentações")

        df = listar_movimentacoes()

        st.dataframe(
            df,
            use_container_width=True
        )

        if not df.empty:

            entradas = df[df["tipo"] == "Entrada"]["valor"].sum()

            saidas = df[df["tipo"] == "Saída"]["valor"].sum()

            saldo = entradas - saidas

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Entradas",
                f"R$ {entradas:,.2f}"
            )

            col2.metric(
                "Saídas",
                f"R$ {saidas:,.2f}"
            )

            col3.metric(
                "Saldo",
                f"R$ {saldo:,.2f}"
            )

    # ==========================================
    # EDITAR
    # ==========================================
    with abas[2]:

        st.subheader("Editar Lançamento")

        df = listar_movimentacoes()

        if not df.empty:

            id_mov = st.selectbox(
                "Selecione",
                df["id"]
            )

            mov = df[df["id"] == id_mov].iloc[0]

            nova_descricao = st.text_input(
                "Descrição",
                value=mov["descricao"]
            )

            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                value=float(mov["valor"]),
                format="%.2f"
            )

            novo_tipo = st.selectbox(
                "Tipo",
                ["Entrada", "Saída"],
                key="tipo_edicao"
            )

            nova_categoria = st.text_input(
                "Categoria",
                value=mov["categoria"]
            )

            nova_data = st.date_input(
                "Data",
                value=mov["data_lancamento"],
                key="data_edicao"
           )

            if st.button("Atualizar"):

                atualizar_movimentacao(
                    id_mov,
                    nova_descricao,
                    novo_valor,
                    novo_tipo,
                    nova_categoria,
                    nova_data
                )

                st.success("✅ Atualizado!")

                st.rerun()

            st.divider()

            if st.button("🗑️ Excluir"):

                excluir_movimentacao(id_mov)

                st.success("Movimentação excluída!")

                st.rerun()

        else:

            st.info("Nenhuma movimentação cadastrada.")