import streamlit as st

from telas.fechamento_caixa import tela_fechamento_caixa
from telas.formacao_preco import tela_formacao_preco


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

    with open(
        "styles/styles.css",
        encoding="utf-8"
    ) as f:

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
from telas.configuracoes import tela_configuracoes
from telas.compras import tela_compras
from telas.fornecedores import tela_fornecedores
from telas.painel_admin_permissoes import tela_painel_permissoes


# =========================
# USUÁRIOS (fallback)
# =========================
try:

    from telas.usuarios import tela_usuarios

except:

    def tela_usuarios():

        st.title("👤 Usuários")

        st.info(
            "Tela de usuários em desenvolvimento."
        )


# =========================
# SESSION
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
# ADMIN TOTAL
# =========================
admin_total = perfil in [
    "admin",
    "diretor"
]


# =========================
# MENU
# =========================
menu_opcoes = []

menu_opcoes.append(
    "🏠 Dashboard"
)


# ==========================================
# CAIXA
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_caixa")
):

    menu_opcoes.append(
        "💰 Caixa"
    )


# ==========================================
# CLIENTES
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_clientes")
):

    menu_opcoes.append(
        "👥 Clientes"
    )


# ==========================================
# PRODUTOS
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_produtos")
):

    menu_opcoes.append(
        "📦 Produtos"
    )

    menu_opcoes.append(
        "💰 Formação de Preço"
    )


# ==========================================
# FORNECEDORES
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_produtos")
):

    menu_opcoes.append(
        "🚚 Fornecedores"
    )

    menu_opcoes.append(
        "📥 Compras"
    )


# ==========================================
# USUÁRIOS
# ==========================================
if admin_total:

    menu_opcoes.append(
        "👤 Usuários"
    )


# ==========================================
# MOVIMENTAÇÕES
# ==========================================
menu_opcoes.append(
    "💰 Movimentações"
)


# ==========================================
# VENDAS
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_vendas")
):

    menu_opcoes.append(
        "🛒 Vendas"
    )


# ==========================================
# CONTAS
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_financeiro")
):

    menu_opcoes.append(
        "🏦 Contas"
    )


# ==========================================
# CONTAS A PAGAR
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_contas_pagar")
):

    menu_opcoes.append(
        "📤 Contas a Pagar"
    )


# ==========================================
# CONTAS A RECEBER
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_contas_receber")
):

    menu_opcoes.append(
        "📥 Contas a Receber"
    )


# ==========================================
# FECHAMENTO CAIXA
# ==========================================
if admin_total:

    menu_opcoes.append(
        "📊 Fechamento de Caixa"
    )


# ==========================================
# CONFIGURAÇÕES
# ==========================================
if (
    admin_total
    or st.session_state.get("pode_configuracoes")
):

    menu_opcoes.append(
        "⚙️ Configurações"
    )


# ==========================================
# PERMISSÕES
# ==========================================
if admin_total:

    menu_opcoes.append(
        "🔐 Permissões"
    )


# =========================
# PROTEÇÃO MENU
# =========================
if len(menu_opcoes) <= 1:

    st.error(
        "⛔ Usuário sem permissões."
    )

    st.stop()


# =========================
# SIDEBAR
# =========================
with st.sidebar:

    try:

        st.image(
            "assets/Logo.png",
            width=180
        )

    except:

        pass

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

    if st.button(
        "🚪 Sair",
        use_container_width=True
    ):

        st.session_state.clear()

        st.rerun()


# =========================
# BLOQUEIO
# =========================
def bloquear(permissao):

    if not (
        admin_total
        or st.session_state.get(
            permissao,
            False
        )
    ):

        st.error(
            "⛔ Você não possui permissão."
        )

        st.stop()


# =========================
# ROTAS
# =========================
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

    tela_formacao_preco()


elif menu == "🚚 Fornecedores":

    bloquear("pode_produtos")

    tela_fornecedores()


elif menu == "📥 Compras":

    bloquear("pode_produtos")

    tela_compras()


elif menu == "👤 Usuários":

    tela_usuarios()


elif menu == "💰 Movimentações":

    tela_movimentacoes()


elif menu == "🛒 Vendas":

    bloquear("pode_vendas")

    tela_vendas()


elif menu == "🏦 Contas":

    bloquear("pode_financeiro")

    tela_contas()


elif menu == "📤 Contas a Pagar":

    bloquear("pode_contas_pagar")

    tela_contas_pagar()


elif menu == "📥 Contas a Receber":

    bloquear("pode_contas_receber")

    tela_contas_receber()


elif menu == "📊 Fechamento de Caixa":

    tela_fechamento_caixa()


elif menu == "⚙️ Configurações":

    bloquear("pode_configuracoes")

    tela_configuracoes()


elif menu == "🔐 Permissões":

    tela_painel_permissoes()