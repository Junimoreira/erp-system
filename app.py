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
from telas.dashboard import tela_dashboard
from telas.despesas import tela_despesas
from telas.caixa import tela_caixa


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
                "💰 Caixa",
                "👥 Clientes",
                "📦 Produtos",
                "💰 Movimentações",
                "🛒 Vendas",
                "💸 Despesas",
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

        tela_dashboard()

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

    #==========================
    # DESPESAS
    #==========================
    elif menu == "💸 Despesas":
        tela_despesas()
    #=========================
    #CAIXA
    #=========================
    elif menu == "💰 Caixa":
        tela_caixa()
    

    # =========================
    # CONFIGURAÇÕES
    # =========================
    elif menu == "⚙️ Configurações":
        tela_configuracoes()