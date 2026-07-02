import streamlit as st
import pandas as pd

from database.connection import conectar
from services.xml_nfe_service import ler_xml_nfe

from services.xml_conversao_service import (
    detectar_conversao_por_descricao,
    aplicar_conversao_produto
)

from services.xml_import_db import (
    importar_nfe_xml,
    buscar_produto_por_codigo,
    buscar_conversao_produto
)

from database.compras_db import (
    cadastrar_compra,
    listar_compras,
    buscar_itens_compra,
    excluir_compra
)

from database.produto_db import listar_produtos


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


def gerar_previa_conversao_xml(dados_xml):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    cursor = conn.cursor()

    try:
        linhas = []

        for item in dados_xml.get("produtos", []):

            nome = item.get("nome", "")
            codigo_barras = item.get("ean", "")
            codigo_fornecedor = item.get("codigo", "")
            unidade_xml = item.get("unidade", "")

            quantidade_xml = float(item.get("quantidade", 0) or 0)
            custo_xml = float(item.get("custo", 0) or 0)
            subtotal_xml = float(
                item.get("subtotal", quantidade_xml * custo_xml) or 0
            )

            produto_id = buscar_produto_por_codigo(
                cursor,
                codigo_barras,
                codigo_fornecedor
            )

            if produto_id is None:
                cursor.execute("""
                    SELECT id
                    FROM produtos
                    WHERE LOWER(TRIM(nome)) = LOWER(TRIM(%s))
                    LIMIT 1
                """, (nome,))

                encontrado = cursor.fetchone()

                if encontrado:
                    produto_id = encontrado[0]

            conversao = buscar_conversao_produto(
                cursor,
                produto_id,
                codigo_barras,
                codigo_fornecedor
            )

            origem_conversao = "Cadastrada"

            if float(conversao.get("fator_conversao", 1) or 1) == 1:
                conversao_detectada = detectar_conversao_por_descricao(nome)

                if conversao_detectada.get("detectado"):
                    conversao = conversao_detectada
                    origem_conversao = "Detectada automaticamente"
                else:
                    origem_conversao = "Padrão"

            dados_conversao = aplicar_conversao_produto(
                quantidade_xml=quantidade_xml,
                custo_xml=custo_xml,
                subtotal_xml=subtotal_xml,
                conversao=conversao
            )

            linhas.append({
                "Produto XML": nome,
                "Produto cadastrado": "Sim" if produto_id else "Não",
                "Código Barras": codigo_barras,
                "Código Fornecedor": codigo_fornecedor,
                "Unidade XML": unidade_xml,
                "Origem Conversão": origem_conversao,
                "Tipo Compra": dados_conversao["tipo_compra"],
                "Qtd XML": quantidade_xml,
                "Fator": dados_conversao["fator_conversao"],
                "Qtd Estoque": dados_conversao["quantidade_estoque"],
                "Unidade Estoque": dados_conversao["unidade_estoque"],
                "Custo XML": custo_xml,
                "Custo Unitário Final": dados_conversao["custo_unitario_estoque"],
                "Subtotal": subtotal_xml
            })

        return pd.DataFrame(linhas)

    except Exception as erro:
        print("Erro gerar_previa_conversao_xml:", erro)
        return pd.DataFrame()

    finally:
        cursor.close()
        conn.close()


def tela_compras():

    st.title("📦 Compras ERP")

    abas = st.tabs([
        "➕ Nova Compra",
        "📄 Importar XML NF-e",
        "📋 Histórico",
        "🗑️ Excluir Compra"
    ])

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

                st.success("✅ XML lido com sucesso.")

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    st.metric(
                        "Número NF-e",
                        dados_xml.get("numero_nfe", "")
                    )

                with col_b:
                    st.metric(
                        "Produtos",
                        len(produtos)
                    )

                with col_c:
                    st.metric(
                        "Total da NF-e",
                        f"R$ {float(dados_xml['valor_total']):,.2f}"
                    )

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

                st.markdown("### 🧠 Conferência Inteligente da Conversão")

                df_previa = gerar_previa_conversao_xml(dados_xml)

                if df_previa.empty:
                    st.warning("Não foi possível gerar a prévia de conversão.")
                else:
                    st.dataframe(
                        df_previa,
                        use_container_width=True,
                        hide_index=True
                    )

                    sem_cadastro = df_previa[
                        df_previa["Produto cadastrado"] == "Não"
                    ]

                    sem_conversao = df_previa[
                        df_previa["Fator"] == 1.0
                    ]

                    conversao_detectada = df_previa[
                        df_previa["Origem Conversão"] == "Detectada automaticamente"
                    ]

                    if not sem_cadastro.empty:
                        st.warning(
                            f"{len(sem_cadastro)} produto(s) ainda não estão cadastrados. "
                            "Eles serão criados automaticamente."
                        )

                    if not conversao_detectada.empty:
                        st.success(
                            f"{len(conversao_detectada)} conversão(ões) foram detectadas automaticamente pela descrição."
                        )

                    if not sem_conversao.empty:
                        st.info(
                            f"{len(sem_conversao)} item(ns) estão com fator 1. "
                            "Se algum produto veio em caixa, pacote ou fardo e não foi detectado, cadastre a conversão antes de importar."
                        )

                st.warning(
                    "Ao confirmar, o ERP irá registrar a compra, atualizar estoque, "
                    "atualizar custos, criar histórico de custo e criar lotes de estoque."
                )

                confirmar_importacao = st.checkbox(
                    "Confirmo que conferi as conversões e desejo importar esta NF-e",
                    key=f"confirmar_importar_xml_{dados_xml.get('chave_nfe', '')}"
                )

                if st.button(
                    "📥 Importar NF-e",
                    use_container_width=True,
                    disabled=not confirmar_importacao
                ):

                    with st.spinner("Importando XML e atualizando estoque..."):

                        resultado = importar_nfe_xml(
                            dados_xml=dados_xml,
                            usuario=st.session_state.get("usuario", "Sistema")
                        )

                    if resultado.get("sucesso"):

                        st.success("✅ NF-e importada com sucesso!")

                        st.markdown("### 📌 Resumo da Importação")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Compra Nº",
                                resultado.get("compra_id", "")
                            )

                        with col2:
                            st.metric(
                                "NF-e",
                                resultado.get("numero_nfe", "")
                            )

                        with col3:
                            st.metric(
                                "Valor Total",
                                f"R$ {float(resultado.get('valor_total', 0)):,.2f}"
                            )

                        col4, col5, col6 = st.columns(3)

                        with col4:
                            st.metric(
                                "Produtos na Nota",
                                resultado.get("total_produtos", 0)
                            )

                        with col5:
                            st.metric(
                                "Produtos Novos",
                                resultado.get("produtos_novos", 0)
                            )

                        with col6:
                            st.metric(
                                "Produtos Atualizados",
                                resultado.get("produtos_atualizados", 0)
                            )

                        st.info(
                            f"Fornecedor: {resultado.get('fornecedor', '')}"
                        )

                        itens_convertidos = resultado.get(
                            "itens_convertidos",
                            []
                        )

                        if itens_convertidos:
                            st.markdown("### 🔁 Itens Convertidos")

                            st.dataframe(
                                pd.DataFrame(itens_convertidos),
                                use_container_width=True,
                                hide_index=True
                            )

                        st.success(
                            "Estoque, custos, histórico de custos e lotes foram atualizados com sucesso."
                        )

                    elif resultado.get("duplicada"):

                        st.warning("⚠️ Esta NF-e já foi importada anteriormente.")

                        st.markdown("### 📌 Dados da importação existente")

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric(
                                "Compra Nº",
                                resultado.get("compra_id", "")
                            )

                        with col2:
                            st.metric(
                                "NF-e",
                                resultado.get("numero_nfe", "")
                            )

                        with col3:
                            st.metric(
                                "Fornecedor",
                                resultado.get("fornecedor", "")
                            )

                        st.info(
                            f"Chave NF-e: {resultado.get('chave_nfe', '')}"
                        )

                        st.warning(
                            "Nenhuma alteração foi realizada no estoque, custos ou compras."
                        )

                    else:
                        st.error(resultado.get(
                            "mensagem",
                            "Erro ao importar NF-e."
                        ))

            except Exception as erro:
                st.error(f"Erro ao ler XML: {erro}")

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