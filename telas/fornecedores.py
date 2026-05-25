import streamlit as st
import pandas as pd

from database.fornecedores_db import (
    listar_fornecedores,
    cadastrar_fornecedor,
    atualizar_fornecedor,
    excluir_fornecedor
)


# ==================================================
# TELA FORNECEDORES ERP
# ==================================================
def tela_fornecedores():

    st.title("🚚 Fornecedores")

    abas = st.tabs([
        "➕ Novo Fornecedor",
        "📋 Lista",
        "✏️ Editar"
    ])

    # ==================================================
    # NOVO FORNECEDOR
    # ==================================================
    with abas[0]:

        with st.form(
            "form_fornecedor",
            clear_on_submit=True,
            enter_to_submit=False
        ):

            st.subheader(
                "Cadastro de Fornecedor"
            )

            col1, col2 = st.columns(2)

            with col1:

                razao_social = st.text_input(
                    "Razão Social"
                )

                nome_fantasia = st.text_input(
                    "Nome Fantasia"
                )

                cnpj = st.text_input(
                    "CNPJ"
                )

                inscricao_estadual = st.text_input(
                    "Inscrição Estadual"
                )

                telefone = st.text_input(
                    "Telefone"
                )

                email = st.text_input(
                    "Email"
                )

            with col2:

                endereco = st.text_input(
                    "Endereço"
                )

                numero = st.text_input(
                    "Número"
                )

                bairro = st.text_input(
                    "Bairro"
                )

                cidade = st.text_input(
                    "Cidade"
                )

                estado = st.text_input(
                    "Estado"
                )

                cep = st.text_input(
                    "CEP"
                )

            contato = st.text_input(
                "Contato Responsável"
            )

            observacoes = st.text_area(
                "Observações"
            )

            salvar = st.form_submit_button(
                "💾 Salvar Fornecedor",
                use_container_width=True
            )

            if salvar:

                if not razao_social.strip():

                    st.warning(
                        "Informe a razão social."
                    )

                else:

                    sucesso = cadastrar_fornecedor(
                        razao_social,
                        nome_fantasia,
                        cnpj,
                        inscricao_estadual,
                        telefone,
                        email,
                        endereco,
                        numero,
                        bairro,
                        cidade,
                        estado,
                        cep,
                        contato,
                        observacoes
                    )

                    if sucesso:

                        st.success(
                            "✅ Fornecedor cadastrado!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Erro ao cadastrar fornecedor."
                        )

    # ==================================================
    # LISTAGEM
    # ==================================================
    with abas[1]:

        st.subheader(
            "📋 Lista de Fornecedores"
        )

        busca = st.text_input(
            "🔎 Buscar fornecedor"
        )

        df = listar_fornecedores()

        if df.empty:

            st.info(
                "Nenhum fornecedor cadastrado."
            )

        else:

            if busca:

                busca = busca.lower()

                df = df[
                    df["razao_social"]
                    .astype(str)
                    .str.lower()
                    .str.contains(busca, na=False)
                ]

            st.dataframe(
                df,
                use_container_width=True,
                height=500
            )

    # ==================================================
    # EDITAR
    # ==================================================
    with abas[2]:

        st.subheader(
            "✏️ Editar Fornecedor"
        )

        df = listar_fornecedores()

        if df.empty:

            st.info(
                "Nenhum fornecedor cadastrado."
            )

            return

        fornecedores = {
            f"{row['id']} - {row['razao_social']}": row
            for _, row in df.iterrows()
        }

        selecionado = st.selectbox(
            "Selecione o fornecedor",
            list(fornecedores.keys())
        )

        fornecedor = fornecedores[selecionado]

        with st.form(
            "form_editar_fornecedor",
            enter_to_submit=False
        ):

            col1, col2 = st.columns(2)

            with col1:

                razao_social = st.text_input(
                    "Razão Social",
                    value=str(
                        fornecedor.get(
                            "razao_social",
                            ""
                        )
                    )
                )

                nome_fantasia = st.text_input(
                    "Nome Fantasia",
                    value=str(
                        fornecedor.get(
                            "nome_fantasia",
                            ""
                        )
                    )
                )

                cnpj = st.text_input(
                    "CNPJ",
                    value=str(
                        fornecedor.get(
                            "cnpj",
                            ""
                        )
                    )
                )

                inscricao_estadual = st.text_input(
                    "Inscrição Estadual",
                    value=str(
                        fornecedor.get(
                            "inscricao_estadual",
                            ""
                        )
                    )
                )

                telefone = st.text_input(
                    "Telefone",
                    value=str(
                        fornecedor.get(
                            "telefone",
                            ""
                        )
                    )
                )

                email = st.text_input(
                    "Email",
                    value=str(
                        fornecedor.get(
                            "email",
                            ""
                        )
                    )
                )

            with col2:

                endereco = st.text_input(
                    "Endereço",
                    value=str(
                        fornecedor.get(
                            "endereco",
                            ""
                        )
                    )
                )

                numero = st.text_input(
                    "Número",
                    value=str(
                        fornecedor.get(
                            "numero",
                            ""
                        )
                    )
                )

                bairro = st.text_input(
                    "Bairro",
                    value=str(
                        fornecedor.get(
                            "bairro",
                            ""
                        )
                    )
                )

                cidade = st.text_input(
                    "Cidade",
                    value=str(
                        fornecedor.get(
                            "cidade",
                            ""
                        )
                    )
                )

                estado = st.text_input(
                    "Estado",
                    value=str(
                        fornecedor.get(
                            "estado",
                            ""
                        )
                    )
                )

                cep = st.text_input(
                    "CEP",
                    value=str(
                        fornecedor.get(
                            "cep",
                            ""
                        )
                    )
                )

            contato = st.text_input(
                "Contato Responsável",
                value=str(
                    fornecedor.get(
                        "contato_responsavel",
                        ""
                    )
                )
            )

            observacoes = st.text_area(
                "Observações",
                value=str(
                    fornecedor.get(
                        "observacoes",
                        ""
                    )
                )
            )

            col_btn1, col_btn2 = st.columns(2)

            with col_btn1:

                salvar = st.form_submit_button(
                    "💾 Salvar Alterações",
                    use_container_width=True
                )

            with col_btn2:

                excluir = st.form_submit_button(
                    "🗑️ Excluir Fornecedor",
                    use_container_width=True
                )

            # ==========================================
            # SALVAR
            # ==========================================
            if salvar:

                sucesso = atualizar_fornecedor(
                    fornecedor["id"],
                    razao_social,
                    nome_fantasia,
                    cnpj,
                    inscricao_estadual,
                    telefone,
                    email,
                    endereco,
                    numero,
                    bairro,
                    cidade,
                    estado,
                    cep,
                    contato,
                    observacoes
                )

                if sucesso:

                    st.success(
                        "✅ Fornecedor atualizado!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Erro ao atualizar fornecedor."
                    )

            # ==========================================
            # EXCLUIR
            # ==========================================
            if excluir:

                sucesso = excluir_fornecedor(
                    fornecedor["id"]
                )

                if sucesso:

                    st.success(
                        "🗑️ Fornecedor excluído!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Erro ao excluir fornecedor."
                    )