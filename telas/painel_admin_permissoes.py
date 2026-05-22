import streamlit as st
from database.connection import conectar


# =====================================
# CARREGAR USUÁRIOS
# =====================================
def listar_usuarios():

    conn = conectar()

    if conn is None:
        return []

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
            cadastrar_produto,
            ver_contas,
            ver_despesas

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

    if conn is None:
        return False

    cur = conn.cursor()

    try:

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
                cadastrar_produto = %s,
                ver_contas = %s,
                ver_despesas = %s
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
            dados["ver_contas"],
            dados["ver_despesas"],

            user_id
        ))

        conn.commit()

        return True

    except Exception as erro:

        print(
            "Erro ao salvar permissões:",
            erro
        )

        return False

    finally:

        cur.close()
        conn.close()


# =====================================
# TELA ADMIN
# =====================================
def tela_painel_permissoes():

    st.title("🔐 Painel de Permissões")

    usuarios = listar_usuarios()

    if not usuarios:
        st.warning("Nenhum usuário encontrado.")
        return

    # =====================================
    # SELECT USUÁRIO
    # =====================================
    lista_nomes = [
        f"{u['nome']} ({u['perfil']})"
        for u in usuarios
    ]

    selecionado = st.selectbox(
        "Selecionar usuário",
        lista_nomes
    )

    user = usuarios[
        lista_nomes.index(selecionado)
    ]

    st.divider()

    st.subheader(f"👤 {user['nome']}")

    # =====================================
    # ADMIN / DIRETOR
    # =====================================
    perfil = str(
        user["perfil"]
    ).strip().lower()

    if perfil in ["admin", "diretor"]:

        st.success(
            "Este usuário possui acesso administrativo total."
        )

        st.info(
            "Permissões administrativas não precisam ser editadas."
        )

        return

    # =====================================
    # CHECKBOXES
    # =====================================
    col1, col2 = st.columns(2)

    permissoes = {}

    # =====================================
    # COLUNA 1
    # =====================================
    with col1:

        permissoes["abrir_caixa"] = st.checkbox(
            "Abrir Caixa",
            value=bool(user["abrir_caixa"])
        )

        permissoes["fechar_caixa"] = st.checkbox(
            "Fechar Caixa",
            value=bool(user["fechar_caixa"])
        )

        permissoes["realizar_venda"] = st.checkbox(
            "Realizar Venda",
            value=bool(user["realizar_venda"])
        )

        permissoes["cadastrar_cliente"] = st.checkbox(
            "Cadastrar Cliente",
            value=bool(user["cadastrar_cliente"])
        )

        permissoes["cadastrar_produto"] = st.checkbox(
            "Cadastrar Produto",
            value=bool(user["cadastrar_produto"])
        )

        permissoes["ver_contas"] = st.checkbox(
            "Contas",
            value=bool(user["ver_contas"])
        )

    # =====================================
    # COLUNA 2
    # =====================================
    with col2:

        permissoes["ver_financeiro"] = st.checkbox(
            "Ver Financeiro",
            value=bool(user["ver_financeiro"])
        )

        permissoes["contas_pagar"] = st.checkbox(
            "Contas a Pagar",
            value=bool(user["contas_pagar"])
        )

        permissoes["configuracoes"] = st.checkbox(
            "Configurações",
            value=bool(user["configuracoes"])
        )

        permissoes["usuarios"] = st.checkbox(
            "Usuários",
            value=bool(user["usuarios"])
        )

        permissoes["ver_despesas"] = st.checkbox(
            "Despesas",
            value=bool(user["ver_despesas"])
        )

    st.divider()

    # =====================================
    # BOTÃO SALVAR
    # =====================================
    if st.button(
        "💾 Salvar Permissões",
        use_container_width=True
    ):

        sucesso = salvar_permissoes(
            user["id"],
            permissoes
        )

        if sucesso:

            st.success(
                "✅ Permissões atualizadas com sucesso!"
            )

            st.rerun()

        else:

            st.error(
                "❌ Erro ao salvar permissões."
            )