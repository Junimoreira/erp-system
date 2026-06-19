import streamlit as st
import pandas as pd

from database.contas_pagar_db import (
    listar_contas,
    cadastrar_conta,
    pagar_conta,
    excluir_conta,
    atualizar_conta
)

from database.contas_bancarias import listar_contas as listar_bancos


CATEGORIAS_DESPESA = [
    "FIXA",
    "VARIAVEL"
]

TIPOS_DESPESA = [
    "ALUGUEL",
    "SALARIO",
    "CONTABILIDADE",
    "ENERGIA",
    "INTERNET",
    "TELEFONIA",
    "CONDOMINIO",
    "ASSOCIACAO",
    "FORNECEDOR",
    "IMPOSTO",
    "ADIANTAMENTO",
    "FRETE",
    "MARKETING",
    "MANUTENCAO",
    "SISTEMA",
    "OUTROS"
]


def obter_index(lista, valor, padrao=0):
    valor = str(valor).upper().strip()

    if valor in lista:
        return lista.index(valor)

    return padrao


def tela_contas_pagar():

    st.title("📄 Contas a Pagar")

    df = listar_contas()
    df_bancos = listar_bancos()

    if df.empty:
        st.info("Nenhuma conta cadastrada.")
    else:
        st.subheader("📋 Contas cadastradas")
        st.dataframe(df, use_container_width=True)

    st.divider()

    # ==================================================
    # BAIXAR / PAGAR CONTA
    # ==================================================
    if not df.empty:

        st.subheader("💸 Baixar / Pagar Conta")

        contas_pendentes = df[
            df["status"].astype(str).str.strip().str.upper() != "PAGO"
        ]

        if contas_pendentes.empty:
            st.info("Nenhuma conta pendente.")
        else:
            contas_pendentes = contas_pendentes.copy()

            contas_pendentes["opcao"] = contas_pendentes.apply(
                lambda row: (
                    f'{row["id"]} - {row["descricao"]} | '
                    f'R$ {float(row["valor"]):,.2f} | '
                    f'Venc: {row["vencimento"]}'
                ),
                axis=1
            )

            opcao = st.selectbox(
                "Selecione a conta para baixar",
                contas_pendentes["opcao"].tolist(),
                key="pagar_conta_select"
            )

            conta_pagar_id = int(opcao.split(" - ")[0])

            conta_selecionada = contas_pendentes[
                contas_pendentes["id"] == conta_pagar_id
            ].iloc[0]

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Valor",
                f"R$ {float(conta_selecionada['valor']):,.2f}"
            )

            col2.metric(
                "Vencimento",
                str(conta_selecionada["vencimento"])
            )

            col3.metric(
                "Status",
                str(conta_selecionada["status"])
            )

            origem_financeira = st.selectbox(
                "Forma de pagamento / origem financeira",
                [
                    "CAIXA",
                    "DINHEIRO",
                    "PIX",
                    "BANCO",
                    "BOLETO",
                    "TRANSFERENCIA",
                    "CARTAO DEBITO",
                    "CARTAO"
                ],
                key="origem_pagamento_conta"
            )

            formas_banco = [
                "PIX",
                "BANCO",
                "BOLETO",
                "TRANSFERENCIA",
                "CARTAO DEBITO",
                "CARTAO"
            ]

            conta_bancaria_id = None

            if origem_financeira in formas_banco:

                st.info(
                    "Essa forma de pagamento será debitada de uma conta bancária."
                )

                if df_bancos.empty:
                    st.error(
                        "Nenhuma conta bancária cadastrada. Cadastre uma conta bancária antes de baixar por banco."
                    )
                else:
                    df_bancos_tmp = df_bancos.copy()

                    df_bancos_tmp["opcao"] = df_bancos_tmp.apply(
                        lambda row: (
                            f'{row["id"]} - {row["banco"]} | '
                            f'Ag: {row["agencia"]} | '
                            f'Conta: {row["conta"]} | '
                            f'Saldo: R$ {float(row["saldo"]):,.2f}'
                        ),
                        axis=1
                    )

                    banco_opcao = st.selectbox(
                        "Conta bancária para débito",
                        df_bancos_tmp["opcao"].tolist(),
                        key="conta_bancaria_pagamento"
                    )

                    conta_bancaria_id = int(
                        banco_opcao.split(" - ")[0]
                    )

            else:
                st.warning(
                    "Essa baixa será registrada como saída de caixa/movimentação financeira."
                )

            confirmar = st.checkbox(
                "Confirmo que desejo baixar esta conta como paga",
                key="confirmar_baixa_conta_pagar"
            )

            if st.button(
                "✅ Confirmar Baixa / Pagamento",
                use_container_width=True
            ):

                if not confirmar:
                    st.warning(
                        "Marque a confirmação antes de baixar a conta."
                    )
                    return

                if origem_financeira in formas_banco and conta_bancaria_id is None:
                    st.error(
                        "Selecione uma conta bancária para realizar a baixa."
                    )
                    return

                sucesso = pagar_conta(
                    conta_id=conta_pagar_id,
                    origem_financeira=origem_financeira,
                    conta_bancaria_id=conta_bancaria_id
                )

                if sucesso:
                    st.success("Conta baixada/paga com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao baixar/pagar conta.")

    st.divider()

    # ==================================================
    # CADASTRAR CONTA
    # ==================================================
    st.subheader("➕ Cadastrar Conta a Pagar")

    with st.form("form_cadastrar_conta_pagar"):

        descricao = st.text_input("Descrição")

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            step=0.01
        )

        vencimento = st.date_input("Vencimento")

        categoria = st.selectbox(
            "Categoria da despesa",
            CATEGORIAS_DESPESA,
            help="FIXA entra no cálculo da meta mensal. VARIAVEL não entra na meta fixa."
        )

        tipo = st.selectbox(
            "Tipo da despesa",
            TIPOS_DESPESA
        )

        observacoes = st.text_area("Observações")

        enviar = st.form_submit_button("Cadastrar")

        if enviar:
            if not descricao or valor <= 0:
                st.warning("Informe descrição e valor válido.")
            else:
                sucesso = cadastrar_conta(
                    descricao=descricao,
                    valor=valor,
                    vencimento=vencimento,
                    categoria=categoria,
                    tipo=tipo,
                    observacoes=observacoes
                )

                if sucesso:
                    st.success("Conta cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao cadastrar conta.")

    st.divider()

    # ==================================================
    # EDITAR CONTA
    # ==================================================
    if not df.empty:

        st.subheader("✏️ Editar Conta")

        conta_edit = st.selectbox(
            "Selecione a conta para editar",
            df["id"].tolist(),
            key="edit_conta"
        )

        conta_info = df[df["id"] == conta_edit].iloc[0]

        with st.form("form_editar_conta_pagar"):

            nova_descricao = st.text_input(
                "Descrição",
                value=str(conta_info.get("descricao", ""))
            )

            novo_valor = st.number_input(
                "Valor",
                min_value=0.0,
                step=0.01,
                value=float(conta_info.get("valor", 0))
            )

            novo_vencimento = st.date_input(
                "Vencimento",
                value=pd.to_datetime(
                    conta_info.get("vencimento")
                ).date()
            )

            categoria_atual = str(
                conta_info.get("categoria", "VARIAVEL")
            ).upper().strip()

            tipo_atual = str(
                conta_info.get("tipo", "OUTROS")
            ).upper().strip()

            nova_categoria = st.selectbox(
                "Categoria da despesa",
                CATEGORIAS_DESPESA,
                index=obter_index(
                    CATEGORIAS_DESPESA,
                    categoria_atual,
                    1
                )
            )

            novo_tipo = st.selectbox(
                "Tipo da despesa",
                TIPOS_DESPESA,
                index=obter_index(
                    TIPOS_DESPESA,
                    tipo_atual,
                    TIPOS_DESPESA.index("OUTROS")
                )
            )

            st.info(
                "Para marcar como PAGO, use a seção Baixar / Pagar Conta. A edição mantém o controle financeiro seguro."
            )

            novo_status = st.selectbox(
                "Status",
                ["PENDENTE", "PAGO"],
                index=0
                if str(
                    conta_info.get("status", "PENDENTE")
                ).upper().strip() != "PAGO"
                else 1,
                disabled=True
            )

            novas_observacoes = st.text_area(
                "Observações",
                value=str(
                    conta_info.get("observacoes", "")
                )
            )

            salvar_edicao = st.form_submit_button(
                "Salvar Alterações"
            )

            if salvar_edicao:
                sucesso = atualizar_conta(
                    conta_id=conta_edit,
                    descricao=nova_descricao,
                    valor=novo_valor,
                    vencimento=novo_vencimento,
                    categoria=nova_categoria,
                    tipo=novo_tipo,
                    status=str(
                        conta_info.get("status", "PENDENTE")
                    ),
                    observacoes=novas_observacoes
                )

                if sucesso:
                    st.success("Conta atualizada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao atualizar conta.")

    st.divider()

    # ==================================================
    # EXCLUIR CONTA
    # ==================================================
    if not df.empty:

        st.subheader("🗑️ Excluir Conta")

        conta_excluir = st.selectbox(
            "Selecione a conta para excluir",
            df["id"].tolist(),
            key="excluir_conta"
        )

        confirmar_exclusao = st.checkbox(
            "Confirmo que desejo excluir esta conta",
            key="confirmar_excluir_conta_pagar"
        )

        if st.button("Excluir Conta"):

            if not confirmar_exclusao:
                st.warning(
                    "Marque a confirmação antes de excluir."
                )
                return

            sucesso = excluir_conta(conta_excluir)

            if sucesso:
                st.success("Conta excluída com sucesso!")
                st.rerun()
            else:
                st.error("Erro ao excluir conta.")