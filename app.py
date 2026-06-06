# ==================================================
# IMPORTAÇÃO DAS TELAS
# ==================================================
from telas.fechamento_caixa import tela_fechamento_caixa
from telas.formacao_preco import tela_formacao_preco
from telas.relatorios.relatorio_caixa import tela_relatorio_caixa
from telas.relatorios.relatorio_vendas import tela_relatorio_vendas
from telas.login import tela_login
from telas.dashboard import tela_dashboard
from telas.caixa import tela_caixa
from telas.clientes import tela_clientes
from telas.produtos import tela_produtos
from telas.vendas import tela_vendas
from telas.movimentacoes import tela_movimentacoes
from telas.contas_bancarias import tela_contas_bancarias
from telas.contas_pagar import tela_contas_pagar
from telas.contas_receber import tela_contas_receber
from telas.configuracoes import tela_configuracoes
from telas.compras import tela_compras
from telas.fornecedores import tela_fornecedores
from telas.painel_admin_permissoes import tela_painel_permissoes
from telas.relatorios.relatorio_produtos_pdf import tela_relatorio_produtos_pdf
from telas.relatorios.relatorio_vendas_pdf import tela_relatorio_vendas_lucro
from telas.relatorios.relatorio_contas_pagar_pdf import tela_relatorio_contas_pagar
from telas.relatorios.relatorio_contas_receber_pdf import tela_relatorio_contas_receber

import streamlit as st
import sys
import os

# ==================================================
# PATH
# ==================================================
sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../.."
        )
    )
)

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(
    page_title="ERP - Verde Infância",
    page_icon="assets/logo2.png",
    layout="wide"
)
# ==================================================
# CSS
# ==================================================
import os

# ==================================================
# CSS
# ==================================================
def carregar_css():

    try:

        caminho_css = os.path.join(
            os.path.dirname(__file__),
            "styles",
            "styles.css"
        )

        with open(caminho_css, encoding="utf-8") as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

    except Exception as e:

        st.error(f"Erro CSS: {e}")

carregar_css()
# ==================================================
# FALLBACK USUÁRIOS
# ==================================================
try:
    from telas.usuarios import tela_usuarios
except:
    def tela_usuarios():
        st.warning("Tela de usuários não encontrada.")

# ==================================================
# SESSION
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

if admin_total or st.session_state.get("pode_caixa", False):
    menu_opcoes.append("💰 Caixa")

if admin_total or st.session_state.get("pode_clientes", False):
    menu_opcoes.append("👥 Clientes")

if admin_total or st.session_state.get("pode_produtos", False):
    menu_opcoes += ["📦 Produtos", "💰 Formação de Preço", "🚚 Fornecedores", "📥 Compras"]

if admin_total or st.session_state.get("pode_movimentacoes", False):
    menu_opcoes.append("💰 Movimentações")

if admin_total or st.session_state.get("pode_vendas", False):
    menu_opcoes.append("🛒 Vendas")

if admin_total or st.session_state.get("pode_financeiro", False):
    menu_opcoes.append("🏦 Contas Bancárias")

if admin_total or st.session_state.get("pode_contas_pagar", False):
    menu_opcoes.append("📤 Contas a Pagar")

if admin_total or st.session_state.get("pode_contas_receber", False):
    menu_opcoes.append("📥 Contas a Receber")

if admin_total or st.session_state.get("pode_relatorios", False):
    menu_opcoes.append("📊 Relatórios")

if admin_total or st.session_state.get("pode_configuracoes", False):
    menu_opcoes.append("⚙️ Configurações")

if admin_total or st.session_state.get("pode_fechamento_caixa", False):
    menu_opcoes.append("📊 Fechamento de Caixa")

if admin_total or st.session_state.get("pode_usuarios", False):
    menu_opcoes.append("👤 Usuários")

if admin_total:
    menu_opcoes.append("🔐 Permissões")

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:

    try:
        st.image("assets/Logo.png", width=180)
    except:
        pass

    st.markdown("<b>Gestão</b>", unsafe_allow_html=True)

    st.success(f"👤 {st.session_state.get('usuario', 'Usuário')}")

    st.divider()

    menu = st.radio("Menu", menu_opcoes)

    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
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
        tela_formacao_preco()

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

    elif menu == "🏦 Contas Bancárias":
        bloquear("pode_financeiro")
        tela_contas_bancarias()

    elif menu == "📤 Contas a Pagar":
        bloquear("pode_contas_pagar")
        tela_contas_pagar()

    elif menu == "📥 Contas a Receber":
        bloquear("pode_contas_receber")
        tela_contas_receber()

    elif menu == "📊 Fechamento de Caixa":
        bloquear("pode_fechamento_caixa")
        tela_fechamento_caixa()

    elif menu == "📊 Relatórios":

        bloquear("pode_relatorios")

        st.title("📊 Central de Relatórios")

        relatorio = st.selectbox(
            "Relatório",
            [
                "Caixa",
                "Vendas",
                "Vendas com lucro",
                "Produtos PDF",
                "Contas a Pagar",
                "Contas a Receber"
            ]
        )

        if relatorio == "Caixa":
            tela_relatorio_caixa()

        elif relatorio == "Vendas":
            tela_relatorio_vendas()

        elif relatorio == "Vendas com lucro":
            tela_relatorio_vendas_lucro()

        elif relatorio == "Produtos PDF":
            tela_relatorio_produtos_pdf()

        elif relatorio == "Contas a Pagar":
            tela_relatorio_contas_pagar()

        elif relatorio == "Contas a Receber":
            tela_relatorio_contas_receber()

    elif menu == "⚙️ Configurações":
        bloquear("pode_configuracoes")
        tela_configuracoes()

    elif menu == "👤 Usuários":
        bloquear("pode_usuarios")
        tela_usuarios()

    elif menu == "🔐 Permissões":
        tela_painel_permissoes()

except Exception as e:
    st.error(f"Erro na tela: {e}")
    st.exception(e)
# ==================================================
# RELATÓRIOS (CORRIGIDO)
# ==================================================
elif menu == "📊 Relatórios":

    bloquear("pode_relatorios")

    st.title("📊 Central de Relatórios")

    relatorio = st.selectbox("Relatório", [
        "Caixa",
        "Vendas",
        "Vendas com lucro",
        "Produtos PDF",
        "Contas a Pagar",
        "Contas a Receber"
    ])

    if relatorio == "Caixa":
        tela_relatorio_caixa()

    elif relatorio == "Vendas":
        tela_relatorio_vendas()

    elif relatorio == "Vendas com lucro":
        tela_relatorio_vendas_lucro()

    elif relatorio == "Produtos PDF":
        tela_relatorio_produtos_pdf()

    elif relatorio == "Contas a Pagar":
        tela_relatorio_contas_pagar()

    elif relatorio == "Contas a Receber":
        tela_relatorio_contas_receber()

elif menu == "⚙️ Configurações":
    bloquear("pode_configuracoes")
    tela_configuracoes()

elif menu == "👤 Usuários":
    bloquear("pode_usuarios")
    tela_usuarios()

elif menu == "🔐 Permissões":
    tela_painel_permissoes()