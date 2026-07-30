import os
import sys

import streamlit as st


# ==================================================
# PATH DO PROJETO
# ==================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


# ==================================================
# CONFIGURAÇÃO DO STREAMLIT
# ==================================================
st.set_page_config(
    page_title="ERP Verde Infância",
    page_icon="assets/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# IMPORTAÇÃO DAS TELAS
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
# CSS EXTERNO
# ==================================================
def carregar_css():
    caminho_css = os.path.join(
        BASE_DIR,
        "styles",
        "styles.css"
    )

    if os.path.exists(caminho_css):
        with open(caminho_css, encoding="utf-8") as arquivo_css:
            st.markdown(
                f"<style>{arquivo_css.read()}</style>",
                unsafe_allow_html=True
            )


carregar_css()


# ==================================================
# CSS LOCAL DO APP
# ==================================================
st.markdown(
    """
    <style>
        /* ==================================================
           BOTÕES DO MENU LATERAL
        ================================================== */

        section[data-testid="stSidebar"]
        div[data-testid="stButton"] {
            width: 100% !important;
            margin: 0 0 6px 0 !important;
        }

        section[data-testid="stSidebar"]
        div[data-testid="stButton"] > button {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;

            height: 46px !important;
            min-height: 46px !important;
            max-height: 46px !important;

            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;

            padding: 0 16px !important;
            margin: 0 !important;

            border-radius: 14px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;

            background: rgba(255, 255, 255, 0.08) !important;
            color: white !important;

            font-size: 14px !important;
            font-weight: 600 !important;
            line-height: 1.2 !important;
            text-align: left !important;

            box-sizing: border-box !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }

        section[data-testid="stSidebar"]
        div[data-testid="stButton"] > button p {
            width: 100% !important;
            margin: 0 !important;

            color: white !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            line-height: 1.2 !important;
            text-align: left !important;

            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        section[data-testid="stSidebar"]
        div[data-testid="stButton"] > button:hover {
            background: rgba(68, 214, 44, 0.30) !important;
            border-color: #44D62C !important;
            color: white !important;
        }

        section[data-testid="stSidebar"]
        div[data-testid="stButton"] > button:focus {
            border-color: #44D62C !important;
            box-shadow: 0 0 0 1px rgba(68, 214, 44, 0.35) !important;
        }

        /* ==================================================
           ITEM ATIVO DO MENU
        ================================================== */

        .menu-ativo {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;

            height: 46px !important;
            min-height: 46px !important;
            max-height: 46px !important;

            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;

            padding: 0 16px !important;
            margin: 0 0 6px 0 !important;

            border-radius: 14px !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;

            background: linear-gradient(
                90deg,
                #44D62C,
                #008ACD
            ) !important;

            color: white !important;
            font-size: 14px !important;
            font-weight: 800 !important;
            line-height: 1.2 !important;

            box-sizing: border-box !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        /* ==================================================
           CAIXA DO USUÁRIO NA SIDEBAR
        ================================================== */

        .usuario-box {
            width: 100%;
            padding: 11px 13px;
            margin: 4px 0 14px 0;

            background: rgba(68, 214, 44, 0.14);
            border: 1px solid rgba(68, 214, 44, 0.38);
            border-radius: 14px;

            color: white;
            font-weight: 700;
            box-sizing: border-box;
        }

        .usuario-perfil {
            margin-top: 3px;
            font-size: 12px;
            font-weight: 500;
            opacity: 0.85;
        }

        /* ==================================================
           MENU SUPERIOR
        ================================================== */

        .menu-topo-box {
            padding: 10px 14px;
            margin-bottom: 12px;

            background: rgba(68, 214, 44, 0.08);
            border: 1px solid rgba(68, 214, 44, 0.25);
            border-radius: 14px;
        }

        .menu-topo-titulo {
            color: #44D62C;
            font-weight: 800;
        }

        /* ==================================================
           TÍTULOS DA SIDEBAR
        ================================================== */

        section[data-testid="stSidebar"] h1 {
            font-size: 22px !important;
            white-space: normal !important;
        }

        section[data-testid="stSidebar"] h3 {
            margin-top: 4px !important;
            margin-bottom: 12px !important;
        }

        /* ==================================================
           RESPONSIVIDADE
        ================================================== */

        @media (max-width: 768px) {
            section[data-testid="stSidebar"]
            div[data-testid="stButton"] > button,
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
# PERFIL DO USUÁRIO
# ==================================================
perfil = str(
    st.session_state.get("perfil", "")
).strip()

perfil_normalizado = perfil.lower()

admin_total = perfil_normalizado in [
    "admin",
    "diretor"
]


# ==================================================
# FUNÇÃO DE PERMISSÃO
# ==================================================
def tem_permissao(permissao):
    if admin_total:
        return True

    return bool(
        st.session_state.get(permissao, False)
    )


# ==================================================
# CONSTRUÇÃO DAS OPÇÕES DO MENU
# ==================================================
menu_opcoes = ["🏠 Dashboard"]

if tem_permissao("pode_caixa"):
    menu_opcoes.append("💰 Caixa")

if tem_permissao("pode_clientes"):
    menu_opcoes.append("👥 Clientes")

if tem_permissao("pode_produtos"):
    menu_opcoes.extend([
        "📦 Produtos",
        "💰 Formação de Preço",
        "🚚 Fornecedores",
        "📥 Compras",
        "🔁 Conversão XML"
    ])

if tem_permissao("pode_movimentacoes"):
    menu_opcoes.append("💰 Movimentações")

if tem_permissao("pode_vendas"):
    menu_opcoes.extend([
        "🛒 Vendas",
        "📢 Marketing"
    ])

if tem_permissao("pode_financeiro"):
    menu_opcoes.extend([
        "🏦 Contas Bancárias",
        "📊 Fluxo de Caixa"
    ])

if tem_permissao("pode_contas_pagar"):
    menu_opcoes.append("📤 Contas a Pagar")

if tem_permissao("pode_contas_receber"):
    menu_opcoes.append("📥 Contas a Receber")

if tem_permissao("pode_produtos"):
    menu_opcoes.append("🧠 Central de Compras")

if tem_permissao("pode_relatorios"):
    menu_opcoes.append("📊 Relatórios")

if tem_permissao("pode_configuracoes"):
    menu_opcoes.append("⚙️ Configurações")

if tem_permissao("pode_fechamento_caixa"):
    menu_opcoes.append("📊 Fechamento de Caixa")

if admin_total:
    menu_opcoes.extend([
        "💾 Administração do Banco",
        "🔐 Permissões"
    ])


# ==================================================
# VALIDAÇÃO DO MENU ATUAL
# ==================================================
if st.session_state["menu_atual"] not in menu_opcoes:
    st.session_state["menu_atual"] = "🏠 Dashboard"


# ==================================================
# MENU SUPERIOR DE SEGURANÇA
# ==================================================
st.markdown(
    """
    <div class="menu-topo-box">
        <div class="menu-topo-titulo">
            🧭 Navegação rápida
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

col_menu, col_sair = st.columns([4, 1])

with col_menu:
    menu_topo = st.selectbox(
        "Escolha a tela",
        options=menu_opcoes,
        index=menu_opcoes.index(
            st.session_state["menu_atual"]
        ),
        key="menu_topo_select",
        label_visibility="collapsed"
    )

with col_sair:
    if st.button(
        "🚪 Sair",
        key="botao_sair_topo",
        use_container_width=True
    ):
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

    logo_path = os.path.join(
        BASE_DIR,
        "assets",
        "logo.png"
    )

    if os.path.exists(logo_path):
        st.image(
            logo_path,
            use_container_width=True
        )
    else:
        st.title("ERP Verde Infância")

    usuario_nome = (
        st.session_state.get("nome")
        or st.session_state.get("usuario")
        or "Usuário"
    )

    st.markdown(
        f"""
        <div class="usuario-box">
            👤 {usuario_nome}
            <div class="usuario-perfil">
                {perfil or "Usuário"}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### Menu")

    for opcao in menu_opcoes:

        if opcao == st.session_state["menu_atual"]:

            st.markdown(
                f"""
                <div class="menu-ativo">
                    {opcao}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            if st.button(
                opcao,
                key=f"menu_{opcao}",
                use_container_width=True
            ):
                st.session_state["menu_atual"] = opcao
                st.rerun()

    st.divider()

    if st.button(
        "🚪 Sair",
        key="botao_sair_sidebar",
        use_container_width=True
    ):
        st.session_state.clear()
        st.rerun()


# ==================================================
# MENU SELECIONADO
# ==================================================
menu = st.session_state["menu_atual"]


# ==================================================
# BLOQUEIO DE PERMISSÃO
# ==================================================
def bloquear(permissao):
    if not tem_permissao(permissao):
        st.error("⛔ Você não possui permissão para acessar esta tela.")
        st.stop()


# ==================================================
# ROTAS DO SISTEMA
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

        if not admin_total:
            st.error("⛔ Acesso restrito ao Diretor.")
            st.stop()

        tela_painel_permissoes()

    else:
        st.warning("Tela não encontrada.")
        st.session_state["menu_atual"] = "🏠 Dashboard"
        st.rerun()


except Exception as erro:
    st.error("Ocorreu um erro geral na aplicação.")
    st.exception(erro)