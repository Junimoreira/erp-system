import streamlit as st


def tela_configuracoes():

    #st.title("⚙️ Configurações")

    abas = st.tabs([
        "🏢 Empresa",
        "👤 Usuários",
        "💰 Financeiro",
        "🎨 Aparência"
    ])

    with abas[0]:

        st.subheader("Dados da Empresa")

        nome = st.text_input("Nome da empresa")
        cnpj = st.text_input("CNPJ")
        telefone = st.text_input("Telefone")

        if st.button("Salvar Dados"):
            st.success("Dados salvos com sucesso!")

    with abas[1]:

        st.subheader("Usuários")

        st.info("Área de gerenciamento de usuários.")

    with abas[2]:

        st.subheader("Financeiro")

        desconto = st.number_input(
            "Desconto máximo (%)",
            0,
            100
        )

    with abas[3]:

        st.subheader("Aparência")

        tema = st.selectbox(
            "Tema",
            ["Claro", "Escuro"]
        )