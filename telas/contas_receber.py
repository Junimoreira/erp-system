# telas/contas_receber.py

import streamlit as st
import pandas as pd

from database.connection import conectar


# ==================================================
# LISTAR CONTAS A RECEBER
# ==================================================

def listar_contas_receber():

    conn = conectar()

    query = """
        SELECT
            cr.id,
            c.nome AS cliente,
            cr.descricao,
            cr.valor,
            cr.vencimento,
            cr.status
        FROM contas_receber cr
        LEFT JOIN clientes c
            ON cr.cliente_id = c.id
        ORDER BY cr.vencimento ASC
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ==================================================
# RECEBER CONTA
# ==================================================

def receber_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==========================================
        # BUSCAR DADOS DA CONTA
        # ==========================================

        cursor.execute("""
            SELECT descricao, valor
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        descricao, valor = conta

        # ==========================================
        # ATUALIZAR STATUS
        # ==========================================

        cursor.execute("""
            UPDATE contas_receber
            SET status = 'Pago'
            WHERE id = %s
        """, (conta_id,))

        # ==========================================
        # GERAR MOVIMENTAÇÃO
        # ==========================================

        cursor.execute("""
            INSERT INTO movimentacoes (
                tipo,
                valor,
                descricao,
                origem
            )
            VALUES (%s, %s, %s, %s)
        """, (
            "entrada",
            valor,
            f"Recebimento: {descricao}",
            "Contas a Receber"
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao receber conta:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CONTA
# ==================================================

def atualizar_conta_receber(
    conta_id,
    descricao,
    valor,
    vencimento
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE contas_receber
            SET
                descricao = %s,
                valor = %s,
                vencimento = %s
            WHERE id = %s
        """, (
            descricao,
            valor,
            vencimento,
            conta_id
        ))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao atualizar conta:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CONTA
# ==================================================

def excluir_conta_receber(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # ==========================================
        # VALIDAR STATUS
        # ==========================================

        cursor.execute("""
            SELECT status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        if conta[0] == "Pago":
            return "pago"

        # ==========================================
        # EXCLUIR
        # ==========================================

        cursor.execute("""
            DELETE FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro ao excluir conta:", erro)

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# TELA PRINCIPAL
# ==================================================

def tela_contas_receber():

    st.title("📥 Contas a Receber")

    abas = st.tabs([
        "📋 Lista",
        "💰 Receber",
        "✏️ Editar",
        "🗑️ Excluir"
    ])

    # ==================================================
    # ABA 1 - LISTA
    # ==================================================

    with abas[0]:

        st.subheader("Lista de Contas")

        df = listar_contas_receber()

        # ==============================================
        # FILTROS
        # ==============================================

        col1, col2 = st.columns(2)

        with col1:

            status = st.selectbox(
                "Status",
                [
                    "Todos",
                    "Pendente",
                    "Pago"
                ],
                key="filtro_status_receber"
            )

        with col2:

            busca = st.text_input(
                "Buscar Cliente",
                key="buscar_cliente_receber"
            )

        # ==============================================
        # APLICAR FILTROS
        # ==============================================

        if status != "Todos":

            df = df[
                df["status"] == status
            ]

        if busca:

            df = df[
                df["cliente"].str.contains(
                    busca,
                    case=False,
                    na=False
                )
            ]

        # ==============================================
        # VALIDAR
        # ==============================================

        if df.empty:

            st.info(
                "Nenhuma conta encontrada."
            )

        else:

            # ==========================================
            # FORMATAR
            # ==========================================

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

    # ==================================================
    # ABA 2 - RECEBER CONTA
    # ==================================================

    with abas[1]:

        st.subheader("💰 Receber Conta")

        df = listar_contas_receber()

        pendentes = df[
            df["status"] == "Pendente"
        ]

        if pendentes.empty:

            st.success(
                "✅ Nenhuma conta pendente."
            )

        else:

            contas = {

                f"{row['id']} - {row['cliente']}": row

                for _, row in pendentes.iterrows()
            }

            conta_sel = st.selectbox(
                "Selecione a conta",
                list(contas.keys()),
                key="receber_conta"
            )

            conta = contas[conta_sel]

            st.info(f"""
Cliente: {conta['cliente']}

Descrição: {conta['descricao']}

Valor: R$ {conta['valor']:,.2f}

Vencimento: {conta['vencimento']}
            """)

            if st.button(
                "✅ Confirmar Recebimento",
                key="confirmar_recebimento"
            ):

                sucesso = receber_conta(
                    conta["id"]
                )

                if sucesso:

                    st.success(
                        "Conta recebida com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Erro ao receber conta."
                    )

    # ==================================================
    # ABA 3 - EDITAR
    # ==================================================

    with abas[2]:

        st.subheader("✏️ Editar Conta")

        df = listar_contas_receber()

        if df.empty:

            st.info(
                "Nenhuma conta cadastrada."
            )

        else:

            contas = {

                f"{row['id']} - {row['cliente']}": row

                for _, row in df.iterrows()
            }

            conta_sel = st.selectbox(
                "Selecione a conta",
                list(contas.keys()),
                key="editar_conta_receber"
            )

            conta = contas[conta_sel]

            with st.form("form_editar_receber"):

                descricao = st.text_input(
                    "Descrição",
                    value=conta["descricao"]
                )

                valor = st.number_input(
                    "Valor",
                    value=float(conta["valor"]),
                    format="%.2f"
                )

                vencimento = st.date_input(
                    "Vencimento",
                    value=conta["vencimento"]
                )

                atualizar = st.form_submit_button(
                    "💾 Atualizar Conta"
                )

                if atualizar:

                    sucesso = atualizar_conta_receber(
                        conta["id"],
                        descricao,
                        valor,
                        vencimento
                    )

                    if sucesso:

                        st.success(
                            "Conta atualizada!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Erro ao atualizar conta."
                        )

    # ==================================================
    # ABA 4 - EXCLUIR
    # ==================================================

    with abas[3]:

        st.subheader("🗑️ Excluir Conta")

        df = listar_contas_receber()

        if df.empty:

            st.info(
                "Nenhuma conta cadastrada."
            )

        else:

            contas = {

                f"{row['id']} - {row['cliente']}": row

                for _, row in df.iterrows()
            }

            conta_sel = st.selectbox(
                "Selecione a conta",
                list(contas.keys()),
                key="excluir_conta_receber"
            )

            conta = contas[conta_sel]

            st.warning(
                f"Deseja excluir a conta de {conta['cliente']}?"
            )

            if st.button(
                "🗑️ Confirmar Exclusão",
                key="confirmar_exclusao_receber"
            ):

                resultado = excluir_conta_receber(
                    conta["id"]
                )

                if resultado == True:

                    st.success(
                        "Conta excluída com sucesso!"
                    )

                    st.rerun()

                elif resultado == "pago":

                    st.error(
                        "Não é permitido excluir conta já recebida."
                    )

                else:

                    st.error(
                        "Erro ao excluir conta."
                    )