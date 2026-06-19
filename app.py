import streamlit as st
import sys
import os

# ==================================================
# PATH
# ==================================================
BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)

# ==================================================
# CONFIG STREAMLIT
# ==================================================
st.set_page_config(
    page_title="ERP Verde Infância",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# IMPORT DAS TELAS
# ==================================================
from telas.login import tela_login
from telas.dashboard import tela_dashboard
from telas.caixa import tela_caixa
from telas.clientes import tela_clientes
from telas.produtos import tela_produtos
from telas.vendas import tela_vendas
from telas.movimentacoes import tela_movimentacoes
from telas.fornecedores import tela_fornecedores
from telas.compras import tela_compras
from telas.contas_bancarias import tela_contas_bancarias
from telas.contas_pagar import tela_contas_pagar
from telas.contas_receber import tela_contas_receber
from telas.configuracoes import tela_configuracoes
from telas.fechamento_caixa import tela_fechamento_caixa
from telas.painel_admin_permissoes import tela_painel_permissoes
from telas.relatorios.financeiro_diario import tela_relatorios
from telas.marketing import tela_marketing
from telas.fluxo_caixa import tela_fluxo_caixa


# ==================================================
# CSS
# ==================================================
def carregar_css():
    caminho_css = os.path.join(BASE_DIR, "styles", "styles.css")

    if os.path.exists(caminho_css):
        with open(caminho_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


carregar_css()

# ==================================================
# SESSION STATE
# ==================================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

# ==================================================
# LOGIN
# ==================================================
if not st.session_state["logado"]:
    tela_login()
    st.stop()

# ==================================================
# PERFIL
# ==================================================
perfil = str(st.session_state.get("perfil", "")).lower()
admin_total = perfil in ["admin", "diretor"]

# ==================================================
# MENU
# ==================================================
menu_opcoes = ["🏠 Dashboard"]

if admin_total or st.session_state.get("pode_caixa"):
    menu_opcoes.append("💰 Caixa")

if admin_total or st.session_state.get("pode_clientes"):
    menu_opcoes.append("👥 Clientes")

if admin_total or st.session_state.get("pode_produtos"):
    menu_opcoes += [
        "📦 Produtos",
        "💰 Formação de Preço",
        "🚚 Fornecedores",
        "📥 Compras"
    ]

if admin_total or st.session_state.get("pode_movimentacoes"):
    menu_opcoes.append("💰 Movimentações")

if admin_total or st.session_state.get("pode_vendas"):
    menu_opcoes.append("🛒 Vendas")
    menu_opcoes.append("📢 Marketing")

if admin_total or st.session_state.get("pode_financeiro"):
    menu_opcoes.append("🏦 Contas Bancárias")
    menu_opcoes.append("📊 Fluxo de Caixa")

if admin_total or st.session_state.get("pode_contas_pagar"):
    menu_opcoes.append("📤 Contas a Pagar")

if admin_total or st.session_state.get("pode_contas_receber"):
    menu_opcoes.append("📥 Contas a Receber")

if admin_total or st.session_state.get("pode_relatorios"):
    menu_opcoes.append("📊 Relatórios")

if admin_total or st.session_state.get("pode_configuracoes"):
    menu_opcoes.append("⚙️ Configurações")

if admin_total or st.session_state.get("pode_fechamento_caixa"):
    menu_opcoes.append("📊 Fechamento de Caixa")

if admin_total:
    menu_opcoes.append("🔐 Permissões")

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.title("ERP Verde Infância")
    st.success(f"👤 {st.session_state.get('usuario', 'Usuário')}")

    menu = st.radio("Menu", menu_opcoes)

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# ==================================================
# BLOQUEIO
# ==================================================
def bloquear(permissao):
    if not (admin_total or st.session_state.get(permissao, False)):
        st.error("⛔ Sem permissão")
        st.stop()


# ==================================================
# ROTAS
# ==================================================
try:

    if menu == "🏠 Dashboard":
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

    elif menu == "💰 Formação de Preço":
        bloquear("pode_produtos")
        tela_produtos()

    elif menu == "🚚 Fornecedores":
        bloquear("pode_produtos")
        tela_fornecedores()

    elif menu == "📥 Compras":
        bloquear("pode_produtos")
        tela_compras()

    elif menu == "💰 Movimentações":
        bloquear("pode_movimentacoes")
        tela_movimentacoes()

    elif menu == "🛒 Vendas":
        bloquear("pode_vendas")
        tela_vendas()

    elif menu == "📢 Marketing":
        bloquear("pode_vendas")
        tela_marketing()

    elif menu == "🏦 Contas Bancárias":
        bloquear("pode_financeiro")
        tela_contas_bancarias()

    elif menu == "📊 Fluxo de Caixa":
        bloquear("pode_financeiro")
        tela_fluxo_caixa()

    elif menu == "📤 Contas a Pagar":
        bloquear("pode_contas_pagar")
        tela_contas_pagar()

    elif menu == "📥 Contas a Receber":
        bloquear("pode_contas_receber")
        tela_contas_receber()

    elif menu == "📊 Relatórios":
        bloquear("pode_relatorios")
        tela_relatorios()

    elif menu == "📊 Fechamento de Caixa":
        bloquear("pode_fechamento_caixa")
        tela_fechamento_caixa()

    elif menu == "⚙️ Configurações":
        bloquear("pode_configuracoes")
        tela_configuracoes()

    elif menu == "🔐 Permissões":
        tela_painel_permissoes()

except Exception as e:
    st.error("Erro geral na aplicação")
    st.exception(e)