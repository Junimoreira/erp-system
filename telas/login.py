import streamlit as st
import bcrypt
from database.connection import conectar


# =====================================
# BUSCAR USUÁRIO NO BANCO
# =====================================
def autenticar_usuario(usuario, senha):

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            nome,
            usuario,
            senha,
            perfil,
            ativo,

            abrir_caixa,
            fechar_caixa,
            realizar_venda,
            cadastrar_cliente,
            ver_financeiro,
            contas_pagar,
            configuracoes,
            usuarios,
            cadastrar_produto

        FROM usuarios
        WHERE usuario = %s
        LIMIT 1
    """, (usuario,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    dados = {
        "id": row[0],
        "nome": row[1],
        "usuario": row[2],
        "senha": row[3],
        "perfil": row[4],
        "ativo": row[5],

        "abrir_caixa": row[6],
        "fechar_caixa": row[7],
        "realizar_venda": row[8],
        "cadastrar_cliente": row[9],
        "ver_financeiro": row[10],
        "contas_pagar": row[11],
        "configuracoes": row[12],
        "usuarios": row[13],
        "cadastrar_produto": row[14],
    }

    return dados


# =====================================
# LOGIN
# =====================================
def tela_login():

    st.markdown("""
        <style>
        .login-box {
            background-color: #0f172a;
            padding: 30px;
            border-radius: 12px;
            max-width: 400px;
            margin: auto;
            margin-top: 100px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🔐 ERP - Login")

    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        dados = autenticar_usuario(usuario, senha)

        if not dados:
            st.error("Usuário não encontrado.")
            return

        if not dados["ativo"]:
            st.error("Usuário desativado.")
            return

        # =====================================
        # VALIDAÇÃO DE SENHA (bcrypt)
        # =====================================
        if not bcrypt.checkpw(senha.encode(), dados["senha"].encode()):
            st.error("Senha inválida.")
            return

        # =====================================
        # REGRA DE SUPER USUÁRIO
        # =====================================
        is_admin = dados["perfil"] in ["admin", "diretor"]

        # =====================================
        # SET SESSION STATE (MOTOR DO ERP)
        # =====================================
        st.session_state["logado"] = True
        st.session_state["id"] = dados["id"]
        st.session_state["usuario"] = dados["usuario"]
        st.session_state["nome"] = dados["nome"]
        st.session_state["perfil"] = dados["perfil"]

        # permissões banco
        st.session_state["abrir_caixa"] = True if is_admin else dados["abrir_caixa"]
        st.session_state["fechar_caixa"] = True if is_admin else dados["fechar_caixa"]
        st.session_state["realizar_venda"] = True if is_admin else dados["realizar_venda"]
        st.session_state["cadastrar_cliente"] = True if is_admin else dados["cadastrar_cliente"]
        st.session_state["ver_financeiro"] = True if is_admin else dados["ver_financeiro"]
        st.session_state["contas_pagar"] = True if is_admin else dados["contas_pagar"]
        st.session_state["configuracoes"] = True if is_admin else dados["configuracoes"]
        st.session_state["usuarios"] = True if is_admin else dados["usuarios"]
        st.session_state["cadastrar_produto"] = True if is_admin else dados["cadastrar_produto"]

        st.success(f"Bem-vindo, {dados['nome']}!")

        st.rerun()