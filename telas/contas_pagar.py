# telas/contas_pagar.py

import streamlit as st
import pandas as pd

from database.connection import conectar


# ==================================================
# LISTAR CONTAS A PAGAR
# ==================================================

def listar_contas_pagar():

    conn = conectar()

    query = """
        SELECT
            id,
            descricao,
            valor,
            vencimento,
            status,
            observacoes
        FROM contas_pagar
        ORDER BY vencimento
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# CADASTRAR CONTA
# ==================================================

def cadastrar_conta_pagar(
    descricao,
    valor,
    vencimento,
    observacoes
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        query = """
            INSERT INTO contas_pagar (

                descricao,
                valor,
                vencimento,
                observacoes

            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                descricao,
                valor,
                vencimento,
                observacoes
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao cadastrar conta:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# PAGAR CONTA
# ==================================================

def pagar_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==========================================
        # BUSCAR DADOS DA CONTA
        # ==========================================

        query_busca = """
            SELECT
                descricao,
                valor
            FROM contas_pagar
            WHERE id = %s
        """

        cursor.execute(
            query_busca,
            (conta_id,)
        )

        conta = cursor.fetchone()

        descricao = conta[0]
        valor = conta[1]

        # ==========================================
        # ATUALIZAR STATUS
        # ==========================================

        query_update = """
            UPDATE contas_pagar
            SET status = 'Pago'
            WHERE id = %s
        """

        cursor.execute(
            query_update,
            (conta_id,)
        )

        # ==========================================
        # LANÇAR SAÍDA NO CAIXA
        # ==========================================

        query_fluxo = """
            INSERT INTO fluxo_caixa (

                tipo,
                descricao,
                valor,
                origem

            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query_fluxo,
            (
                "Saída",
                descricao,
                valor,
                "Contas a Pagar"
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao pagar conta:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# TELA CONTAS A PAGAR
# ==================================================

def tela_contas_pagar():

    st.title("📤 Contas a Pagar")

    abas = st.tabs([
        "➕ Nova Conta",
        "📋 Contas"
    ])

    # ==================================================
    # NOVA CONTA
    # ==================================================

    with abas[0]:

        st.subheader(
            "Cadastrar Conta"
        )

        descricao = st.text_input(
            "Descrição"
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            step=0.01
        )

        vencimento = st.date_input(
            "Vencimento"
        )

        observacoes = st.text_area(
            "Observações"
        )

        if st.button(
            "Salvar Conta",
            key="salvar_conta_pagar"
        ):

            sucesso = cadastrar_conta_pagar(
                descricao,
                valor,
                vencimento,
                observacoes
            )

            if sucesso:

                st.success(
                    "✅ Conta cadastrada!"
                )

                st.rerun()

            else:

                st.error(
                    "❌ Erro ao salvar conta."
                )

    # ==================================================
    # LISTAGEM
    # ==================================================

    with abas[1]:

        st.subheader(
            "Lista de Contas"
        )

        df = listar_contas_pagar()

        # ==============================================
        # FILTRO STATUS
        # ==============================================

        status = st.selectbox(

            "Filtrar Status",

            [
                "Todos",
                "Pendente",
                "Pago"
            ],

            key="filtro_status_pagar"
        )

        if status != "Todos":

            df = df[
                df["status"] == status
            ]

        # ==============================================
        # VALIDAR
        # ==============================================

        if df.empty:

            st.info(
                "Nenhuma conta encontrada."
            )

            return

        # ==============================================
        # FORMATAR
        # ==============================================

        df_exibir = df.copy()

        df_exibir["valor"] = df_exibir[
            "valor"
        ].map(
            lambda x: f"R$ {x:,.2f}"
        )

        st.dataframe(
            df_exibir,
            use_container_width=True
        )

        # ==============================================
        # PAGAR CONTA
        # ==============================================

        pendentes = df[
            df["status"] == "Pendente"
        ]

        if pendentes.empty:

            st.success(
                "✅ Nenhuma conta pendente."
            )

            return

        st.divider()

        st.subheader(
            "Pagar Conta"
        )

        conta_id = st.selectbox(

            "Selecione a Conta",

            pendentes["id"],

            key="select_pagar_conta"
        )

        conta = pendentes[
            pendentes["id"] == conta_id
        ].iloc[0]

        st.info(
            f"""
Descrição: {conta['descricao']}

Valor: R$ {conta['valor']:,.2f}

Vencimento: {conta['vencimento']}
            """
        )

        # ==============================================
        # CONFIRMAR PAGAMENTO
        # ==============================================

        if st.button(
            "💸 Confirmar Pagamento",
            key="confirmar_pagamento"
        ):

            sucesso = pagar_conta(
                int(conta_id)
            )

            if sucesso:

                st.success(
                    "✅ Conta paga com sucesso!"
                )

                st.rerun()

            else:

                st.error(
                    "❌ Erro ao pagar conta."
                )