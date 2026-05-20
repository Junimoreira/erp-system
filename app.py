import streamlit as st


# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="ERP Verde Infância",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# CSS GLOBAL
# =========================
with open("styles/styles.css", encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )


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
# SESSÃO
# =========================
if "logado" not in st.session_state:
    st.session_state["logado"] = False


# =========================
# LOGIN
# =========================
if not st.session_state["logado"]:
    tela_login()
    st.stop()


# =========================
# MENU BASE (COM PERMISSÕES)
# =========================
menu_opcoes = []

if st.session_state.get("pode_dashboard"):
    menu_opcoes.append("🏠 Dashboard")

if st.session_state.get("pode_caixa"):
    menu_opcoes.append("💰 Caixa")

if st.session_state.get("pode_clientes"):
    menu_opcoes.append("👥 Clientes")

if st.session_state.get("pode_produtos"):
    menu_opcoes.append("📦 Produtos")

menu_opcoes.append("💰 Movimentações")

if st.session_state.get("pode_vendas"):
    menu_opcoes.append("🛒 Vendas")

if st.session_state.get("pode_despesas"):
    menu_opcoes.append("💸 Despesas")

menu_opcoes.append("🏦 Contas")

if st.session_state.get("pode_contas_pagar"):
    menu_opcoes.append("📤 Contas a Pagar")

if st.session_state.get("pode_contas_receber"):
    menu_opcoes.append("📥 Contas a Receber")

if st.session_state.get("pode_configuracoes"):
    menu_opcoes.append("⚙️ Configurações")


# =========================
# SISTEMA PRINCIPAL
# =========================
with st.sidebar:

    st.image("assets/Logo.png", width=180)

    st.markdown(
        """
        <div class="sidebar-title">
            ERP Verde Infância
        </div>
        """,
        unsafe_allow_html=True
    )

    st.success(f"👤 {st.session_state['usuario']}")

    st.divider()

    menu = st.radio("Menu", menu_opcoes)

    st.divider()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


# =========================
# PROTEÇÃO DE ACESSO
# =========================
def bloquear(permissao):
    if not st.session_state.get(permissao, False):
        st.error("⛔ Você não tem permissão para acessar esta área.")
        st.stop()


# =========================
# ROTAS
# =========================
if menu == "🏠 Dashboard":
    bloquear("pode_dashboard")
    tela_dashboard()

elif menu == "💰 Caixa":
    bloquear("pode_caixa")
    tela_caixa()

elif menu == "👥 Clientes":
    bloquear("pode_clientes")
    tela_clientes()

elif menu == "📦 Produtos":
    bloquear("pode_produtos")
    tela_produtos()

elif menu == "💰 Movimentações":
    tela_movimentacoes()

elif menu == "🛒 Vendas":
    bloquear("pode_vendas")
    tela_vendas()

elif menu == "💸 Despesas":
    bloquear("pode_despesas")
    tela_despesas()

elif menu == "🏦 Contas":
    tela_contas()

elif menu == "📤 Contas a Pagar":
    bloquear("pode_contas_pagar")
    tela_contas_pagar()

elif menu == "📥 Contas a Receber":
    bloquear("pode_contas_receber")
    tela_contas_receber()

elif menu == "⚙️ Configurações":
    bloquear("pode_configuracoes")
    tela_configuracoes()