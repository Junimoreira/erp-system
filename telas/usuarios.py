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

                pode_caixa,
                pode_vendas,
                pode_produtos,
                pode_clientes,
                pode_financeiro,
                pode_configuracoes,
                pode_usuarios

            FROM usuarios

            ORDER BY nome
        """

        df = pd.read_sql(query, conn)

        return df

    except Exception as erro:

        st.error(f"Erro ao listar usuários: {erro}")

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# CRIAR USUÁRIO
# ==================================================
def criar_usuario(

    nome,
    usuario,
    senha,
    perfil,

    pode_caixa,
    pode_vendas,
    pode_produtos,
    pode_clientes,
    pode_financeiro,
    pode_configuracoes,
    pode_usuarios
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        senha_hash = bcrypt.hashpw(
            senha.encode(),
            bcrypt.gensalt()
        ).decode()

        cursor.execute("""

            INSERT INTO usuarios (

                nome,
                usuario,
                senha,
                perfil,
                ativo,

                pode_caixa,
                pode_vendas,
                pode_produtos,
                pode_clientes,
                pode_financeiro,
                pode_configuracoes,
                pode_usuarios

            )

            VALUES (

                %s,
                %s,
                %s,
                %s,
                TRUE,

                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s

            )

        """, (

            nome,
            usuario,
            senha_hash,
            perfil,

            pode_caixa,
            pode_vendas,
            pode_produtos,
            pode_clientes,
            pode_financeiro,
            pode_configuracoes,
            pode_usuarios

        ))

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
def atualizar_permissoes(

    usuario_id,

    pode_caixa,
    pode_vendas,
    pode_produtos,
    pode_clientes,
    pode_financeiro,
    pode_configuracoes,
    pode_usuarios

):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""

            UPDATE usuarios

            SET

                pode_caixa = %s,
                pode_vendas = %s,
                pode_produtos = %s,
                pode_clientes = %s,
                pode_financeiro = %s,
                pode_configuracoes = %s,
                pode_usuarios = %s

            WHERE id = %s

        """, (

            pode_caixa,
            pode_vendas,
            pode_produtos,
            pode_clientes,
            pode_financeiro,
            pode_configuracoes,
            pode_usuarios,

            usuario_id

        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        st.error(f"Erro ao atualizar permissões: {erro}")

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATIVAR / DESATIVAR
# ==================================================
def alterar_status(usuario_id, ativo):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""

            UPDATE usuarios

            SET ativo = %s

            WHERE id = %s

        """, (

            ativo,
            usuario_id

        ))

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

    abas = st.tabs([

        "👤 Usuários",
        "➕ Novo Usuário"

    ])

    # ==================================================
    # LISTAGEM
    # ==================================================
    with abas[0]:

        st.subheader("Usuários cadastrados")

        df = listar_usuarios()

        if not df.empty:

            st.dataframe(
                df,
                width="stretch"
            )

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

            st.subheader("Permissões")

            pode_caixa = st.checkbox(
                "Caixa",
                value=bool(dados["pode_caixa"])
            )

            pode_vendas = st.checkbox(
                "Vendas",
                value=bool(dados["pode_vendas"])
            )

            pode_produtos = st.checkbox(
                "Produtos",
                value=bool(dados["pode_produtos"])
            )

            pode_clientes = st.checkbox(
                "Clientes",
                value=bool(dados["pode_clientes"])
            )

            pode_financeiro = st.checkbox(
                "Financeiro",
                value=bool(dados["pode_financeiro"])
            )

            pode_configuracoes = st.checkbox(
                "Configurações",
                value=bool(dados["pode_configuracoes"])
            )

            pode_usuarios = st.checkbox(
                "Usuários",
                value=bool(dados["pode_usuarios"])
            )

            if st.button("💾 Salvar Permissões"):

                sucesso = atualizar_permissoes(

                    usuario_id=int(dados["id"]),

                    pode_caixa=pode_caixa,
                    pode_vendas=pode_vendas,
                    pode_produtos=pode_produtos,
                    pode_clientes=pode_clientes,
                    pode_financeiro=pode_financeiro,
                    pode_configuracoes=pode_configuracoes,
                    pode_usuarios=pode_usuarios
                )

                if sucesso:

                    st.success(
                        "✅ Permissões atualizadas!"
                    )

                    st.rerun()

            st.divider()

            ativo = st.checkbox(
                "Usuário ativo",
                value=bool(dados["ativo"])
            )

            if st.button("🔄 Atualizar Status"):

                sucesso = alterar_status(

                    usuario_id=int(dados["id"]),
                    ativo=ativo

                )

                if sucesso:

                    st.success(
                        "✅ Status atualizado!"
                    )

                    st.rerun()

        else:

            st.info("Nenhum usuário cadastrado.")

    # ==================================================
    # NOVO USUÁRIO
    # ==================================================
    with abas[1]:

        st.subheader("Cadastrar novo usuário")

        nome = st.text_input("Nome")

        usuario = st.text_input("Login")

        senha = st.text_input(
            "Senha",
            type="password"
        )

        perfil = st.selectbox(

            "Perfil",

            [
                "Diretor",
                "Administrador",
                "Atendente"
            ]

        )

        st.divider()

        st.subheader("Permissões")

        pode_caixa = st.checkbox("Caixa", value=True)

        pode_vendas = st.checkbox("Vendas", value=True)

        pode_produtos = st.checkbox("Produtos", value=True)

        pode_clientes = st.checkbox("Clientes", value=True)

        pode_financeiro = st.checkbox("Financeiro")

        pode_configuracoes = st.checkbox("Configurações")

        pode_usuarios = st.checkbox("Usuários")

        if st.button("🚀 Criar Usuário"):

            if nome == "" or usuario == "" or senha == "":

                st.warning(
                    "Preencha todos os campos."
                )

            else:

                sucesso = criar_usuario(

                    nome=nome,
                    usuario=usuario,
                    senha=senha,
                    perfil=perfil,

                    pode_caixa=pode_caixa,
                    pode_vendas=pode_vendas,
                    pode_produtos=pode_produtos,
                    pode_clientes=pode_clientes,
                    pode_financeiro=pode_financeiro,
                    pode_configuracoes=pode_configuracoes,
                    pode_usuarios=pode_usuarios
                )

                if sucesso:

                    st.success(
                        "✅ Usuário criado!"
                    )

                    st.rerun()