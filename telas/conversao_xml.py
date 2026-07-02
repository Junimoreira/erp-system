import streamlit as st
import pandas as pd

from database.produto_db import listar_produtos

from database.conversao_xml_db import (
    listar_conversoes_xml,
    cadastrar_conversao_xml,
    atualizar_conversao_xml,
    excluir_conversao_xml
)


def tela_conversao_xml():

    st.title("📦 Conversão XML → Estoque")

    st.info(
        "Use esta tela para configurar produtos comprados em caixa, pacote, fardo ou kit, "
        "mas vendidos/estocados em unidade."
    )

    abas = st.tabs([
        "➕ Nova Conversão",
        "📋 Conversões",
        "✏️ Editar",
        "🗑️ Excluir"
    ])

    produtos = listar_produtos()

    if produtos is None or produtos.empty:
        st.warning("Cadastre produtos antes de configurar conversões.")
        return

    produto_map = {
        f"{row['id']} - {row['nome']}": row["id"]
        for _, row in produtos.iterrows()
    }

    tipos_compra = [
        "UNIDADE",
        "CAIXA",
        "PACOTE",
        "FARDO",
        "KIT",
        "RESMA",
        "DISPLAY",
        "OUTRO"
    ]

    unidades = [
        "UNIDADE",
        "CAIXA",
        "PACOTE",
        "FARDO",
        "KIT",
        "RESMA",
        "DISPLAY",
        "OUTRO"
    ]

    with abas[0]:

        st.subheader("➕ Nova Conversão")

        with st.form("form_nova_conversao_xml"):

            produto_nome = st.selectbox(
                "Produto",
                list(produto_map.keys())
            )

            produto_id = produto_map[produto_nome]

            col1, col2, col3 = st.columns(3)

            with col1:
                tipo_compra = st.selectbox(
                    "Tipo comprado no XML",
                    tipos_compra,
                    index=1
                )

            with col2:
                unidade_compra = st.selectbox(
                    "Unidade de compra",
                    unidades,
                    index=1
                )

            with col3:
                unidade_estoque = st.selectbox(
                    "Unidade no estoque/venda",
                    unidades,
                    index=0
                )

            fator_conversao = st.number_input(
                "Fator de conversão",
                min_value=0.001,
                value=1.000,
                step=1.000,
                format="%.3f",
                help="Exemplo: se 1 caixa tem 12 unidades, informe 12."
            )

            col4, col5 = st.columns(2)

            with col4:
                codigo_barras = st.text_input(
                    "Código de barras / EAN"
                )

            with col5:
                codigo_fornecedor = st.text_input(
                    "Código do fornecedor"
                )

            ativo = st.checkbox(
                "Conversão ativa",
                value=True
            )

            observacoes = st.text_area("Observações")

            st.info(
                f"Exemplo: 1 {tipo_compra} = {fator_conversao:.3f} {unidade_estoque}(s)."
            )

            salvar = st.form_submit_button(
                "💾 Salvar Conversão",
                use_container_width=True
            )

            if salvar:

                sucesso = cadastrar_conversao_xml(
                    produto_id=produto_id,
                    codigo_barras=codigo_barras,
                    codigo_fornecedor=codigo_fornecedor,
                    tipo_compra=tipo_compra,
                    unidade_compra=unidade_compra,
                    unidade_estoque=unidade_estoque,
                    fator_conversao=fator_conversao,
                    ativo=ativo,
                    observacoes=observacoes
                )

                if sucesso:
                    st.success("Conversão cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao cadastrar conversão.")

    with abas[1]:

        st.subheader("📋 Conversões Cadastradas")

        df = listar_conversoes_xml()

        if df.empty:
            st.info("Nenhuma conversão cadastrada.")
        else:
            st.dataframe(
                df,
                use_container_width=True,
                height=500
            )

    with abas[2]:

        st.subheader("✏️ Editar Conversão")

        df = listar_conversoes_xml()

        if df.empty:
            st.info("Nenhuma conversão cadastrada para editar.")
        else:
            opcoes = {
                f"{row['id']} | {row['produto']} | {row['tipo_compra']} x {row['fator_conversao']}": row["id"]
                for _, row in df.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione a conversão",
                list(opcoes.keys())
            )

            conversao_id = opcoes[selecionado]
            row = df[df["id"] == conversao_id].iloc[0]

            with st.form("form_editar_conversao_xml"):

                produto_atual = None

                for nome, pid in produto_map.items():
                    if int(pid) == int(row["produto_id"]):
                        produto_atual = nome
                        break

                produto_nome = st.selectbox(
                    "Produto",
                    list(produto_map.keys()),
                    index=list(produto_map.keys()).index(produto_atual)
                    if produto_atual in produto_map else 0
                )

                produto_id = produto_map[produto_nome]

                col1, col2, col3 = st.columns(3)

                with col1:
                    tipo_compra = st.selectbox(
                        "Tipo comprado no XML",
                        tipos_compra,
                        index=tipos_compra.index(row["tipo_compra"])
                        if row["tipo_compra"] in tipos_compra else 0
                    )

                with col2:
                    unidade_compra = st.selectbox(
                        "Unidade de compra",
                        unidades,
                        index=unidades.index(row["unidade_compra"])
                        if row["unidade_compra"] in unidades else 0
                    )

                with col3:
                    unidade_estoque = st.selectbox(
                        "Unidade no estoque/venda",
                        unidades,
                        index=unidades.index(row["unidade_estoque"])
                        if row["unidade_estoque"] in unidades else 0
                    )

                fator_conversao = st.number_input(
                    "Fator de conversão",
                    min_value=0.001,
                    value=float(row["fator_conversao"] or 1),
                    step=1.000,
                    format="%.3f"
                )

                col4, col5 = st.columns(2)

                with col4:
                    codigo_barras = st.text_input(
                        "Código de barras / EAN",
                        value=str(row["codigo_barras"] or "")
                    )

                with col5:
                    codigo_fornecedor = st.text_input(
                        "Código do fornecedor",
                        value=str(row["codigo_fornecedor"] or "")
                    )

                ativo = st.checkbox(
                    "Conversão ativa",
                    value=bool(row["ativo"])
                )

                observacoes = st.text_area(
                    "Observações",
                    value=str(row["observacoes"] or "")
                )

                atualizar = st.form_submit_button(
                    "💾 Atualizar Conversão",
                    use_container_width=True
                )

                if atualizar:

                    sucesso = atualizar_conversao_xml(
                        conversao_id=conversao_id,
                        produto_id=produto_id,
                        codigo_barras=codigo_barras,
                        codigo_fornecedor=codigo_fornecedor,
                        tipo_compra=tipo_compra,
                        unidade_compra=unidade_compra,
                        unidade_estoque=unidade_estoque,
                        fator_conversao=fator_conversao,
                        ativo=ativo,
                        observacoes=observacoes
                    )

                    if sucesso:
                        st.success("Conversão atualizada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao atualizar conversão.")

    with abas[3]:

        st.subheader("🗑️ Excluir Conversão")

        df = listar_conversoes_xml()

        if df.empty:
            st.info("Nenhuma conversão cadastrada para excluir.")
        else:
            opcoes = {
                f"{row['id']} | {row['produto']} | {row['tipo_compra']} x {row['fator_conversao']}": row["id"]
                for _, row in df.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione a conversão para excluir",
                list(opcoes.keys())
            )

            conversao_id = opcoes[selecionado]

            confirmar = st.checkbox(
                "Confirmo que desejo excluir esta conversão",
                key="confirmar_excluir_conversao_xml"
            )

            if st.button(
                "🗑️ Excluir Conversão",
                use_container_width=True
            ):

                if not confirmar:
                    st.warning("Marque a confirmação antes de excluir.")
                    return

                sucesso = excluir_conversao_xml(conversao_id)

                if sucesso:
                    st.success("Conversão excluída com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao excluir conversão.")