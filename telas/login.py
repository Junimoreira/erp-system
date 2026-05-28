import streamlit as st
import bcrypt
import os

from database.connection import conectar


# =====================================
# AUTENTICAÇÃO
# =====================================
def autenticar_usuario(usuario):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT id, nome, usuario, senha, perfil, ativo
            FROM usuarios
            WHERE usuario = %s
            LIMIT 1
        """, (usuario,))

        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "nome": row[1],
            "usuario": row[2],
            "senha": row[3],
            "perfil": row[4],
            "ativo": row[5]
        }

    finally:
        cursor.close()
        conn.close()


# =====================================
# LOGIN SaaS PROFISSIONAL
# =====================================
def tela_login():

    st.markdown("""
        <style>

        /* FUNDO SaaS MODERNO */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #111827 50%, #0b1120 100%);
        }

        /* CENTRALIZAÇÃO TOTAL */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 90vh;
        }

        /* CARD PRINCIPAL */
        .login-card {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);

            border: 1px solid rgba(255, 255, 255, 0.15);

            padding: 40px 35px;
            border-radius: 18px;

            width: 380px;

            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        }

        /* TÍTULO */
        .titulo-login {
            text-align: center;
            color: white;
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 25px;
        }

        /* INPUTS */
        .stTextInput input {
            border-radius: 10px !important;
            padding: 10px !important;
            border: 2px solid #44D62C !important;
        }

        /* BOTÃO */
        .stButton button {
            width: 100%;
            border-radius: 10px;
            height: 45px;
            font-weight: bold;
            background: linear-gradient(90deg, #44D62C, #008ACD);
            color: white;
            border: none;
            transition: 0.3s;
        }

        .stButton button:hover {
            transform: scale(1.03);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }

        /* TEXTO AUXILIAR */
        .login-sub {
            text-align: center;
            color: #cbd5e1;
            font-size: 13px;
            margin-bottom: 20px;
        }

        </style>
    """, unsafe_allow_html=True)

    # =====================================
    # LAYOUT CENTRAL
    # =====================================
    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)

    # LOGO
    logo_path = "assets/logo1.png"

    if os.path.exists(logo_path):
        st.image(logo_path, width=180)

    st.markdown('<div class="titulo-login">ERP Verde Infância</div>', unsafe_allow_html=True)

    st.markdown('<div class="login-sub">Faça login para acessar o sistema</div>', unsafe_allow_html=True)

    # CAMPOS
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    # BOTÃO
    if st.button("Entrar", use_container_width=True):

        if not usuario or not senha:
            st.warning("Informe usuário e senha.")
            return

        dados = autenticar_usuario(usuario)

        if dados is None:
            st.error("Usuário inválido.")
            return

        if not dados["ativo"]:
            st.error("Usuário desativado.")
            return

        try:
            senha_valida = bcrypt.checkpw(
                senha.encode(),
                dados["senha"].encode()
            )
        except:
            st.error("Erro ao validar senha.")
            return

        if not senha_valida:
            st.error("Senha inválida.")
            return

        # SESSION
        st.session_state["logado"] = True
        st.session_state["id"] = dados["id"]
        st.session_state["usuario"] = dados["usuario"]
        st.session_state["nome"] = dados["nome"]
        st.session_state["perfil"] = dados["perfil"]

        st.success(f"Bem-vindo, {dados['nome']}!")
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)