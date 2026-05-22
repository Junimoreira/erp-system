import streamlit as st
from database.connection import conectar


# =====================================
# CARREGAR USUÁRIOS
# =====================================
def listar_usuarios():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            nome,
            usuario,
            perfil,

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
        ORDER BY nome
    """)

    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return [dict(zip(cols, r)) for r in rows]


# =====================================
# SALVAR PERMISSÕES
# =====================================
def salvar_permissoes(user_id, dados):

    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        UPDATE usuarios
        SET
            abrir_caixa = %s,
            fechar_caixa = %s,
            realizar_venda = %s,
            cadastrar_cliente = %s,
            ver_financeiro = %s,
            contas_pagar = %s,
            configuracoes = %s,
            usuarios = %s,
            cadastrar_produto = %s
        WHERE id = %s
    """, (
        dados["abrir_caixa"],
        dados["fechar_caixa"],
        dados["realizar_venda"],
        dados["cadastrar_cliente"],
        dados["ver_financeiro"],
        dados["contas_pagar"],
        dados["configuracoes"],
        dados["usuarios"],
        dados["cadastrar_produto"],
        user_id
    ))

    conn.commit()
    cur.close()
    conn.close()


# =====================================
# TELA ADMIN
# =====================================
def tela_painel_permissoes():

    st.title("🔐 Painel de Permissões (Admin)")

    usuarios = listar_usuarios()

    if not usuarios:
        st.warning("Nenhum usuário encontrado.")
        return

    # =====================================
    # SELEÇÃO DE USUÁRIO
    # =====================================
    lista_nomes = [f"{u['nome']} ({u['perfil']})" for u in usuarios]
    selecionado = st.selectbox("Selecionar usuário", lista_nomes)

    user = usuarios[lista_nomes.index(selecionado)]

    st.divider()

    st.subheader(f"👤 {user['nome']}")

    # =====================================
    # PROTEÇÃO ADMIN (NÃO EDITÁVEL)
    # =====================================
    if user["perfil"] == "admin":
        st.success("Este usuário é ADMIN e possui acesso total automático.")
        st.info("Permissões não precisam ser editadas.")
        return

    # =====================================
    # CHECKBOXES
    # =====================================
    col1, col2 = st.columns(2)

    permissoes = {}

    with col1:
        permissoes["abrir_caixa"] = st.checkbox("Abrir Caixa", value=user["abrir_caixa"])
        permissoes["fechar_caixa"] = st.checkbox("Fechar Caixa", value=user["fechar_caixa"])
        permissoes["realizar_venda"] = st.checkbox("Realizar Venda", value=user["realizar_venda"])
        permissoes["cadastrar_cliente"] = st.checkbox("Cadastrar Cliente", value=user["cadastrar_cliente"])
        permissoes["cadastrar_produto"] = st.checkbox("Cadastrar Produto", value=user["cadastrar_produto"])

    with col2:
        permissoes["ver_financeiro"] = st.checkbox("Ver Financeiro", value=user["ver_financeiro"])
        permissoes["contas_pagar"] = st.checkbox("Contas a Pagar", value=user["contas_pagar"])
        permissoes["configuracoes"] = st.checkbox("Configurações", value=user["configuracoes"])
        permissoes["usuarios"] = st.checkbox("Usuários", value=user["usuarios"])

    st.divider()

    # =====================================
    # SALVAR
    # =====================================
    if st.button("💾 Salvar Permissões", use_container_width=True):

        salvar_permissoes(user["id"], permissoes)

        st.success("Permissões atualizadas com sucesso!")

        st.rerun()