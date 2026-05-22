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

                abrir_caixa,
                fechar_caixa,
                realizar_venda,
                cadastrar_cliente,
                cadastrar_produto,
                ver_financeiro,
                contas_pagar,
                configuracoes,
                usuarios,
                ver_contas,
                ver_despesas

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

    abrir_caixa,
    fechar_caixa,
    realizar_venda,
    cadastrar_cliente,
    cadastrar_produto,
    ver_financeiro,
    contas_pagar,
    configuracoes,
    usuarios,
    ver_contas,
    ver_despesas
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

                abrir_caixa,
                fechar_caixa,
                realizar_venda,
                cadastrar_cliente,
                cadastrar_produto,
                ver_financeiro,
                contas_pagar,
                configuracoes,
                usuarios,
                ver_contas,
                ver_despesas

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

            abrir_caixa,
            fechar_caixa,
            realizar_venda,
            cadastrar_cliente,
            cadastrar_produto,
            ver_financeiro,
            contas_pagar,
            configuracoes,
            usuarios,
            ver_contas,
            ver_despesas

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

    abrir_caixa,
    fechar_caixa,
    realizar_venda,
    cadastrar_cliente,
    cadastrar_produto,
    ver_financeiro,
    contas_pagar,
    configuracoes,
    usuarios,
    ver_contas,
    ver_despesas

):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""

            UPDATE usuarios

            SET

                abrir_caixa = %s,
                fechar_caixa = %s,
                realizar_venda = %s,
                cadastrar_cliente = %s,
                cadastrar_produto = %s,
                ver_financeiro = %s,
                contas_pagar = %s,
                configuracoes = %s,
                usuarios = %s,
                ver_contas = %s,
                ver_despesas = %s

            WHERE id = %s

        """, (

            abrir_caixa,
            fechar_caixa,
            realizar_venda,
            cadastrar_cliente,
            cadastrar_produto,
            ver_financeiro,
            contas_pagar,
            configuracoes,
            usuarios,
            ver_contas,
            ver_despesas,

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
                use_container_width=True
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

            col1, col2 = st.columns(2)

            with col1:

                abrir_caixa = st.checkbox(
                    "Abrir Caixa",
                    value=bool(dados["abrir_caixa"])
                )

                fechar_caixa = st.checkbox(
                    "Fechar Caixa",
                    value=bool(dados["fechar_caixa"])
                )

                realizar_venda = st.checkbox(
                    "Realizar Venda",
                    value=bool(dados["realizar_venda"])
                )

                cadastrar_cliente = st.checkbox(
                    "Cadastrar Cliente",
                    value=bool(dados["cadastrar_cliente"])
                )

                cadastrar_produto = st.checkbox(
                    "Cadastrar Produto",
                    value=bool(dados["cadastrar_produto"])
                )

                ver_contas = st.checkbox(
                    "Ver Contas",
                    value=bool(dados["ver_contas"])
                )

            with col2:

                ver_financeiro = st.checkbox(
                    "Ver Financeiro",
                    value=bool(dados["ver_financeiro"])
                )

                contas_pagar = st.checkbox(
                    "Contas a Pagar",
                    value=bool(dados["contas_pagar"])
                )

                ver_despesas = st.checkbox(
                    "Ver Despesas",
                    value=bool(dados["ver_despesas"])
                )

                configuracoes = st.checkbox(
                    "Configurações",
                    value=bool(dados["configuracoes"])
                )

                usuarios = st.checkbox(
                    "Usuários",
                    value=bool(dados["usuarios"])
                )

            if st.button("💾 Salvar Permissões"):

                sucesso = atualizar_permissoes(

                    usuario_id=int(dados["id"]),

                    abrir_caixa=abrir_caixa,
                    fechar_caixa=fechar_caixa,
                    realizar_venda=realizar_venda,
                    cadastrar_cliente=cadastrar_cliente,
                    cadastrar_produto=cadastrar_produto,
                    ver_financeiro=ver_financeiro,
                    contas_pagar=contas_pagar,
                    configuracoes=configuracoes,
                    usuarios=usuarios,
                    ver_contas=ver_contas,
                    ver_despesas=ver_despesas
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
                "diretor",
                "admin",
                "atendente"
            ]

        )

        st.divider()

        st.subheader("Permissões")

        abrir_caixa = st.checkbox("Abrir Caixa", value=True)
        fechar_caixa = st.checkbox("Fechar Caixa")
        realizar_venda = st.checkbox("Realizar Venda", value=True)
        cadastrar_cliente = st.checkbox("Cadastrar Cliente", value=True)
        cadastrar_produto = st.checkbox("Cadastrar Produto", value=True)

        ver_financeiro = st.checkbox("Ver Financeiro")
        contas_pagar = st.checkbox("Contas a Pagar")
        ver_contas = st.checkbox("Ver Contas")
        ver_despesas = st.checkbox("Ver Despesas")

        configuracoes = st.checkbox("Configurações")
        usuarios = st.checkbox("Usuários")

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

                    abrir_caixa=abrir_caixa,
                    fechar_caixa=fechar_caixa,
                    realizar_venda=realizar_venda,
                    cadastrar_cliente=cadastrar_cliente,
                    cadastrar_produto=cadastrar_produto,
                    ver_financeiro=ver_financeiro,
                    contas_pagar=contas_pagar,
                    configuracoes=configuracoes,
                    usuarios=usuarios,
                    ver_contas=ver_contas,
                    ver_despesas=ver_despesas
                )

                if sucesso:

                    st.success(
                        "✅ Usuário criado!"
                    )

                    st.rerun()