import streamlit as st

from database.contas_receber_db import (
    listar_contas_receber,
    excluir_conta_receber
)

from services.finance_service import (
    processar_entrada_financeira
)


def tela_contas_receber():

    st.title("📥 Contas a Receber")

    # ==========================================
    # BUSCA DADOS
    # ==========================================
    df = listar_contas_receber()

    st.caption(
        f"Registros encontrados: {len(df)}"
    )

    if df is None or df.empty:

        st.info(
            "Nenhuma conta cadastrada."
        )

        return

    # ==========================================
    # TABELA
    # ==========================================
    st.dataframe(
        df,
        use_container_width=True
    )

    st.divider()

    # ==========================================
    # RECEBER CONTA
    # ==========================================
    st.subheader(
        "💰 Receber Conta"
    )

    if "status" not in df.columns:

        st.error(
            "Coluna STATUS não encontrada."
        )

        return

    pendentes = df[
        df["status"]
        .astype(str)
        .str.lower()
        == "pendente"
    ]

    if not pendentes.empty:

        conta_id = st.selectbox(
            "Selecione a conta",
            pendentes["id"].tolist()
        )

        conta = pendentes[
            pendentes["id"] == conta_id
        ].iloc[0]

        st.write(
            f"📌 {conta['descricao']}"
        )

        st.write(
            f"💲 R$ {float(conta['valor']):.2f}"
        )

        if st.button(
            "💰 Receber Conta",
            use_container_width=True
        ):

            try:

                ok = processar_entrada_financeira(
                    valor=float(
                        conta["valor"]
                    ),
                    descricao=str(
                        conta["descricao"]
                    ),
                    categoria="Recebimento",
                    origem="contas_receber",
                    referencia_id=int(
                        conta["id"]
                    )
                )

                if ok:

                    st.success(
                        "Conta recebida com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "A função retornou False."
                    )

            except Exception as erro:

                st.error(
                    f"Erro: {erro}"
                )

                print(erro)

    else:

        st.info(
            "Nenhuma conta pendente."
        )

    st.divider()

    # ==========================================
    # EXCLUIR CONTA
    # ==========================================
    st.subheader(
        "🗑️ Excluir Conta"
    )

    conta_excluir = st.selectbox(
        "Selecione a conta para excluir",
        df["id"].tolist(),
        key="excluir_conta_receber"
    )

    if st.button(
        "🗑️ Excluir Conta",
        use_container_width=True
    ):

        resultado = excluir_conta_receber(
            conta_excluir
        )

        if resultado is True:

            st.success(
                "Conta excluída com sucesso!"
            )

            st.rerun()

        elif resultado == "recebido":

            st.warning(
                "Não é permitido excluir contas já recebidas."
            )

        else:

            st.error(
                "Erro ao excluir conta."
            )