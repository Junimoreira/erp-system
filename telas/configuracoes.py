import streamlit as st

from database.empresa_db import buscar_empresa, salvar_empresa
from database.configuracoes_db import (
    buscar_configuracoes_financeiras,
    salvar_configuracoes_financeiras
)


# ==================================================
# TELA CONFIGURAÇÕES
# ==================================================
def tela_configuracoes():

    abas = st.tabs([
        "🏢 Empresa",
        "👥 Usuários",
        "💰 Financeiro",
        "🎨 Aparência"
    ])

    # ==================================================
    # EMPRESA
    # ==================================================
    with abas[0]:

        st.subheader("🏢 Dados da Empresa")

        empresa = buscar_empresa()

        nome_default = empresa["nome"] if empresa else ""
        cnpj_default = empresa["cnpj"] if empresa else ""
        tel_default = empresa["telefone"] if empresa else ""
        end_default = empresa["endereco"] if empresa else ""
        email_default = empresa["email"] if empresa else ""

        nome_empresa = st.text_input("Nome da Empresa", value=nome_default)
        cnpj = st.text_input("CNPJ", value=cnpj_default)
        telefone = st.text_input("Telefone", value=tel_default)
        endereco = st.text_area("Endereço", value=end_default)
        email = st.text_input("E-mail", value=email_default)

        logo = st.file_uploader("Logo da Empresa", type=["png", "jpg", "jpeg"])

        # ==================================================
        # PREVIEW DO BANCO
        # ==================================================
        if empresa:

            st.info("📌 Dados já cadastrados no sistema")

            st.write("Nome:", empresa.get("nome"))
            st.write("CNPJ:", empresa.get("cnpj"))
            st.write("Telefone:", empresa.get("telefone"))

            # ==================================================
            # CORREÇÃO DO ERRO memoryview → bytes
            # ==================================================
            if empresa.get("logo"):

                try:
                    logo_bytes = bytes(empresa["logo"])
                    st.image(logo_bytes, caption="Logo atual", width=150)

                except Exception as e:
                    st.warning("Logo encontrada, mas não foi possível exibir.")
                    print("Erro logo:", e)

        st.divider()

        if st.button("💾 Salvar Dados Empresa"):

            logo_bytes = logo.read() if logo else (
                empresa["logo"] if empresa else None
            )

            salvar_empresa(
                nome_empresa,
                cnpj,
                telefone,
                endereco,
                email,
                logo_bytes
            )

            st.success("✅ Empresa salva com sucesso!")
            st.rerun()

    # ==================================================
    # USUÁRIOS
    # ==================================================
    with abas[1]:

        st.subheader("👥 Usuários do Sistema")

        st.info("Módulo de usuários será implementado futuramente.")

    # ==================================================
    # FINANCEIRO
    # ==================================================
    with abas[2]:

        st.subheader("💰 Configurações Financeiras")

        config = buscar_configuracoes_financeiras()

        imposto_padrao = 0.0
        frete_padrao = 0.0
        taxa_cartao_padrao = 0.0
        margem_padrao = 30.0
        desconto_max_padrao = 0.0

        if config is not None:

            imposto_padrao = float(config.get("imposto_padrao", 0.0))
            frete_padrao = float(config.get("frete_padrao", 0.0))
            taxa_cartao_padrao = float(config.get("taxa_cartao_padrao", 0.0))
            margem_padrao = float(config.get("margem_lucro_padrao", 30.0))
            desconto_max_padrao = float(config.get("desconto_maximo", 0.0))

        st.divider()

        imposto = st.number_input("Imposto Padrão (%)", min_value=0.0, value=imposto_padrao, format="%.2f")
        frete = st.number_input("Frete Padrão (%)", min_value=0.0, value=frete_padrao, format="%.2f")
        taxa_cartao = st.number_input("Taxa Cartão (%)", min_value=0.0, value=taxa_cartao_padrao, format="%.2f")
        margem = st.number_input("Margem Lucro Padrão (%)", min_value=0.0, value=margem_padrao, format="%.2f")
        desconto_maximo = st.number_input("Desconto Máximo (%)", min_value=0.0, max_value=100.0, value=desconto_max_padrao, format="%.2f")

        st.divider()

        st.info("Esses parâmetros são usados na precificação automática dos produtos.")

        if st.button("💾 Salvar Configurações Financeiras"):

            sucesso = salvar_configuracoes_financeiras(
                imposto=imposto,
                frete=frete,
                taxa_cartao=taxa_cartao,
                margem=margem,
                desconto_maximo=desconto_maximo
            )

            if sucesso:
                st.success("✅ Configurações salvas com sucesso!")
                st.rerun()
            else:
                st.error("❌ Erro ao salvar configurações.")

    # ==================================================
    # APARÊNCIA
    # ==================================================
    with abas[3]:

        st.subheader("🎨 Aparência do Sistema")

        tema = st.selectbox("Tema", ["Claro", "Escuro"])
        cor = st.color_picker("Cor Principal", "#1f77b4")

        st.divider()

        if st.button("💾 Salvar Aparência"):
            st.success("✅ Aparência salva com sucesso!")