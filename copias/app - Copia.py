import streamlit as st


# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(
    page_title="ERP Verde Infância",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# CSS GLOBAL
# =========================
try:
    with open("styles/styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass


# =========================
# IMPORTAÇÃO DAS TELAS
# =========================
from telas.painel_admin_permissoes import tela_painel_permissoes

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
# SUPER USUÁRIO
# =========================
#perfil = st.session_state.get("perfil")

#if perfil in ["admin", "diretor"]:
 #   st.session_state["abrir_caixa"] = True
  #  st.session_state["cadastrar_cliente"] = True
    #st.session_state["cadastrar_produto"] = True
    #st.session_state["realizar_venda"] = True
    #st.session_state["ver_financeiro"] = True
    #st.session_state["contas_pagar"] = True
    #st.session_state["configuracoes"] = True
    #st.session_state["usuarios"] = True

    if st.session_state.get("usuarios"):
        menu_opcoes.append("🔐 Permissões")



# =========================
# PERMISSÕES PADRÃO (EVITA BUGS)
# =========================
permissoes_padrao = [
    "abrir_caixa",
    "cadastrar_cliente",
    "cadastrar_produto",
    "realizar_venda",
    "ver_financeiro",
    "contas_pagar",
    "configuracoes",
    "usuarios"
]

for p in permissoes_padrao:
    if p not in st.session_state:
        st.session_state[p] = False


# =========================
# SUPER USUÁRIO (ADMIN/DIRETOR)
# =========================
perfil = st.session_state.get("perfil")

if perfil in ["admin", "diretor"]:
    for p in permissoes_padrao:
        st.session_state[p] = True


# =========================
# MENU BASE (CORRETO)
# =========================
menu_opcoes = []

menu_opcoes.append("🏠 Dashboard")

if st.session_state.get("abrir_caixa"):
    menu_opcoes.append("💰 Caixa")

if st.session_state.get("cadastrar_cliente"):
    menu_opcoes.append("👥 Clientes")

if st.session_state.get("cadastrar_produto"):
    menu_opcoes.append("📦 Produtos")

menu_opcoes.append("💰 Movimentações")

if st.session_state.get("realizar_venda"):
    menu_opcoes.append("🛒 Vendas")

menu_opcoes.append("🏦 Contas")

if st.session_state.get("contas_pagar"):
    menu_opcoes.append("📤 Contas a Pagar")

if st.session_state.get("ver_financeiro"):
    menu_opcoes.append("📥 Contas a Receber")

menu_opcoes.append("💸 Despesas")

if st.session_state.get("configuracoes"):
    menu_opcoes.append("⚙️ Configurações")


# 🔥 MENU ADMIN (CORRETO — AQUI ESTAVA O ERRO)
if perfil in ["admin", "diretor"]:
    menu_opcoes.append("🔐 Permissões")


# =========================
# PROTEÇÃO MENU VAZIO
# =========================
if len(menu_opcoes) <= 1:
    st.error("⛔ Usuário sem permissões liberadas.")
    st.stop()


# =========================
# SIDEBAR
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

    st.success(f"👤 {st.session_state.get('usuario', 'Usuário')}")

    st.divider()

    menu = st.radio("Menu", menu_opcoes)

    st.divider()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()


# =========================
# BLOQUEIO
# =========================
def bloquear(permissao):
    if not st.session_state.get(permissao, False):
        st.error("⛔ Você não tem permissão para acessar esta área.")
        st.stop()


# =========================
# ROTAS
# =========================
if menu == "🏠 Dashboard":
    tela_dashboard()

elif menu == "💰 Caixa":
    bloquear("abrir_caixa")
    tela_caixa()

elif menu == "👥 Clientes":
    bloquear("cadastrar_cliente")
    tela_clientes()

elif menu == "📦 Produtos":
    bloquear("cadastrar_produto")
    tela_produtos()

elif menu == "💰 Movimentações":
    tela_movimentacoes()

elif menu == "🛒 Vendas":
    bloquear("realizar_venda")
    tela_vendas()

elif menu == "💸 Despesas":
    tela_despesas()

elif menu == "🏦 Contas":
    tela_contas()

elif menu == "📤 Contas a Pagar":
    bloquear("contas_pagar")
    tela_contas_pagar()

elif menu == "📥 Contas a Receber":
    bloquear("ver_financeiro")
    tela_contas_receber()

elif menu == "🔐 Permissões":
    tela_painel_permissoes()

elif menu == "⚙️ Configurações":
    bloquear("configuracoes")
    tela_configuracoes()