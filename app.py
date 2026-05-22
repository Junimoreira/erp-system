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
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )
except:
    pass


# =========================
# IMPORTAÇÃO DAS TELAS
# =========================
from telas.login import tela_login

from telas.dashboard import tela_dashboard
from telas.caixa import tela_caixa
from telas.clientes import tela_clientes
from telas.produtos import tela_produtos
from telas.vendas import tela_vendas
from telas.movimentacoes import tela_movimentacoes
from telas.contas import tela_contas
from telas.contas_pagar import tela_contas_pagar
from telas.contas_receber import tela_contas_receber
from telas.despesas import tela_despesas
from telas.configuracoes import tela_configuracoes

from telas.painel_admin_permissoes import (
    tela_painel_permissoes
)

# ⚠ IMPORTANTE:
# Só mantenha esta importação se o arquivo existir
# telas/usuarios.py
try:
    from telas.usuarios import tela_usuarios
except:
    def tela_usuarios():
        st.title("👤 Usuários")
        st.info(
            "Tela de usuários ainda em desenvolvimento."
        )


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
# PERFIL
# =========================
perfil = str(
    st.session_state.get(
        "perfil",
        ""
    )
).strip().lower()


# =========================
# MENU BASE
# =========================
menu_opcoes = []

menu_opcoes.append("🏠 Dashboard")


# =====================================
# CAIXA
# =====================================
if st.session_state.get("abrir_caixa"):
    menu_opcoes.append("💰 Caixa")


# =====================================
# CLIENTES
# =====================================
if st.session_state.get("cadastrar_cliente"):
    menu_opcoes.append("👥 Clientes")


# =====================================
# PRODUTOS
# =====================================
if st.session_state.get("cadastrar_produto"):
    menu_opcoes.append("📦 Produtos")


# =====================================
# USUÁRIOS
# =====================================
if st.session_state.get("usuarios"):
    menu_opcoes.append("👤 Usuários")


# =====================================
# MOVIMENTAÇÕES
# =====================================
menu_opcoes.append("💰 Movimentações")


# =====================================
# VENDAS
# =====================================
if st.session_state.get("realizar_venda"):
    menu_opcoes.append("🛒 Vendas")


# =====================================
# CONTAS
# =====================================
if st.session_state.get("ver_contas"):
    menu_opcoes.append("🏦 Contas")


# =====================================
# CONTAS A PAGAR
# =====================================
if st.session_state.get("contas_pagar"):
    menu_opcoes.append("📤 Contas a Pagar")


# =====================================
# CONTAS A RECEBER
# =====================================
if st.session_state.get("ver_financeiro"):
    menu_opcoes.append("📥 Contas a Receber")


# =====================================
# DESPESAS
# =====================================
if st.session_state.get("ver_despesas"):
    menu_opcoes.append("💸 Despesas")


# =====================================
# CONFIGURAÇÕES
# =====================================
if st.session_state.get("configuracoes"):
    menu_opcoes.append("⚙️ Configurações")


# =====================================
# MENU ADMIN
# =====================================
if perfil in ["admin", "diretor"]:
    menu_opcoes.append("🔐 Permissões")


# =========================
# PROTEÇÃO MENU VAZIO
# =========================
if len(menu_opcoes) <= 1:
    st.error(
        "⛔ Usuário sem permissões liberadas."
    )
    st.stop()


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    st.image(
        "assets/Logo.png",
        width=180
    )

    st.markdown(
        """
        <div class="sidebar-title">
            ERP Verde Infância
        </div>
        """,
        unsafe_allow_html=True
    )

    st.success(
        f"👤 {st.session_state.get('usuario', 'Usuário')}"
    )

    st.divider()

    menu = st.radio(
        "Menu",
        menu_opcoes
    )

    st.divider()

    if st.button("🚪 Sair"):

        st.session_state.clear()

        st.rerun()


# =========================
# BLOQUEIO
# =========================
def bloquear(permissao):

    if not st.session_state.get(
        permissao,
        False
    ):

        st.error(
            "⛔ Você não tem permissão para acessar esta área."
        )

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


elif menu == "👤 Usuários":

    bloquear("usuarios")

    tela_usuarios()


elif menu == "💰 Movimentações":

    tela_movimentacoes()


elif menu == "🛒 Vendas":

    bloquear("realizar_venda")

    tela_vendas()


elif menu == "🏦 Contas":

    bloquear("ver_contas")

    tela_contas()


elif menu == "📤 Contas a Pagar":

    bloquear("contas_pagar")

    tela_contas_pagar()


elif menu == "📥 Contas a Receber":

    bloquear("ver_financeiro")

    tela_contas_receber()


elif menu == "💸 Despesas":

    bloquear("ver_despesas")

    tela_despesas()


elif menu == "🔐 Permissões":

    tela_painel_permissoes()


elif menu == "⚙️ Configurações":

    bloquear("configuracoes")

    tela_configuracoes()