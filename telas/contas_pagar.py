import streamlit as st
import pandas as pd

from database.connection import conectar


# ==================================================
# LISTAR CONTAS
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
        ORDER BY vencimento ASC
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df


# ==================================================
# CADASTRAR CONTA
# ==================================================

def cadastrar_conta_pagar(descricao, valor, vencimento, observacoes):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO contas_pagar (
                descricao,
                valor,
                vencimento,
                observacoes,
                status
            )
            VALUES (%s, %s, %s, %s, 'Pendente')
        """, (
            descricao,
            valor,
            vencimento,
            observacoes
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao cadastrar conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# PAGAR CONTA (GERA MOVIMENTAÇÃO)
# ==================================================

def pagar_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # Buscar conta
        cursor.execute("""
            SELECT descricao, valor
            FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        descricao, valor = conta

        # Atualizar status
        cursor.execute("""
            UPDATE contas_pagar
            SET status = 'Pago'
            WHERE id = %s
        """, (conta_id,))

        # Criar movimentação de saída
        cursor.execute("""
            INSERT INTO movimentacoes (
                tipo,
                descricao,
                valor
            )
            VALUES (
                'saida',
                %s,
                %s
            )
        """, (f"Conta a Pagar: {descricao}", valor))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro ao pagar conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# TELA PRINCIPAL
# ==================================================

def tela_contas_pagar():

    st.title("📤 Contas a Pagar")

    abas = st.tabs([
        "➕ Nova Conta",
        "📋 Lista de Contas"
    ])

    # ==================================================
    # ABA 1 - CADASTRO
    # ==================================================

    with abas[0]:

        st.subheader("Cadastrar Nova Conta")

        with st.form("form_conta_pagar"):

            col1, col2 = st.columns(2)

            with col1:
                descricao = st.text_input("Descrição")

            with col2:
                valor = st.number_input(
                    "Valor",
                    min_value=0.0,
                    format="%.2f"
                )

            vencimento = st.date_input("Vencimento")

            observacoes = st.text_area("Observações")

            salvar = st.form_submit_button("💾 Salvar Conta")

            if salvar:

                if cadastrar_conta_pagar(
                    descricao,
                    valor,
                    vencimento,
                    observacoes
                ):
                    st.success("Conta cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao cadastrar conta.")


    # ==================================================
    # ABA 2 - LISTAGEM
    # ==================================================

    with abas[1]:

        st.subheader("Lista de Contas")

        df = listar_contas_pagar()

        # ==========================================
        # FILTRO
        # ==========================================

        filtro = st.selectbox(
            "Filtrar status",
            ["Todos", "Pendente", "Pago"]
        )

        if filtro != "Todos":
            df = df[df["status"] == filtro]

        if df.empty:
            st.info("Nenhuma conta encontrada.")
            return

        # ==========================================
        # FORMATAÇÃO VISUAL
        # ==========================================

        df_exibir = df.copy()
        df_exibir["valor"] = df_exibir["valor"].map(lambda x: f"R$ {x:,.2f}")

        st.dataframe(df_exibir, use_container_width=True)

        # ==========================================
        # AÇÃO: PAGAR CONTA
        # ==========================================

        pendentes = df[df["status"] == "Pendente"]

        if not pendentes.empty:

            st.divider()
            st.subheader("💸 Pagar Conta")

            contas_dict = {
                f"{row['id']} - {row['descricao']}": row
                for _, row in pendentes.iterrows()
            }

            conta_sel = st.selectbox(
                "Selecione a conta",
                list(contas_dict.keys())
            )

            conta = contas_dict[conta_sel]

            st.info(f"""
📌 Descrição: {conta['descricao']}
💰 Valor: R$ {conta['valor']:,.2f}
📅 Vencimento: {conta['vencimento']}
            """)

            if st.button("💸 Confirmar Pagamento"):

                if pagar_conta(conta["id"]):

                    st.success("Conta paga com sucesso!")
                    st.rerun()

                else:
                    st.error("Erro ao processar pagamento.")