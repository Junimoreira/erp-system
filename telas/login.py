import streamlit as st
import bcrypt
import os

from database.connection import conectar


# =====================================
# BUSCAR USUÁRIO NO BANCO
# =====================================
def autenticar_usuario(usuario):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        print("Usuário recebido:", usuario)

        cursor.execute("""
            SELECT
                id,
                nome,
                usuario,
                senha,
                perfil,
                ativo
            FROM usuarios
            WHERE usuario = %s
            LIMIT 1
        """, (usuario,))

        row = cursor.fetchone()

        print("Resultado banco:", row)

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

    except Exception as erro:

        print(f"Erro ao autenticar usuário: {erro}")

        return None

    finally:

        cursor.close()
        conn.close()


# =====================================
# LOGIN
# =====================================
def tela_login():

    st.markdown("""
        <style>

        .stApp {
            background: linear-gradient(
                135deg,
                #0f172a 0%,
                #111827 50%,
                #0b1120 100%
            );
        }

        .titulo-login {
            text-align: center;
            color: white;
            margin-top: 10px;
            margin-bottom: 30px;
        }

        .stTextInput > div > div > input {
            border-radius: 10px;
        }

        .stButton button {
            border-radius: 10px;
            height: 45px;
            font-weight: bold;
        }

        </style>
    """, unsafe_allow_html=True)

    # =====================================
    # LOGO
    # =====================================

    logo_path = "assets/logo1.png"

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if os.path.exists(logo_path):

            st.image(logo_path, width=240)

        else:

            st.warning("Logo não encontrada.")

        st.markdown(
            """
            <h1 class="titulo-login">
                🔐 ERP Verde Infância
            </h1>
            """,
            unsafe_allow_html=True
        )

    # =====================================
    # CAMPOS LOGIN
    # =====================================

    usuario = st.text_input("👤 Usuário")

    senha = st.text_input(
        "🔐 Senha",
        type="password"
    )

    # =====================================
    # BOTÃO LOGIN
    # =====================================

    if st.button(
        "Entrar",
        use_container_width=True
    ):

        if not usuario or not senha:

            st.warning(
                "Informe usuário e senha."
            )

            return

        dados = autenticar_usuario(usuario)

        # =====================================
        # USUÁRIO NÃO ENCONTRADO
        # =====================================

        if dados is None:

            st.error("Usuário inválido.")

            return

        # =====================================
        # USUÁRIO INATIVO
        # =====================================

        if not dados["ativo"]:

            st.error("Usuário desativado.")

            return

        # =====================================
        # VALIDAÇÃO SENHA
        # =====================================

        try:

            senha_valida = bcrypt.checkpw(
                senha.encode(),
                dados["senha"].encode()
            )

        except Exception as erro:

            print(f"Erro bcrypt: {erro}")

            st.error("Erro ao validar senha.")

            return

        if not senha_valida:

            st.error("Senha inválida.")

            return

        # =====================================
        # SESSION
        # =====================================

        st.session_state["logado"] = True

        st.session_state["id"] = dados["id"]

        st.session_state["usuario"] = dados["usuario"]

        st.session_state["nome"] = dados["nome"]

        st.session_state["perfil"] = dados["perfil"]

        # =====================================
        # PERMISSÕES TEMPORÁRIAS ADMIN
        # =====================================

        st.session_state["pode_dashboard"] = True
        st.session_state["pode_caixa"] = True
        st.session_state["pode_clientes"] = True
        st.session_state["pode_produtos"] = True
        st.session_state["pode_vendas"] = True
        st.session_state["pode_financeiro"] = True
        st.session_state["pode_contas_pagar"] = True
        st.session_state["pode_contas_receber"] = True
        st.session_state["pode_despesas"] = True
        st.session_state["pode_configuracoes"] = True

        st.success(
            f"Bem-vindo, {dados['nome']}!"
        )

        st.rerun()