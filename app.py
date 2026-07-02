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
from telas.central_compras import tela_central_compras
from telas.admin_banco import tela_admin_banco
from telas.conversao_xml import tela_conversao_xml


# ==================================================
# CSS
# ==================================================
def carregar_css():
    caminho_css = os.path.join(BASE_DIR, "styles", "styles.css")

    if os.path.exists(caminho_css):
        with open(caminho_css, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


carregar_css()

st.markdown(
    """
    <style>
        /* IMPORTANTE:
           Não forçamos mais largura interna da sidebar.
           Isso evita o sumiço da barra lateral no Render/Streamlit.
        */

        section[data-testid="stSidebar"] button {
            min-height: 44px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            background: rgba(255,255,255,0.08) !important;
            color: white !important;
            font-weight: 600 !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding-left: 14px !important;
            padding-right: 14px !important;
            margin-bottom: 6px !important;
            box-sizing: border-box !important;
            white-space:nowrap !important;
        }

        section[data-testid="stSidebar"] button:hover {
            background: rgba(68,214,44,0.30) !important;
            border: 1px solid #44D62C !important;
            color: white !important;
        }

       .menu-ativo{

            width:100% !important;
            min-width:100% !important;
            max-width:100% !important;

            height:46px !important;

            display:flex;
            align-items:center;
            justify-content:flex-start;

            padding:0 16px;

            border-radius:14px;

            background:linear-gradient(
                90deg,
                #44D62C,
                #008ACD
            );

    color:white;

    font-weight:800;

    box-sizing:border-box;

    margin-bottom:8px;

    overflow:hidden;

    white-space:nowrap;
}

        section[data-testid="stSidebar"] h1 {
            font-size: 22px !important;
            white-space: normal !important;
        }

        .menu-topo-box {
            background: rgba(68,214,44,0.08);
            border: 1px solid rgba(68,214,44,0.25);
            border-radius: 14px;
            padding: 10px 14px;
            margin-bottom: 12px;
        }

        .menu-topo-titulo {
            font-weight: 800;
            color: #44D62C;
            margin-bottom: 4px;
        }

        @media (max-width: 768px) {
            section[data-testid="stSidebar"] button,
            .menu-ativo {
                font-size: 13px !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ==================================================
# SESSION STATE
# ==================================================
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if "menu_atual" not in st.session_state:
    st.session_state["menu_atual"] = "🏠 Dashboard"

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
        "📥 Compras",
        "🔁 Conversão XML"
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

if admin_total or st.session_state.get("pode_produtos"):
    menu_opcoes.append("🧠 Central de Compras")

if admin_total or st.session_state.get("pode_relatorios"):
    menu_opcoes.append("📊 Relatórios")

if admin_total or st.session_state.get("pode_configuracoes"):
    menu_opcoes.append("⚙️ Configurações")

if admin_total:
    menu_opcoes.append("💾 Administração do Banco")

if admin_total or st.session_state.get("pode_fechamento_caixa"):
    menu_opcoes.append("📊 Fechamento de Caixa")

if admin_total:
    menu_opcoes.append("🔐 Permissões")

if st.session_state["menu_atual"] not in menu_opcoes:
    st.session_state["menu_atual"] = "🏠 Dashboard"

# ==================================================
# MENU SUPERIOR DE SEGURANÇA
# ==================================================
st.markdown(
    """
    <div class="menu-topo-box">
        <div class="menu-topo-titulo">🧭 Navegação rápida</div>
    </div>
    """,
    unsafe_allow_html=True
)

col_menu, col_sair = st.columns([4, 1])

with col_menu:
    menu_topo = st.selectbox(
        "Escolha a tela",
        menu_opcoes,
        index=menu_opcoes.index(st.session_state["menu_atual"]),
        key="menu_topo_select",
        label_visibility="collapsed"
    )

with col_sair:
    if st.button("🚪 Sair", use_container_width=True, key="botao_sair_topo"):
        st.session_state.clear()
        st.rerun()

if menu_topo != st.session_state["menu_atual"]:
    st.session_state["menu_atual"] = menu_topo
    st.rerun()

st.divider()

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.title("ERP Verde Infância")
    st.success(f"👤 {st.session_state.get('usuario', 'Usuário')}")

    st.markdown("### Menu")

    for opcao in menu_opcoes:
        if opcao == st.session_state["menu_atual"]:
            st.markdown(
                f"<div class='menu-ativo'>{opcao}</div>",
                unsafe_allow_html=True
            )
        else:
            if st.button(opcao, key=f"menu_{opcao}"):
                st.session_state["menu_atual"] = opcao
                st.rerun()

    st.divider()

    if st.button("🚪 Sair", key="botao_sair"):
        st.session_state.clear()
        st.rerun()

menu = st.session_state["menu_atual"]

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

    elif menu == "🔁 Conversão XML":
        bloquear("pode_produtos")
        tela_conversao_xml()

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

    elif menu == "🧠 Central de Compras":
        bloquear("pode_produtos")
        tela_central_compras()

    elif menu == "📊 Relatórios":
        bloquear("pode_relatorios")
        tela_relatorios()

    elif menu == "📊 Fechamento de Caixa":
        bloquear("pode_fechamento_caixa")
        tela_fechamento_caixa()

    elif menu == "⚙️ Configurações":
        bloquear("pode_configuracoes")
        tela_configuracoes()

    elif menu == "💾 Administração do Banco":
        if not admin_total:
            st.error("⛔ Acesso restrito ao Diretor.")
            st.stop()
        tela_admin_banco()

    elif menu == "🔐 Permissões":
        tela_painel_permissoes()

except Exception as e:
    st.error("Erro geral na aplicação")
    st.exception(e)
