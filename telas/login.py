import streamlit as st
import bcrypt
import os
from database.connection import conectar


# =====================================
# BUSCAR USUÁRIO NO BANCO
# =====================================
def autenticar_usuario(usuario, senha):

    conn = conectar()

    if conn is None:
        return None

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
            cadastrar_produto,
            ver_contas,
            ver_despesas

        FROM usuarios
        WHERE usuario = %s
        LIMIT 1
    """, (usuario,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    return {
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
        "ver_contas": row[15],
        "ver_despesas": row[16],
    }


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

        </style>
    """, unsafe_allow_html=True)

    # =====================================
    # LOGO (CORRIGIDO PARA RENDER)
    # =====================================

    logo_path = "assets/logo1.png"

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        if os.path.exists(logo_path):
            st.image(logo_path, width=240)
        else:
            st.warning("Logo não encontrada (verifique assets/logo.png)")

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
    senha = st.text_input("🔐 Senha", type="password")

    # =====================================
    # BOTÃO LOGIN
    # =====================================
    if st.button("Entrar", use_container_width=True):

        dados = autenticar_usuario(usuario, senha)

        if not dados:
            st.error("Usuário não encontrado.")
            return

        if not dados["ativo"]:
            st.error("Usuário desativado.")
            return

        # =====================================
        # VALIDAÇÃO DE SENHA
        # =====================================
        if not bcrypt.checkpw(
            senha.encode(),
            dados["senha"].encode()
        ):
            st.error("Senha inválida.")
            return

        # =====================================
        # SESSION STATE
        # =====================================
        st.session_state["logado"] = True
        st.session_state["id"] = dados["id"]
        st.session_state["usuario"] = dados["usuario"]
        st.session_state["nome"] = dados["nome"]
        st.session_state["perfil"] = dados["perfil"]

        # =====================================
        # PERMISSÕES
        # =====================================
        st.session_state.update({
            "abrir_caixa": dados["abrir_caixa"],
            "fechar_caixa": dados["fechar_caixa"],
            "realizar_venda": dados["realizar_venda"],
            "cadastrar_cliente": dados["cadastrar_cliente"],
            "ver_financeiro": dados["ver_financeiro"],
            "contas_pagar": dados["contas_pagar"],
            "configuracoes": dados["configuracoes"],
            "usuarios": dados["usuarios"],
            "cadastrar_produto": dados["cadastrar_produto"],
            "ver_contas": dados["ver_contas"],
            "ver_despesas": dados["ver_despesas"]
        })

        st.success(f"Bem-vindo, {dados['nome']}!")
        st.rerun()