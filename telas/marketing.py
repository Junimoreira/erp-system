import streamlit as st
import pandas as pd
from urllib.parse import quote

from database.marketing_db import (
    listar_aniversariantes_mes,
    listar_clientes_inativos,
    listar_top_clientes
)


# ==================================================
# WHATSAPP
# ==================================================
def gerar_link_whatsapp(telefone, mensagem):

    telefone = (
        str(telefone)
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if telefone.startswith("0"):
        telefone = telefone[1:]

    if not telefone.startswith("55"):
        telefone = "55" + telefone

    mensagem_url = quote(mensagem)

    return f"https://wa.me/{telefone}?text={mensagem_url}"


# ==================================================
# TELA MARKETING
# ==================================================
def tela_marketing():

    st.title("📢 Marketing")

    abas = st.tabs([
        "🎂 Aniversariantes do Mês",
        "😴 Clientes Inativos",
        "🏆 Top Clientes"
    ])

# ==================================================
# TOP CLIENTES
# ==================================================
    with abas[2]:

        st.subheader("🏆 Top Clientes")

        limite = st.number_input(
            "Quantidade de clientes no ranking",
            min_value=5,
            max_value=100,
            value=20,
            step=5
        )

        df_top = listar_top_clientes(
            limit=int(limite)
        )

        if df_top.empty:

            st.info("Nenhuma venda encontrada para gerar ranking.")

        else:

            df_top = df_top.copy()

            df_top["ultima_compra"] = pd.to_datetime(
                df_top["ultima_compra"],
                errors="coerce"
            ).dt.strftime("%d/%m/%Y")

            df_top["total_comprado"] = df_top["total_comprado"].astype(float)
            df_top["ticket_medio"] = df_top["ticket_medio"].astype(float)

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Clientes no ranking",
                len(df_top)
            )

            col2.metric(
                "Total comprado",
                f"R$ {df_top['total_comprado'].sum():,.2f}"
            )

            col3.metric(
                "Ticket médio geral",
                f"R$ {df_top['ticket_medio'].mean():,.2f}"
            )

            st.dataframe(
                df_top,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader("📲 Campanha para cliente VIP")

            clientes_top = {
                f"{row['nome']} - R$ {float(row['total_comprado']):,.2f}": row
                for _, row in df_top.iterrows()
            }

            selecionado_top = st.selectbox(
                "Selecione o cliente",
                list(clientes_top.keys()),
                key="cliente_top_select"
            )

            cliente = clientes_top[selecionado_top]

            mensagem = st.text_area(
                "Mensagem para cliente VIP",
                value=f"""Olá {cliente['nome']}! 🌱

Você está entre nossos clientes especiais da Verde Infância. 💚

Preparamos novidades em brinquedos educativos, papelaria e materiais escolares, e será um prazer receber você novamente em nossa loja.

Como cliente especial, apresente esta mensagem em sua próxima visita e receba um carinho exclusivo.

Com carinho,
Equipe Verde Infância 🎁""",
                key="mensagem_cliente_top"
            )

            telefone = cliente.get("telefone", "")

            if not telefone:

                st.warning("Este cliente não possui telefone cadastrado.")

            else:

                link = gerar_link_whatsapp(
                    telefone,
                    mensagem
                )

                st.link_button(
                    "📲 Abrir WhatsApp",
                    link,
                    use_container_width=True
                )

    # ==================================================
    # ANIVERSARIANTES
    # ==================================================
    with abas[0]:

        st.subheader("🎂 Aniversariantes do Mês")

        df = listar_aniversariantes_mes()

        if df.empty:

            st.info(
                "Nenhum aniversariante encontrado neste mês."
            )

        else:

            df = df.copy()

            df["data_nascimento"] = pd.to_datetime(
                df["data_nascimento"],
                errors="coerce"
            ).dt.strftime("%d/%m")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader(
                "📲 Enviar mensagem pelo WhatsApp"
            )

            clientes = {
                f"{row['nome']} - {row['data_nascimento']}": row
                for _, row in df.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione o cliente",
                list(clientes.keys()),
                key="aniversariante_select"
            )

            cliente = clientes[selecionado]

            mensagem = st.text_area(
                "Mensagem",
                value=f"""Olá {cliente['nome']}! 🎉

A Verde Infância deseja um feliz aniversário cheio de alegria, carinho e momentos especiais.

Para comemorar com você, preparamos um carinho especial: apresente esta mensagem na loja e ganhe 10% de desconto em sua próxima compra.

Com carinho,
Equipe Verde Infância 🌱""",
                key="mensagem_aniversario"
            )

            telefone = cliente.get(
                "telefone",
                ""
            )

            if not telefone:

                st.warning(
                    "Este cliente não possui telefone cadastrado."
                )

            else:

                link = gerar_link_whatsapp(
                    telefone,
                    mensagem
                )

                st.link_button(
                    "📲 Abrir WhatsApp",
                    link,
                    use_container_width=True
                )

    # ==================================================
    # CLIENTES INATIVOS
    # ==================================================
    with abas[1]:

        st.subheader("😴 Clientes Inativos")

        dias = st.number_input(
            "Considerar inativo após quantos dias sem comprar?",
            min_value=30,
            max_value=365,
            value=90,
            step=30
        )

        df_inativos = listar_clientes_inativos(
            dias=int(dias)
        )

        if df_inativos.empty:

            st.success(
                "Nenhum cliente inativo encontrado para esse período."
            )

        else:

            df_inativos = df_inativos.copy()

            if "ultima_compra" in df_inativos.columns:

                df_inativos["ultima_compra"] = pd.to_datetime(
                    df_inativos["ultima_compra"],
                    errors="coerce"
                ).dt.strftime("%d/%m/%Y")

            st.metric(
                "Clientes Inativos",
                len(df_inativos)
            )

            st.dataframe(
                df_inativos,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            st.subheader(
                "📲 Reativar cliente pelo WhatsApp"
            )

            clientes_inativos = {
                f"{row['nome']} - {row['dias_sem_comprar']} dias": row
                for _, row in df_inativos.iterrows()
            }

            selecionado = st.selectbox(
                "Selecione o cliente",
                list(clientes_inativos.keys()),
                key="cliente_inativo_select"
            )

            cliente = clientes_inativos[
                selecionado
            ]

            mensagem = st.text_area(
                "Mensagem de reativação",
                value=f"""Olá {cliente['nome']}! 🌱

Sentimos sua falta aqui na Verde Infância.

Estamos com novidades em brinquedos educativos, papelaria e materiais escolares.

Será um prazer receber você novamente em nossa loja.

Apresente esta mensagem e ganhe um carinho especial em sua próxima compra.

Com carinho,
Equipe Verde Infância 💚""",
                key="mensagem_cliente_inativo"
            )

            telefone = cliente.get(
                "telefone",
                ""
            )

            if not telefone:

                st.warning(
                    "Este cliente não possui telefone cadastrado."
                )

            else:

                link = gerar_link_whatsapp(
                    telefone,
                    mensagem
                )

                st.link_button(
                    "📲 Abrir WhatsApp",
                    link,
                    use_container_width=True
                )