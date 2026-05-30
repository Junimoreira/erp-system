from streamlit_option_menu import option_menu
import streamlit as st


def exibir_menu_horizontal():

    st.markdown("""
    <style>

    .main {
        padding-top: 0rem;
    }

    div[data-testid="stSidebar"] {
        display: none;
    }

    .menu-superior {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }

    </style>
    """, unsafe_allow_html=True)

    menu = option_menu(
        menu_title="ERP Verde Infância",

        options=[
            "Dashboard",
            "Comercial",
            "Financeiro",
            "Estoque",
            "Relatórios",
            "Administração"
        ],

        icons=[
            "house",
            "cart",
            "cash",
            "boxes",
            "bar-chart",
            "gear"
        ],

        orientation="horizontal",

        default_index=0
    )

    return menu