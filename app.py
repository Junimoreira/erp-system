import streamlit as st

from telas.login import tela_login
from telas.clientes import tela_clientes
from telas.produtos import tela_produtos
from telas.financeiro import tela_financeiro

st.set_page_config(
    page_title="ERP Empresarial",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# SESSÃO
# =========================

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""

# =========================
# LOGIN
# =========================

if not st.session_state["logado"]:

    tela_login()

# =========================
# SISTEMA
# =========================

else:

    # SIDEBAR

    with st.sidebar:

        st.success(
            f"👤 {st.session_state['usuario']}"
        )

        st.divider()

        menu = st.radio(
            "Menu",
            [
                "🏠 Dashboard",
                "👥 Clientes",
                "📦 Produtos",
                "💰 Financeiro",
                "🛒 Vendas",
                "⚙️ Configurações"
            ]
        )

        st.divider()

        if st.button("🚪 Sair"):

            st.session_state["logado"] = False
            st.session_state["usuario"] = ""

            st.rerun()

    # =========================
    # DASHBOARD
    # =========================

    if menu == "🏠 Dashboard":

        st.title("🚀 ERP Empresarial")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Vendas Hoje",
            "R$ 0,00"
        )

        col2.metric(
            "Clientes",
            "0"
        )

        col3.metric(
            "Produtos",
            "0"
        )

        col4.metric(
            "Caixa",
            "R$ 0,00"
        )

        st.divider()

        st.info("Sistema ERP online funcionando.")

    # =========================
    # CLIENTES
    # =========================

    elif menu == "👥 Clientes":

        st.title("👥 Clientes")
        #from telas.clientes import tela_clientes
        tela_clientes()
    # =========================
    # PRODUTOS
    # =========================

    elif menu == "📦 Produtos":

        st.title("📦 Produtos")

        st.write("Tela de produtos.")
        tela_produtos()

    # =========================
    # FINANCEIRO
    # =========================

    elif menu == "💰 Financeiro":

        st.title("💰 Financeiro")

        st.write("Tela financeira.")
        tela_financeiro()

    # =========================
    # VENDAS
    # =========================

    elif menu == "🛒 Vendas":

        st.title("🛒 Vendas")

        st.write("Tela de vendas.")

    # =========================
    # CONFIGURAÇÕES
    # =========================

    elif menu == "⚙️ Configurações":

        st.title("⚙️ Configurações")

        st.write("Configurações do sistema.")