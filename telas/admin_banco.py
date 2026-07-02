import streamlit as st
import pandas as pd

from services.backup_service import (
    criar_backup,
    listar_backups,
    restaurar_backup
)


def tela_admin_banco():

    st.title("💾 Administração do Banco")

    st.info(
        "Este módulo é responsável pela segurança do banco de dados, backups e futuras migrações do ERP."
    )

    abas = st.tabs([
        "💾 Backup",
        "📜 Histórico",
        "🔄 Restaurar"
    ])

    with abas[0]:

        st.subheader("Criar Backup")

        st.write(
            "Clique no botão abaixo para gerar um backup completo do banco de dados."
        )

        if st.button(
            "💾 Gerar Backup Agora",
            use_container_width=True
        ):

            with st.spinner("Gerando backup..."):

                resultado = criar_backup()

            if resultado["sucesso"]:
                st.success(resultado["mensagem"])
                st.code(resultado["arquivo"])
            else:
                st.error(resultado["mensagem"])

    with abas[1]:

        st.subheader("Backups Disponíveis")

        backups = listar_backups()

        if len(backups) == 0:
            st.info("Nenhum backup encontrado.")

        else:
            df = pd.DataFrame(backups)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.success(
                f"{len(df)} backup(s) encontrado(s)."
            )

    with abas[2]:

        st.subheader("🔄 Restaurar Backup")

        st.warning(
            "Atenção: restaurar um backup substitui os dados atuais do banco. "
            "Use apenas se tiver certeza."
        )

        backups = listar_backups()

        if len(backups) == 0:
            st.info("Nenhum backup disponível para restauração.")

        else:
            opcoes = {
                f"{b['arquivo']} | {b['data']} | {b['tamanho_mb']} MB": b["caminho"]
                for b in backups
            }

            selecionado = st.selectbox(
                "Selecione o backup para restaurar",
                list(opcoes.keys())
            )

            caminho_backup = opcoes[selecionado]

            confirmar = st.checkbox(
                "Confirmo que desejo restaurar este backup",
                key="confirmar_restaurar_backup"
            )

            confirmar_final = st.checkbox(
                "Entendo que os dados atuais poderão ser substituídos",
                key="confirmar_restaurar_backup_final"
            )

            if st.button(
                "🔄 Restaurar Backup Selecionado",
                use_container_width=True
            ):

                if not confirmar or not confirmar_final:
                    st.warning("Marque as duas confirmações antes de restaurar.")
                    return

                with st.spinner("Restaurando backup..."):

                    resultado = restaurar_backup(caminho_backup)

                if resultado["sucesso"]:
                    st.success(resultado["mensagem"])
                    st.info("Reinicie o sistema após a restauração.")
                else:
                    st.error(resultado["mensagem"])