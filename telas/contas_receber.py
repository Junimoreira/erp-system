import streamlit as st
import pandas as pd

from database.connection import conectar


# ==================================================
# LISTAR CONTAS
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
        ORDER BY cr.vencimento
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
        # BUSCAR DADOS
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
# TELA PRINCIPAL
# ==================================================

def tela_contas_receber():

    st.title("📥 Contas a Receber")

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
            ]
        )

    with col2:

        busca = st.text_input(
            "Buscar Cliente"
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
    # RECEBER CONTA
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
        "💰 Receber Conta"
    )

    contas = {

        f"{row['id']} - {row['cliente']}": row

        for _, row in pendentes.iterrows()
    }

    conta_sel = st.selectbox(
        "Selecione a conta",
        list(contas.keys())
    )

    conta = contas[conta_sel]

    st.info(f"""
Cliente: {conta['cliente']}

Descrição: {conta['descricao']}

Valor: R$ {conta['valor']:,.2f}

Vencimento: {conta['vencimento']}
    """)

    if st.button("✅ Confirmar Recebimento"):

        if receber_conta(conta["id"]):

            st.success(
                "Conta recebida com sucesso!"
            )

            st.rerun()

        else:

            st.error(
                "Erro ao receber conta."
            )