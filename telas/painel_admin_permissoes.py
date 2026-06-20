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
            configuracoes,
            usuarios,
            cadastrar_produto,
            ver_contas,
            ver_despesas,

            pode_movimentacoes,
            pode_fechamento_caixa,
            pode_contas_pagar,
            pode_contas_receber,
            pode_financeiro

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
                configuracoes = %s,
                usuarios = %s,
                cadastrar_produto = %s,
                ver_contas = %s,
                ver_despesas = %s,

                pode_movimentacoes = %s,
                pode_fechamento_caixa = %s,
                pode_contas_pagar = %s,
                pode_contas_receber = %s,
                pode_financeiro = %s
            WHERE id = %s
        """, (

            dados["abrir_caixa"],
            dados["fechar_caixa"],
            dados["realizar_venda"],
            dados["cadastrar_cliente"],
            dados["ver_financeiro"],
            dados["configuracoes"],
            dados["usuarios"],
            dados["cadastrar_produto"],
            dados["ver_contas"],
            dados["ver_despesas"],

            dados["pode_movimentacoes"],
            dados["pode_fechamento_caixa"],
            dados["pode_contas_pagar"],
            dados["pode_contas_receber"],
            dados["pode_financeiro"],
            user_id

        ))

        conn.commit()
        return True

    except Exception as erro:
        print("Erro ao salvar permissões:", erro)
        conn.rollback()
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

    lista_nomes = [
        f"{u['nome']} ({u['perfil']})"
        for u in usuarios
    ]

    selecionado = st.selectbox(
        "Selecionar usuário",
        lista_nomes
    )

    user = usuarios[lista_nomes.index(selecionado)]

    st.divider()
    st.subheader(f"👤 {user['nome']}")

    perfil = str(user["perfil"]).strip().lower()

    if perfil in ["admin", "diretor"]:
        st.success("Este usuário possui acesso administrativo total.")
        st.info("Permissões administrativas não precisam ser editadas.")
        return

    permissoes = {}

    col1, col2 = st.columns(2)

    with col1:

        permissoes["abrir_caixa"] = st.checkbox(
            "Abrir Caixa",
            value=bool(user.get("abrir_caixa", False))
        )

        permissoes["fechar_caixa"] = st.checkbox(
            "Fechar Caixa",
            value=bool(user.get("fechar_caixa", False))
        )

        permissoes["realizar_venda"] = st.checkbox(
            "Realizar Venda",
            value=bool(user.get("realizar_venda", False))
        )

        permissoes["cadastrar_cliente"] = st.checkbox(
            "Cadastrar Cliente",
            value=bool(user.get("cadastrar_cliente", False))
        )

        permissoes["cadastrar_produto"] = st.checkbox(
            "Cadastrar Produto",
            value=bool(user.get("cadastrar_produto", False))
        )

        permissoes["ver_contas"] = st.checkbox(
            "Ver Contas",
            value=bool(user.get("ver_contas", False))
        )

        permissoes["pode_movimentacoes"] = st.checkbox(
            "Movimentações",
            value=bool(user.get("pode_movimentacoes", False))
        )

    with col2:

        permissoes["ver_financeiro"] = st.checkbox(
            "Ver Financeiro",
            value=bool(user.get("ver_financeiro", False))
        )

        permissoes["pode_financeiro"] = st.checkbox(
            "Contas Bancárias / Fluxo de Caixa",
            value=bool(user.get("pode_financeiro", False))
        )

        permissoes["pode_contas_pagar"] = st.checkbox(
            "Contas a Pagar",
            value=bool(user.get("pode_contas_pagar", False))
        )

        permissoes["pode_contas_receber"] = st.checkbox(
            "Contas a Receber",
            value=bool(user.get("pode_contas_receber", False))
        )

        permissoes["pode_fechamento_caixa"] = st.checkbox(
            "Fechamento de Caixa",
            value=bool(user.get("pode_fechamento_caixa", False))
        )

        permissoes["configuracoes"] = st.checkbox(
            "Configurações",
            value=bool(user.get("configuracoes", False))
        )

        permissoes["usuarios"] = st.checkbox(
            "Usuários",
            value=bool(user.get("usuarios", False))
        )

        permissoes["ver_despesas"] = st.checkbox(
            "Ver Despesas",
            value=bool(user.get("ver_despesas", False))
        )

    st.divider()

    if st.button(
        "💾 Salvar Permissões",
        use_container_width=True
    ):

        sucesso = salvar_permissoes(
            user["id"],
            permissoes
        )

        if sucesso:
            st.success("✅ Permissões atualizadas com sucesso!")
            st.info("Peça para o usuário sair e entrar novamente no sistema.")
            st.rerun()

        else:
            st.error("❌ Erro ao salvar permissões.")