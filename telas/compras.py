import streamlit as st
import pandas as pd

from database.connection import conectar
from services.xml_nfe_service import ler_xml_nfe
from database.xml_import_db import importar_nfe_xml
from services.xml_nfe_service import ler_xml_nfe

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

        return pd.read_sql(query, conn)

    except Exception as erro:
        st.error(f"Erro ao buscar fornecedores: {erro}")
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
        "📄 Importar XML NF-e",
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
            st.warning("Nenhum fornecedor cadastrado.")

        elif produtos_df.empty:
            st.warning("Nenhum produto cadastrado.")

        else:
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

                fornecedor_id = fornecedor_map[fornecedor_nome]

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

                    st.markdown(f"### Produto {i + 1}")

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

                    custo_padrao = produto_row.get("custo", 0)

                    if pd.isna(custo_padrao):
                        custo_padrao = 0

                    with col3:
                        custo = st.number_input(
                            f"Custo Unitário {i + 1}",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            value=float(custo_padrao),
                            key=f"custo_{i}"
                        )

                    subtotal = quantidade * custo
                    total_compra += subtotal

                    st.info(f"Subtotal: R$ {subtotal:,.2f}")

                    produtos_compra.append({
                        "produto_id": int(produto_row["id"]),
                        "quantidade": quantidade,
                        "custo": custo
                    })

                    st.divider()

                st.metric(
                    "💰 Total da Compra",
                    f"R$ {total_compra:,.2f}"
                )

                observacoes = st.text_area("Observações")

                salvar = st.form_submit_button(
                    "💾 Finalizar Compra",
                    use_container_width=True
                )

                if salvar:

                    sucesso = cadastrar_compra(
                        fornecedor_id=fornecedor_id,
                        produtos=produtos_compra,
                        usuario=st.session_state.get("usuario", "Sistema"),
                        observacoes=observacoes
                    )

                    if sucesso:
                        st.success("✅ Compra lançada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao lançar compra.")

    # ==================================================
    # IMPORTAR XML NF-E
    # ==================================================
    with abas[1]:

        st.subheader("📄 Importar XML NF-e")

        arquivo_xml = st.file_uploader(
            "Selecione o XML da NF-e",
            type=["xml"]
        )

        if arquivo_xml is None:
            st.info("Envie um arquivo XML de NF-e para iniciar a importação.")

        else:
            try:
                dados_xml = ler_xml_nfe(arquivo_xml)

                fornecedor = dados_xml["fornecedor"]
                produtos = dados_xml["produtos"]

                st.success("XML lido com sucesso.")

                st.markdown("### 🏢 Fornecedor")

                fornecedor_resumo = pd.DataFrame([{
                    "Razão Social": fornecedor.get("razao_social", ""),
                    "Nome Fantasia": fornecedor.get("nome_fantasia", ""),
                    "CNPJ": fornecedor.get("cnpj", ""),
                    "IE": fornecedor.get("inscricao_estadual", ""),
                    "Cidade": fornecedor.get("cidade", ""),
                    "UF": fornecedor.get("estado", "")
                }])

                st.dataframe(
                    fornecedor_resumo,
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("### 📦 Produtos da Nota")

                df_produtos_xml = pd.DataFrame(produtos)

                st.dataframe(
                    df_produtos_xml,
                    use_container_width=True,
                    hide_index=True
                )

                st.metric(
                    "Total da NF-e",
                    f"R$ {float(dados_xml['valor_total']):,.2f}"
                )

                confirmar_importacao = st.checkbox(
                    "Confirmo que desejo importar esta NF-e",
                    key="confirmar_importar_xml"
                )

                if st.button(
                    "📥 Importar NF-e",
                    use_container_width=True
                ):

                    if not confirmar_importacao:
                        st.warning("Marque a confirmação antes de importar.")

                    else:
                        sucesso = importar_nfe_xml(
                            dados_xml=dados_xml,
                            usuario=st.session_state.get("usuario", "Sistema")
                        )

                        if sucesso:
                            st.success("NF-e importada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao importar NF-e.")

            except Exception as erro:
                st.error(f"Erro ao ler XML: {erro}")

    # ==================================================
    # HISTÓRICO
    # ==================================================
    with abas[2]:

        st.subheader("📋 Histórico de Compras")

        compras = listar_compras()

        if compras.empty:
            st.info("Nenhuma compra cadastrada.")

        else:
            busca = st.text_input("🔎 Buscar fornecedor")

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

            if compras.empty:
                st.info("Nenhuma compra encontrada para o filtro informado.")

            else:
                compra_id = st.selectbox(
                    "Selecionar Compra",
                    compras["id"].tolist()
                )

                itens = buscar_itens_compra(compra_id)

                st.markdown("### 📦 Itens da Compra")

                st.dataframe(
                    itens,
                    use_container_width=True
                )

    # ==================================================
    # EXCLUIR COMPRA
    # ==================================================
    with abas[3]:

        st.subheader("🗑️ Excluir Compra")

        compras = listar_compras()

        if compras.empty:
            st.info("Nenhuma compra cadastrada.")

        else:
            compras_map = {
                f"{row['id']} | {row['fornecedor']} | R$ {float(row['valor_total']):,.2f}": row["id"]
                for _, row in compras.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione a compra",
                list(compras_map.keys())
            )

            compra_id = compras_map[selecionado]

            st.warning(
                "⚠️ A exclusão remove apenas o registro da compra. "
                "O estoque não será revertido."
            )

            confirmar = st.checkbox(
                "Confirmo que desejo excluir esta compra",
                key="confirmar_excluir_compra"
            )

            if st.button(
                "🗑️ Excluir Compra",
                use_container_width=True
            ):

                if not confirmar:
                    st.warning("Marque a confirmação antes de excluir.")

                else:
                    sucesso = excluir_compra(compra_id)

                    if sucesso:
                        st.success("✅ Compra excluída!")
                        st.rerun()
                    else:
                        st.error("Erro ao excluir compra.")