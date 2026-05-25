import streamlit as st
import pandas as pd

from database.connection import conectar

from database.compras_db import (
    cadastrar_compra,
    listar_compras,
    buscar_itens_compra,
    excluir_compra
)

from database.produto_db import listar_produtos


# ==================================================
# BUSCAR FORNECEDORES
# ==================================================
def buscar_fornecedores():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                razao_social
            FROM fornecedores
            ORDER BY razao_social
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        st.error(
            f"Erro ao buscar fornecedores: {erro}"
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# TELA COMPRAS ERP
# ==================================================
def tela_compras():

    st.title("📦 Compras ERP")

    abas = st.tabs([
        "➕ Nova Compra",
        "📋 Histórico",
        "🗑️ Excluir Compra"
    ])

    # ==================================================
    # NOVA COMPRA
    # ==================================================
    with abas[0]:

        st.subheader("📦 Lançar Compra")

        fornecedores = buscar_fornecedores()

        produtos_df = listar_produtos()

        if fornecedores.empty:

            st.warning(
                "Nenhum fornecedor cadastrado."
            )

            return

        if produtos_df.empty:

            st.warning(
                "Nenhum produto cadastrado."
            )

            return

        fornecedor_map = {
            row["razao_social"]: row["id"]
            for _, row in fornecedores.iterrows()
        }

        with st.form(
            "form_compra",
            clear_on_submit=True,
            enter_to_submit=False
        ):

            fornecedor_nome = st.selectbox(
                "Fornecedor",
                list(fornecedor_map.keys())
            )

            fornecedor_id = fornecedor_map[
                fornecedor_nome
            ]

            st.divider()

            quantidade_itens = st.number_input(
                "Quantidade de Itens",
                min_value=1,
                max_value=50,
                value=1,
                step=1
            )

            st.divider()

            produtos_compra = []

            total_compra = 0

            for i in range(int(quantidade_itens)):

                st.markdown(
                    f"### Produto {i + 1}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:

                    produto_nome = st.selectbox(
                        f"Produto {i + 1}",
                        produtos_df["nome"].tolist(),
                        key=f"produto_{i}"
                    )

                produto_row = produtos_df[
                    produtos_df["nome"] == produto_nome
                ].iloc[0]

                with col2:

                    quantidade = st.number_input(
                        f"Quantidade {i + 1}",
                        min_value=0.001,
                        step=1.0,
                        format="%.3f",
                        key=f"quantidade_{i}"
                    )

                with col3:

                    custo = st.number_input(
                        f"Custo Unitário {i + 1}",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        value=float(
                            produto_row.get(
                                "custo",
                                0
                            )
                        ),
                        key=f"custo_{i}"
                    )

                subtotal = quantidade * custo

                total_compra += subtotal

                st.info(
                    f"Subtotal: R$ {subtotal:,.2f}"
                )

                produtos_compra.append({

                    "produto_id": int(
                        produto_row["id"]
                    ),

                    "quantidade": quantidade,

                    "custo": custo

                })

                st.divider()

            st.metric(
                "💰 Total da Compra",
                f"R$ {total_compra:,.2f}"
            )

            observacoes = st.text_area(
                "Observações"
            )

            salvar = st.form_submit_button(
                "💾 Finalizar Compra",
                use_container_width=True
            )

            if salvar:

                sucesso = cadastrar_compra(

                    fornecedor_id=fornecedor_id,

                    produtos=produtos_compra,

                    usuario=st.session_state.get(
                        "usuario",
                        "Sistema"
                    ),

                    observacoes=observacoes

                )

                if sucesso:

                    st.success(
                        "✅ Compra lançada com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Erro ao lançar compra."
                    )

    # ==================================================
    # HISTÓRICO
    # ==================================================
    with abas[1]:

        st.subheader(
            "📋 Histórico de Compras"
        )

        compras = listar_compras()

        if compras.empty:

            st.info(
                "Nenhuma compra cadastrada."
            )

            return

        busca = st.text_input(
            "🔎 Buscar fornecedor"
        )

        if busca:

            compras = compras[
                compras["fornecedor"]
                .astype(str)
                .str.contains(
                    busca,
                    case=False,
                    na=False
                )
            ]

        st.dataframe(
            compras,
            use_container_width=True,
            height=400
        )

        st.divider()

        compra_id = st.selectbox(
            "Selecionar Compra",
            compras["id"].tolist()
        )

        itens = buscar_itens_compra(
            compra_id
        )

        st.markdown("### 📦 Itens da Compra")

        st.dataframe(
            itens,
            use_container_width=True
        )

    # ==================================================
    # EXCLUIR COMPRA
    # ==================================================
    with abas[2]:

        st.subheader(
            "🗑️ Excluir Compra"
        )

        compras = listar_compras()

        if compras.empty:

            st.info(
                "Nenhuma compra cadastrada."
            )

            return

        compras_map = {

            f"{row['id']} | {row['fornecedor']} | R$ {row['valor_total']}":

            row["id"]

            for _, row in compras.iterrows()
        }

        selecionado = st.selectbox(
            "Selecione a compra",
            list(compras_map.keys())
        )

        compra_id = compras_map[
            selecionado
        ]

        st.warning(
            "⚠️ A exclusão remove apenas o registro da compra. "
            "O estoque não será revertido."
        )

        if st.button(
            "🗑️ Excluir Compra",
            use_container_width=True
        ):

            sucesso = excluir_compra(
                compra_id
            )

            if sucesso:

                st.success(
                    "✅ Compra excluída!"
                )

                st.rerun()

            else:

                st.error(
                    "Erro ao excluir compra."
                )