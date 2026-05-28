# telas/painel_admin_permissoes.py

import streamlit as st

from database.connection import conectar


# ==================================================
# LISTAR USUÁRIOS
# ==================================================
def listar_usuarios():

    conn = conectar()

    if conn is None:
        return []

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                id,
                usuario,
                perfil,

                pode_caixa,
                pode_clientes,
                pode_produtos,
                pode_vendas,
                pode_financeiro,
                pode_contas_pagar,
                pode_contas_receber,
                pode_configuracoes,

                pode_formacao_preco,
                pode_fornecedores,
                pode_compras,
                pode_relatorios,
                pode_fechamento_caixa,
                pode_movimentacoes

            FROM usuarios
            ORDER BY usuario
        """)

        colunas = [
            desc[0]
            for desc in cursor.description
        ]

        usuarios = []

        for linha in cursor.fetchall():

            usuarios.append(
                dict(
                    zip(colunas, linha)
                )
            )

        return usuarios

    except Exception as erro:

        st.error(
            f"Erro ao listar usuários: {erro}"
        )

        return []

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR PERMISSÕES
# ==================================================
def atualizar_permissoes(
    usuario_id,
    permissoes
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
                pode_clientes = %s,
                pode_produtos = %s,
                pode_vendas = %s,
                pode_financeiro = %s,
                pode_contas_pagar = %s,
                pode_contas_receber = %s,
                pode_configuracoes = %s,

                pode_formacao_preco = %s,
                pode_fornecedores = %s,
                pode_compras = %s,
                pode_relatorios = %s,
                pode_fechamento_caixa = %s,
                pode_movimentacoes = %s

            WHERE id = %s
        """, (

            permissoes["pode_caixa"],
            permissoes["pode_clientes"],
            permissoes["pode_produtos"],
            permissoes["pode_vendas"],
            permissoes["pode_financeiro"],
            permissoes["pode_contas_pagar"],
            permissoes["pode_contas_receber"],
            permissoes["pode_configuracoes"],

            permissoes["pode_formacao_preco"],
            permissoes["pode_fornecedores"],
            permissoes["pode_compras"],
            permissoes["pode_relatorios"],
            permissoes["pode_fechamento_caixa"],
            permissoes["pode_movimentacoes"],

            usuario_id
        ))

        conn.commit()

        return True

    except Exception as erro:

        st.error(
            f"Erro ao atualizar permissões: {erro}"
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# TELA PERMISSÕES
# ==================================================
def tela_painel_permissoes():

    st.title(
        "🔐 Painel de Permissões"
    )

    usuarios = listar_usuarios()

    if not usuarios:

        st.warning(
            "Nenhum usuário encontrado."
        )

        return

    nomes_usuarios = [
        usuario["usuario"]
        for usuario in usuarios
    ]

    usuario_nome = st.selectbox(
        "Selecione o usuário",
        nomes_usuarios
    )

    usuario = next(
        (
            u for u in usuarios
            if u["usuario"] == usuario_nome
        ),
        None
    )

    if usuario is None:

        st.error(
            "Usuário não encontrado."
        )

        return

    st.divider()

    st.subheader(
        f"Permissões de {usuario_nome}"
    )

    col1, col2 = st.columns(2)

    with col1:

        pode_caixa = st.checkbox(
            "💰 Caixa",
            value=usuario.get(
                "pode_caixa",
                False
            )
        )

        pode_clientes = st.checkbox(
            "👥 Clientes",
            value=usuario.get(
                "pode_clientes",
                False
            )
        )

        pode_produtos = st.checkbox(
            "📦 Produtos",
            value=usuario.get(
                "pode_produtos",
                False
            )
        )

        pode_vendas = st.checkbox(
            "🛒 Vendas",
            value=usuario.get(
                "pode_vendas",
                False
            )
        )

        pode_financeiro = st.checkbox(
            "🏦 Contas",
            value=usuario.get(
                "pode_financeiro",
                False
            )
        )

        pode_contas_pagar = st.checkbox(
            "📤 Contas a Pagar",
            value=usuario.get(
                "pode_contas_pagar",
                False
            )
        )

        pode_contas_receber = st.checkbox(
            "📥 Contas a Receber",
            value=usuario.get(
                "pode_contas_receber",
                False
            )
        )

    with col2:

        pode_formacao_preco = st.checkbox(
            "💰 Formação de Preço",
            value=usuario.get(
                "pode_formacao_preco",
                False
            )
        )

        pode_fornecedores = st.checkbox(
            "🚚 Fornecedores",
            value=usuario.get(
                "pode_fornecedores",
                False
            )
        )

        pode_compras = st.checkbox(
            "📥 Compras",
            value=usuario.get(
                "pode_compras",
                False
            )
        )

        pode_relatorios = st.checkbox(
            "📊 Relatórios",
            value=usuario.get(
                "pode_relatorios",
                False
            )
        )

        pode_fechamento_caixa = st.checkbox(
            "📊 Fechamento Caixa",
            value=usuario.get(
                "pode_fechamento_caixa",
                False
            )
        )

        pode_movimentacoes = st.checkbox(
            "💰 Movimentações",
            value=usuario.get(
                "pode_movimentacoes",
                False
            )
        )

        pode_configuracoes = st.checkbox(
            "⚙️ Configurações",
            value=usuario.get(
                "pode_configuracoes",
                False
            )
        )

    st.divider()

    if st.button(
        "💾 Salvar Permissões",
        use_container_width=True
    ):

        permissoes = {

            "pode_caixa": pode_caixa,
            "pode_clientes": pode_clientes,
            "pode_produtos": pode_produtos,
            "pode_vendas": pode_vendas,
            "pode_financeiro": pode_financeiro,
            "pode_contas_pagar": pode_contas_pagar,
            "pode_contas_receber": pode_contas_receber,
            "pode_configuracoes": pode_configuracoes,

            "pode_formacao_preco": pode_formacao_preco,
            "pode_fornecedores": pode_fornecedores,
            "pode_compras": pode_compras,
            "pode_relatorios": pode_relatorios,
            "pode_fechamento_caixa": pode_fechamento_caixa,
            "pode_movimentacoes": pode_movimentacoes
        }

        sucesso = atualizar_permissoes(
            usuario["id"],
            permissoes
        )

        if sucesso:

            st.success(
                "✅ Permissões atualizadas com sucesso!"
            )

            st.rerun()