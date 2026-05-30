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

    /* Espaçamento da página */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 1000px;
    }

    /* Fundo */
    .stApp {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #111827 50%,
            #0b1120 100%
        );
    }

    /* Container Login */
    .login-wrapper {
        margin-top: 100px;
    }

    .subtitulo-login {
        text-align: center;
        color: #cbd5e1;
        font-size: 16px;
        margin-top: 15px;
        margin-bottom: 25px;
    }

    /* Inputs */
    .stTextInput input {
        border-radius: 12px !important;
        border: 2px solid #44D62C !important;
        height: 50px;
    }

    /* Botão */
    .stButton > button {
        width: 100%;
        height: 50px;
        border-radius: 12px;
        border: none;

        background: linear-gradient(
            90deg,
            #44D62C,
            #008ACD
        );

        color: white;
        font-weight: bold;
        font-size: 16px;

        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: scale(1.02);
    }

    </style>
    """, unsafe_allow_html=True)

    # =====================================
    # ESPAÇO SUPERIOR
    # =====================================

    st.markdown(
        "<div class='login-wrapper'></div>",
        unsafe_allow_html=True
    )

    # =====================================
    # CENTRALIZAÇÃO
    # =====================================

    col1, col2, col3 = st.columns([2, 1.5, 2])

    with col2:

        logo_path = "assets/logo1.png"

        if os.path.exists(logo_path):

            st.image(
                logo_path,
                width=320
            )

        st.markdown(
            """
            <div class="subtitulo-login">
                Sistema de Gestão da Loja
            </div>
            """,
            unsafe_allow_html=True
        )

        usuario = st.text_input(
            "👤 Usuário",
            key="login_usuario"
        )

        senha = st.text_input(
            "🔒 Senha",
            type="password",
            key="login_senha"
        )

        if st.button(
            "Entrar",
            use_container_width=True,
            key="btn_login"
        ):

            if not usuario or not senha:

                st.warning(
                    "Informe usuário e senha."
                )

                return

            dados = autenticar_usuario(usuario)

            if dados is None:

                st.error(
                    "Usuário inválido."
                )

                return

            if not dados["ativo"]:

                st.error(
                    "Usuário desativado."
                )

                return

            try:

                senha_valida = bcrypt.checkpw(
                    senha.encode(),
                    dados["senha"].encode()
                )

            except Exception:

                st.error(
                    "Erro ao validar senha."
                )

                return

            if not senha_valida:

                st.error(
                    "Senha inválida."
                )

                return

            st.session_state["logado"] = True
            st.session_state["id"] = dados["id"]
            st.session_state["usuario"] = dados["usuario"]
            st.session_state["nome"] = dados["nome"]
            st.session_state["perfil"] = dados["perfil"]

            st.success(
                f"Bem-vindo, {dados['nome']}!"
            )

            st.rerun()