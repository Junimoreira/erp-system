import streamlit as st


def tem_permissao(permissao):
    return bool(st.session_state.get(permissao, False))


def bloquear_acao(permissao):

    if not tem_permissao(permissao):

        st.error("⛔ Você não tem permissão para essa ação.")
        st.stop()