import streamlit as st

#from telas.dashboard import tela_dashboard
from telas.clientes import tela_clientes
from telas.produtos import tela_produtos
from telas.financeiro import tela_financeiro
from telas.vendas import tela_vendas
#from telas.configuracoes import tela_configuracoes
from telas.login import tela_login
from database.dashboard_db import obter_dashboard

st.set_page_config(
    page_title="ERP Empresarial",
    layout="wide",
    initial_sidebar_state="expanded"
)

col1, col2 = st.columns(2)
use_container_width=True

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

        dados = obter_dashboard()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
        "💰 Entradas",
        f"R$ {dados['entradas']:,.2f}"
    )

        col2.metric(
        "👥 Clientes",
        dados["clientes"]
    )

        col3.metric(
        "📦 Produtos",
        dados["produtos"]
    )

        col4.metric(
        "🏦 Saldo",
        f"R$ {dados['saldo']:,.2f}"
    )

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

        #st.write("Tela de produtos.")
        tela_produtos()

    # =========================
    # FINANCEIRO
    # =========================

    elif menu == "💰 Financeiro":

        st.title("💰 Financeiro")

        #st.write("Tela financeira.")
        tela_financeiro()

    # =========================
    # VENDAS
    # =========================

    elif menu == "🛒 Vendas":

        st.title("🛒 Vendas")

        #st.write("Tela de vendas.")
        tela_vendas()

    # =========================
    # CONFIGURAÇÕES
    # =========================

    elif menu == "⚙️ Configurações":

        st.title("⚙️ Configurações")

        st.write("Configurações do sistema.")
	tela_configuracoes()
