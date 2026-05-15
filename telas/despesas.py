import streamlit as st

from database.despesas_db import (
    listar_despesas,
    cadastrar_despesa,
    atualizar_despesa,
    excluir_despesa,
    pagar_despesa
)


# ==================================================
# TELA DESPESAS
# ==================================================

def tela_despesas():

    st.title("💸 Controle de Despesas")

    abas = st.tabs([
        "📋 Listar",
        "➕ Nova Despesa",
        "✏️ Editar",
        "🗑️ Excluir"
    ])

    # ==================================================
    # ABA 1 - LISTAR
    # ==================================================

    with abas[0]:

        st.subheader("📋 Lista de Despesas")

        df = listar_despesas()

        filtro = st.selectbox(
            "Filtrar Status",
            ["Todos", "Pendente", "Pago"]
        )

        if filtro != "Todos":

            df = df[
                df["status"] == filtro
            ]

        if df.empty:

            st.info(
                "Nenhuma despesa encontrada."
            )

        else:

            df_exibir = df.copy()

            df_exibir["valor"] = (
                df_exibir["valor"]
                .map(
                    lambda x: f"R$ {x:,.2f}"
                )
            )

            st.dataframe(
                df_exibir,
                use_container_width=True
            )

            # ==========================================
            # PAGAR DESPESA
            # ==========================================

            pendentes = df[
                df["status"] == "Pendente"
            ]

            if not pendentes.empty:

                st.divider()

                st.subheader(
                    "💰 Pagar Despesa"
                )

                despesas = {
                    f"{row['id']} - {row['descricao']}": row
                    for _, row in pendentes.iterrows()
                }

                despesa_sel = st.selectbox(
                    "Selecione a despesa",
                    list(despesas.keys()),
                    key="pagar_despesa"
                )

                despesa = despesas[
                    despesa_sel
                ]

                st.info(f"""
📌 Descrição: {despesa['descricao']}
📂 Tipo: {despesa['tipo']}
💰 Valor: R$ {despesa['valor']:,.2f}
📅 Vencimento: {despesa['vencimento']}
                """)

                if st.button(
                    "💸 Confirmar Pagamento"
                ):

                    sucesso = pagar_despesa(
                        despesa["id"]
                    )

                    if sucesso:

                        st.success(
                            "Despesa paga com sucesso!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Erro ao pagar despesa."
                        )

    # ==================================================
    # ABA 2 - NOVA DESPESA
    # ==================================================

    with abas[1]:

        st.subheader("➕ Nova Despesa")

        with st.form("form_despesa"):

            descricao = st.text_input(
                "Descrição"
            )

            tipo = st.selectbox(
                "Tipo",
                [
                    "Fixa",
                    "Variável"
                ]
            )

            valor = st.number_input(
                "Valor",
                min_value=0.0,
                format="%.2f"
            )

            vencimento = st.date_input(
                "Vencimento"
            )

            observacoes = st.text_area(
                "Observações"
            )

            salvar = st.form_submit_button(
                "💾 Salvar Despesa"
            )

            if salvar:

                sucesso = cadastrar_despesa(
                    descricao,
                    tipo,
                    valor,
                    vencimento,
                    observacoes
                )

                if sucesso:

                    st.success(
                        "Despesa cadastrada com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Erro ao cadastrar despesa."
                    )

    # ==================================================
    # ABA 3 - EDITAR
    # ==================================================

    with abas[2]:

        st.subheader("✏️ Editar Despesa")

        df = listar_despesas()

        if df.empty:

            st.info(
                "Nenhuma despesa cadastrada."
            )

        else:

            despesas = {
                f"{row['id']} - {row['descricao']}": row
                for _, row in df.iterrows()
            }

            despesa_sel = st.selectbox(
                "Selecione a despesa",
                list(despesas.keys()),
                key="editar_despesa"
            )

            despesa = despesas[
                despesa_sel
            ]

            with st.form(
                "form_editar_despesa"
            ):

                descricao = st.text_input(
                    "Descrição",
                    value=despesa["descricao"]
                )

                tipo = st.selectbox(
                    "Tipo",
                    [
                        "Fixa",
                        "Variável"
                    ],
                    index=0 if despesa["tipo"] == "Fixa" else 1
                )

                valor = st.number_input(
                    "Valor",
                    value=float(
                        despesa["valor"]
                    ),
                    format="%.2f"
                )

                vencimento = st.date_input(
                    "Vencimento",
                    value=despesa["vencimento"]
                )

                observacoes = st.text_area(
                    "Observações",
                    value=despesa["observacoes"]
                )

                atualizar = st.form_submit_button(
                    "💾 Atualizar"
                )

                if atualizar:

                    sucesso = atualizar_despesa(
                        despesa["id"],
                        descricao,
                        tipo,
                        valor,
                        vencimento,
                        observacoes
                    )

                    if sucesso:

                        st.success(
                            "Despesa atualizada!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Erro ao atualizar despesa."
                        )

    # ==================================================
    # ABA 4 - EXCLUIR
    # ==================================================

    with abas[3]:

        st.subheader("🗑️ Excluir Despesa")

        df = listar_despesas()

        if df.empty:

            st.info(
                "Nenhuma despesa cadastrada."
            )

        else:

            despesas = {
                f"{row['id']} - {row['descricao']}": row
                for _, row in df.iterrows()
            }

            despesa_sel = st.selectbox(
                "Selecione a despesa",
                list(despesas.keys()),
                key="excluir_despesa"
            )

            despesa = despesas[
                despesa_sel
            ]

            st.warning(
                f"Excluir despesa: {despesa['descricao']} ?"
            )

            if st.button(
                "🗑️ Confirmar Exclusão"
            ):

                resultado = excluir_despesa(
                    despesa["id"]
                )

                if resultado == True:

                    st.success(
                        "Despesa excluída!"
                    )

                    st.rerun()

                elif resultado == "pago":

                    st.error(
                        "Não é permitido excluir despesa paga."
                    )

                else:

                    st.error(
                        "Erro ao excluir despesa."
                    )