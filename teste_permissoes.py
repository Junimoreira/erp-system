import streamlit as st

from telas.painel_admin_permissoes import (
    tela_painel_permissoes
)

st.set_page_config(layout="wide")

tela_painel_permissoes()