# telas/usuarios.py

import streamlit as st
import pandas as pd
import bcrypt
from database.connection import conectar


# ==================================================
# LISTAR USUÁRIOS
# ==================================================
def listar_usuarios():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                nome,
                usuario,
                perfil,
                ativo,

                pode_dashboard,
                pode_caixa,
                pode_clientes,
                pode_produtos,
                pode_vendas,
                pode_financeiro,
                pode_contas_pagar,
                pode_contas_receber,
                pode_movimentacoes,
                pode_relatorios,
                pode_configuracoes,
                pode_usuarios,
                pode_fechamento_caixa

            FROM usuarios
            ORDER BY nome
        """

        return pd.read_sql(query, conn)

    except Exception as erro:
        st.error(f"Erro ao listar usuários: {erro}")
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# CRIAR USUÁRIO
# ==================================================
def criar_usuario(nome, usuario, senha, perfil, permissoes):

    conn = conectar()
    cursor = conn.cursor()

    try:

        senha_hash = bcrypt.hashpw(
            senha.encode(),
            bcrypt.gensalt()
        ).decode()

        campos = ", ".join(permissoes.keys())
        valores_placeholder = ", ".join(["%s"] * len(permissoes))

        query = f"""
            INSERT INTO usuarios (
                nome,
                usuario,
                senha,
                perfil,
                ativo,
                {campos}
            )
            VALUES (
                %s, %s, %s, %s, TRUE,
                {valores_placeholder}
            )
        """

        valores = [
            nome,
            usuario,
            senha_hash,
            perfil,
            *permissoes.values()
        ]

        cursor.execute(query, valores)
        conn.commit()

        return True

    except Exception as erro:
        conn.rollback()
        st.error(f"Erro ao criar usuário: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR PERMISSÕES
# ==================================================
def atualizar_permissoes(usuario_id, permissoes):

    conn = conectar()
    cursor = conn.cursor()

    try:

        campos = []
        valores = []

        for campo, valor in permissoes.items():
            campos.append(f"{campo} = %s")
            valores.append(valor)

        valores.append(usuario_id)

        query = f"""
            UPDATE usuarios
            SET {', '.join(campos)}
            WHERE id = %s
        """

        cursor.execute(query, valores)
        conn.commit()

        return True

    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao atualizar permissões: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ALTERAR STATUS
# ==================================================
def alterar_status(usuario_id, ativo):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE usuarios
            SET ativo = %s
            WHERE id = %s
        """, (ativo, usuario_id))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        st.error(f"Erro ao alterar status: {erro}")
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# TELA USUÁRIOS
# ==================================================
def tela_usuarios():

    st.title("👥 Usuários e Permissões")

    abas = st.tabs(["👤 Usuários", "➕ Novo Usuário"])

    # ==================================================
    # LISTAGEM
    # ==================================================
    with abas[0]:

        df = listar_usuarios()

        if df.empty:
            st.info("Nenhum usuário cadastrado.")
            return

        st.dataframe(df, use_container_width=True)
        st.divider()

        usuarios_dict = {
            f"{row['nome']} ({row['usuario']})": row
            for _, row in df.iterrows()
        }

        usuario_sel = st.selectbox(
            "Selecione o usuário",
            list(usuarios_dict.keys())
        )

        dados = usuarios_dict[usuario_sel]

        st.subheader("Permissões do Sistema")

        col1, col2, col3 = st.columns(3)

        with col1:
            pode_caixa = st.checkbox("Caixa", value=bool(dados.get("pode_caixa", False)))
            pode_clientes = st.checkbox("Clientes", value=bool(dados.get("pode_clientes", False)))
            pode_produtos = st.checkbox("Produtos", value=bool(dados.get("pode_produtos", False)))
            pode_vendas = st.checkbox("Vendas", value=bool(dados.get("pode_vendas", False)))

        with col2:
            pode_financeiro = st.checkbox("Financeiro", value=bool(dados.get("pode_financeiro", False)))
            pode_contas_pagar = st.checkbox("Contas a Pagar", value=bool(dados.get("pode_contas_pagar", False)))
            pode_contas_receber = st.checkbox("Contas a Receber", value=bool(dados.get("pode_contas_receber", False)))
            pode_movimentacoes = st.checkbox("Movimentações", value=bool(dados.get("pode_movimentacoes", False)))

        with col3:
            pode_relatorios = st.checkbox("Relatórios", value=bool(dados.get("pode_relatorios", False)))
            pode_configuracoes = st.checkbox("Configurações", value=bool(dados.get("pode_configuracoes", False)))
            pode_usuarios = st.checkbox("Usuários", value=bool(dados.get("pode_usuarios", False)))
            pode_fechamento_caixa = st.checkbox("Fechamento Caixa", value=bool(dados.get("pode_fechamento_caixa", False)))

        if st.button("💾 Salvar Permissões"):

            permissoes = {
                "pode_caixa": pode_caixa,
                "pode_clientes": pode_clientes,
                "pode_produtos": pode_produtos,
                "pode_vendas": pode_vendas,
                "pode_financeiro": pode_financeiro,
                "pode_contas_pagar": pode_contas_pagar,
                "pode_contas_receber": pode_contas_receber,
                "pode_movimentacoes": pode_movimentacoes,
                "pode_relatorios": pode_relatorios,
                "pode_configuracoes": pode_configuracoes,
                "pode_usuarios": pode_usuarios,
                "pode_fechamento_caixa": pode_fechamento_caixa
            }

            sucesso = atualizar_permissoes(int(dados["id"]), permissoes)

            if sucesso:
                st.success("✅ Permissões atualizadas!")
                st.rerun()

        st.divider()

        ativo = st.checkbox("Usuário ativo", value=bool(dados["ativo"]))

        if st.button("🔄 Atualizar Status"):
            if alterar_status(int(dados["id"]), ativo):
                st.success("✅ Status atualizado!")
                st.rerun()

    # ==================================================
    # NOVO USUÁRIO
    # ==================================================
    with abas[1]:

        nome = st.text_input("Nome")
        usuario = st.text_input("Login")
        senha = st.text_input("Senha", type="password")

        perfil = st.selectbox("Perfil", ["diretor", "admin", "atendente"])

        st.subheader("Permissões")

        pode_caixa = st.checkbox("Caixa", True)
        pode_clientes = st.checkbox("Clientes", True)
        pode_produtos = st.checkbox("Produtos", True)
        pode_vendas = st.checkbox("Vendas", True)

        pode_financeiro = st.checkbox("Financeiro")
        pode_contas_pagar = st.checkbox("Contas a Pagar")
        pode_contas_receber = st.checkbox("Contas a Receber")
        pode_movimentacoes = st.checkbox("Movimentações")

        pode_relatorios = st.checkbox("Relatórios")
        pode_configuracoes = st.checkbox("Configurações")
        pode_usuarios = st.checkbox("Usuários")
        pode_fechamento_caixa = st.checkbox("Fechamento Caixa")

        if st.button("🚀 Criar Usuário"):

            if not nome or not usuario or not senha:
                st.warning("Preencha todos os campos.")
                return

            permissoes = {
                "pode_caixa": pode_caixa,
                "pode_clientes": pode_clientes,
                "pode_produtos": pode_produtos,
                "pode_vendas": pode_vendas,
                "pode_financeiro": pode_financeiro,
                "pode_contas_pagar": pode_contas_pagar,
                "pode_contas_receber": pode_contas_receber,
                "pode_movimentacoes": pode_movimentacoes,
                "pode_relatorios": pode_relatorios,
                "pode_configuracoes": pode_configuracoes,
                "pode_usuarios": pode_usuarios,
                "pode_fechamento_caixa": pode_fechamento_caixa
            }

            if criar_usuario(nome, usuario, senha, perfil, permissoes):
                st.success("✅ Usuário criado!")
                st.rerun()