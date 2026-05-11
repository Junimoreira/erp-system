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

    categorias = [
        "Vendas",
        "Estoque",
        "Salários",
        "Impostos",
        "Marketing",
        "Outros"
    ]

    # ==================================================
    # NOVO LANÇAMENTO
    # ==================================================
    with abas[0]:

        st.subheader("Novo Lançamento")

        descricao = st.text_input(
            "Descrição",
            key="descricao_cadastro"
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            format="%.2f",
            key="valor_cadastro"
        )

        tipo = st.selectbox(
            "Tipo",
            ["Entrada", "Saída"],
            key="tipo_cadastro"
        )

        categoria = st.selectbox(
            "Categoria",
            categorias,
            key="categoria_cadastro"
        )

        data_lancamento = st.date_input(
            "Data",
            value=date.today(),
            key="data_cadastro"
        )

        if st.button(
            "Salvar Lançamento",
            key="botao_salvar"
        ):

            cadastrar_movimentacao(
                descricao,
                valor,
                tipo,
                categoria,
                data_lancamento
            )

            st.success("✅ Lançamento cadastrado com sucesso!")

            st.rerun()

    # ==================================================
    # LISTAGEM
    # ==================================================
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

            st.divider()

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

    # ==================================================
    # EDITAR
    # ==================================================
    with abas[2]:

        st.subheader("Editar Lançamento")

        df = listar_movimentacoes()

        if not df.empty:

            id_mov = st.selectbox(
                "Selecione o Lançamento",
                df["id"],
                key="select_edicao"
            )

            mov = df[df["id"] == id_mov].iloc[0]

            indice_tipo = (
                0 if mov["tipo"] == "Entrada" else 1
            )

            indice_categoria = (
                categorias.index(mov["categoria"])
                if mov["categoria"] in categorias
                else 0
            )

            nova_descricao = st.text_input(
                "Descrição",
                value=mov["descricao"],
                key=f"descricao_{id_mov}"
            )

            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                value=float(mov["valor"]),
                format="%.2f",
                key=f"valor_{id_mov}"
            )

            novo_tipo = st.selectbox(
                "Tipo",
                ["Entrada", "Saída"],
                index=indice_tipo,
                key=f"tipo_{id_mov}"
            )

            nova_categoria = st.selectbox(
                "Categoria",
                categorias,
                index=indice_categoria,
                key=f"categoria_{id_mov}"
            )

            nova_data = st.date_input(
                "Data",
                value=mov["data_lancamento"],
                key=f"data_{id_mov}"
            )

            if st.button(
                "Atualizar",
                key=f"atualizar_{id_mov}"
            ):

                atualizar_movimentacao(
                    id_mov,
                    nova_descricao,
                    novo_valor,
                    novo_tipo,
                    nova_categoria,
                    nova_data
                )

                st.success("✅ Lançamento atualizado!")

                st.rerun()

            st.divider()

            if st.button(
                "🗑️ Excluir",
                key=f"excluir_{id_mov}"
            ):

                excluir_movimentacao(id_mov)

                st.success("✅ Lançamento excluído!")

                st.rerun()

        else:

            st.info("Nenhuma movimentação cadastrada.")