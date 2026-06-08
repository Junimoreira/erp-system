# telas/login.py

import os
import base64
from datetime import datetime

import streamlit as st
from database.usuarios_db import autenticar_usuario
from frases import FRASES


# ==================================================
# RETORNA FRASE DO DIA
# ==================================================
def obter_frase_do_dia():
    dia_ano = datetime.now().timetuple().tm_yday
    indice = (dia_ano - 1) % len(FRASES)
    return FRASES[indice]


# ==================================================
# CONVERTE IMAGEM PARA BASE64
# ==================================================
def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()


# ==================================================
# LOGIN
# ==================================================
def tela_login():

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        # ==========================================
        # LOGO CENTRALIZADA
        # ==========================================
        logo_path = os.path.join(
            os.getcwd(),
            "assets",
            "logo1.png"
        )

        if os.path.exists(logo_path):

            logo_base64 = get_base64_image(
                logo_path
            )

            st.markdown(
                f"""
                <div style="
                    width:100%;
                    text-align:center;
                    margin-bottom:10px;
                ">
                    <img
                        src="data:image/png;base64,{logo_base64}"
                        style="
                            width:250px;
                            display:inline-block;
                        "
                    >
                </div>
                """,
                unsafe_allow_html=True
            )

        # ==========================================
        # FRASE DO DIA
        # ==========================================
        frase_do_dia = obter_frase_do_dia()

        st.markdown(
            f"""
            <h4 style='
                text-align:center;
                color:#071633;
                margin-bottom:5px;
                font-weight:500;
            '>
                {frase_do_dia}
            </h4>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <p style='
                text-align:center;
                color:#66bb44;
                font-size:15px;
                font-weight:600;
                margin-bottom:25px;
            '>
                🌱 Palavra que Inspira
            </p>
            """,
            unsafe_allow_html=True
        )

        # ==========================================
        # USUÁRIO
        # ==========================================
        usuario = st.text_input(
            "👤 Usuário"
        )

        # ==========================================
        # SENHA
        # ==========================================
        senha = st.text_input(
            "🔒 Senha",
            type="password"
        )

        # ==========================================
        # BOTÃO LOGIN
        # ==========================================
        if st.button(
            "Entrar",
            use_container_width=True
        ):

            if not usuario or not senha:

                st.warning(
                    "Informe usuário e senha."
                )

                return

            dados = autenticar_usuario(
                usuario,
                senha
            )

            if not dados:

                st.error(
                    "Usuário ou senha inválidos."
                )

                return

            # ======================================
            # SESSÃO
            # ======================================
            st.session_state["logado"] = True
            st.session_state["id"] = dados["id"]
            st.session_state["usuario"] = dados["usuario"]
            st.session_state["nome"] = dados["nome"]
            st.session_state["perfil"] = dados["perfil"]

            # Limpa permissões antigas
            for chave in list(st.session_state.keys()):

                if chave.startswith("pode_"):
                    del st.session_state[chave]

            # Carrega permissões
            for chave, valor in dados.items():

                if chave.startswith("pode_"):
                    st.session_state[chave] = bool(
                        valor
                    )

            st.success(
                f"Bem-vindo, {dados['nome']}!"
            )

            st.rerun()