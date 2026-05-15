import streamlit as st

# =========================
# TELAS
# =========================
from telas.clientes import tela_clientes
from telas.produtos import tela_produtos
from telas.vendas import tela_vendas
from telas.configuracoes import tela_configuracoes
from telas.login import tela_login
from telas.contas import tela_contas
from telas.movimentacoes import tela_movimentacoes
from telas.contas_pagar import tela_contas_pagar
from telas.contas_receber import tela_contas_receber

# =========================
# DATABASE
# =========================
from database.dashboard_db import obter_dashboard

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
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
# SISTEMA PRINCIPAL
# =========================
else:

    # =========================
    # SIDEBAR
    # =========================
    with st.sidebar:

        st.success(f"👤 {st.session_state['usuario']}")
        st.divider()

        menu = st.radio(
            "Menu",
            [
                "🏠 Dashboard",
                "👥 Clientes",
                "📦 Produtos",
                "💰 Movimentações",
                "🛒 Vendas",
                "🏦 Contas",
                "📤 Contas a Pagar",
                "📥 Contas a Receber",
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

        col1.metric("💰 Entradas", f"R$ {dados['entradas']:,.2f}")
        col2.metric("👥 Clientes", dados["clientes"])
        col3.metric("📦 Produtos", dados["produtos"])
        col4.metric("🏦 Saldo", f"R$ {dados['saldo']:,.2f}")

    # =========================
    # CLIENTES
    # =========================
    elif menu == "👥 Clientes":
        tela_clientes()

    # =========================
    # PRODUTOS
    # =========================
    elif menu == "📦 Produtos":
        tela_produtos()

    # =========================
    # MOVIMENTAÇÕES
    # =========================
    elif menu == "💰 Movimentações":
        tela_movimentacoes()

    # =========================
    # VENDAS
    # =========================
    elif menu == "🛒 Vendas":
        tela_vendas()

    # =========================
    # CONTAS
    # =========================
    elif menu == "🏦 Contas":
        tela_contas()

    #===========================
    # CONTAS A PAGAR
    #===========================
    elif menu == "📤 Contas a Pagar":   # 👈 NOVO LINK
        tela_contas_pagar()

    #==========================
    # CONTAS A RECEBER
    #==========================
    elif menu == "📥 Contas a Receber":
        tela_contas_receber()




    # =========================
    # CONFIGURAÇÕES
    # =========================
    elif menu == "⚙️ Configurações":
        tela_configuracoes()