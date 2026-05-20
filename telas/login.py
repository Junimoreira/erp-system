import streamlit as st
import bcrypt

from database.connection import conectar


# ==================================================
# TELA LOGIN
# ==================================================
def tela_login():

    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(
            135deg,
            #0f1117 0%,
            #111827 50%,
            #0b0f14 100%
        );
    }

    .login-box {

        background: rgba(17, 24, 39, 0.92);

        padding: 40px;

        border-radius: 20px;

        border: 1px solid rgba(255,255,255,0.08);

        box-shadow:
            0 0 30px rgba(68,214,44,0.15);

        max-width: 420px;

        margin: auto;

        margin-top: 80px;
    }

    .titulo {
        text-align: center;
        font-size: 38px;
        font-weight: bold;
        color: white;
    }

    .subtitulo {
        text-align: center;
        color: #9ca3af;
        margin-bottom: 30px;
    }

    .verde {
        color: #44d62c;
    }

    .stTextInput > div > div > input {

        background-color: #111827;

        color: white;

        border: 1px solid #374151;

        border-radius: 10px;
    }

    .stButton > button {

        width: 100%;

        background: #44d62c;

        color: black;

        font-weight: bold;

        border: none;

        padding: 14px;

        border-radius: 10px;

        transition: 0.3s;
    }

    .stButton > button:hover {

        background: #36b61f;

        color: white;
    }

    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-box">

        <div class="titulo">
            ERP <span class="verde">Verde Infância</span>
        </div>

        <div class="subtitulo">
            Faça login para acessar o sistema
        </div>

    </div>
    """, unsafe_allow_html=True)

    usuario = st.text_input("Usuário")

    senha = st.text_input(
        "Senha",
        type="password"
    )

    if st.button("Entrar no Sistema"):

        try:

            conn = conectar()

            if conn is None:

                st.error(
                    "Erro ao conectar com banco de dados."
                )

                return

            cur = conn.cursor()

            cur.execute("""

                SELECT

                    id,
                    nome,
                    senha,
                    perfil,

                    pode_dashboard,
                    pode_caixa,
                    pode_clientes,
                    pode_produtos,
                    pode_vendas,
                    pode_financeiro,
                    pode_contas_pagar,
                    pode_contas_receber,
                    pode_despesas,
                    pode_configuracoes

                FROM usuarios

                WHERE usuario = %s

                AND ativo = TRUE

            """, (usuario,))

            dados = cur.fetchone()

            if dados:

                (
                    user_id,
                    nome,
                    senha_hash,
                    perfil,

                    pode_dashboard,
                    pode_caixa,
                    pode_clientes,
                    pode_produtos,
                    pode_vendas,
                    pode_financeiro,
                    pode_contas_pagar,
                    pode_contas_receber,
                    pode_despesas,
                    pode_configuracoes

                ) = dados

                if bcrypt.checkpw(

                    senha.encode(),
                    senha_hash.encode()

                ):

                    # ======================================
                    # SESSÃO
                    # ======================================
                    st.session_state["logado"] = True

                    st.session_state["usuario"] = nome

                    st.session_state["perfil"] = perfil

                    st.session_state["usuario_id"] = user_id

                    # ======================================
                    # PERMISSÕES
                    # ======================================
                    st.session_state["pode_dashboard"] = pode_dashboard

                    st.session_state["pode_caixa"] = pode_caixa

                    st.session_state["pode_clientes"] = pode_clientes

                    st.session_state["pode_produtos"] = pode_produtos

                    st.session_state["pode_vendas"] = pode_vendas

                    st.session_state["pode_financeiro"] = pode_financeiro

                    st.session_state["pode_contas_pagar"] = pode_contas_pagar

                    st.session_state["pode_contas_receber"] = pode_contas_receber

                    st.session_state["pode_despesas"] = pode_despesas

                    st.session_state["pode_configuracoes"] = pode_configuracoes

                    st.success("✅ Login realizado!")

                    st.rerun()

                else:

                    st.error("❌ Senha inválida")

            else:

                st.error("❌ Usuário não encontrado")

            cur.close()

            conn.close()

        except Exception as erro:

            st.error(f"Erro: {erro}")

    st.markdown("</div>", unsafe_allow_html=True)