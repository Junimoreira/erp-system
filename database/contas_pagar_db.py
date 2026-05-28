import pandas as pd
from datetime import datetime

from database.connection import conectar
from database.caixa_db import verificar_caixa_aberto
from database.movimentacoes_db import registrar_movimentacao
from database.fluxo_caixa_db import registrar_fluxo_caixa


# ==================================================
# TRATAMENTO TEXTO
# ==================================================
def tratar_texto(valor):

    if valor is None:
        return ""

    return str(valor).strip()


# ==================================================
# CADASTRAR CONTA
# ==================================================
def cadastrar_conta(
    descricao,
    valor,
    vencimento,
    categoria=None,
    forma_pagamento=None,
    observacoes=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO contas_pagar (
                descricao,
                valor,
                vencimento,
                categoria,
                forma_pagamento,
                observacoes,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Pendente')
        """, (
            descricao,
            float(valor),
            vencimento,
            categoria,
            forma_pagamento,
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
# PAGAR CONTA
# ==================================================
def pagar_conta(conta_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT descricao, valor, categoria, status
            FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise ValueError("Conta não encontrada.")

        descricao = tratar_texto(conta[0])
        valor = float(conta[1])
        categoria = tratar_texto(conta[2]) or "despesa"
        status = tratar_texto(conta[3]).lower()

        if status == "pago":
            raise ValueError("Conta já está paga.")

        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa["id"] if isinstance(caixa, dict) else caixa[0]

        # ==========================================
        # ATUALIZA CONTA
        # ==========================================
        cursor.execute("""
            UPDATE contas_pagar
            SET status = 'Pago',
                data_pagamento = NOW()
            WHERE id = %s
        """, (conta_id,))

        # ==========================================
        # MOVIMENTAÇÃO
        # ==========================================
        sucesso_mov = registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="saida",
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            origem="contas_pagar",
            data_movimentacao=datetime.now()
        )

        if not sucesso_mov:
            raise ValueError("Erro ao gerar movimentação.")

        # ==========================================
        # FLUXO CAIXA
        # ==========================================
        sucesso_fluxo = registrar_fluxo_caixa(
            tipo="saida",
            valor=valor,
            descricao=descricao,
            origem="contas_pagar"
        )

        if not sucesso_fluxo:
            raise ValueError("Erro ao registrar fluxo caixa.")

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
# LISTAR CONTAS (SEGURA)
# ==================================================
def listar_contas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                descricao,
                valor,
                vencimento,
                categoria,
                forma_pagamento,
                observacoes,
                status,
                data_pagamento
            FROM contas_pagar
            ORDER BY vencimento ASC
        """

        return pd.read_sql(query, conn)

    except Exception as erro:

        print(f"Erro listar_contas: {erro}")

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# EXCLUIR CONTA
# ==================================================
def excluir_conta(conta_id):

    conn = conectar()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM contas_pagar
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:

        conn.rollback()
        print(f"Erro excluir_conta: {erro}")
        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CONTA (BLOQUEIA PAGAS)
# ==================================================
def atualizar_conta(
    conta_id,
    descricao,
    valor,
    vencimento,
    categoria=None,
    forma_pagamento=None,
    observacoes=None
):

    conn = conectar()
    cursor = conn.cursor()

    try:

        # BLOQUEIO IMPORTANTE (ERP REAL)
        cursor.execute("""
            SELECT status FROM contas_pagar WHERE id = %s
        """, (conta_id,))

        status = cursor.fetchone()

        if status and status[0].lower() == "pago":
            raise ValueError("Conta paga não pode ser editada.")

        cursor.execute("""
            UPDATE contas_pagar
            SET
                descricao = %s,
                valor = %s,
                vencimento = %s,
                categoria = %s,
                forma_pagamento = %s,
                observacoes = %s
            WHERE id = %s
        """, (
            descricao,
            float(valor),
            vencimento,
            categoria,
            forma_pagamento,
            observacoes,
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