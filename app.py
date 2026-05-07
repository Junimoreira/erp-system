import streamlit as st

from telas.login import tela_login

st.set_page_config(
    page_title="ERP Empresarial",
    layout="wide"
)

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if st.session_state["logado"]:

    st.sidebar.success(
        f"👤 {st.session_state['usuario']}"
    )

    st.title("🚀 ERP Empresarial")

else:
    tela_login()