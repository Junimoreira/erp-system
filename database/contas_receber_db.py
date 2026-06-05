from datetime import datetime
import pandas as pd

from database.connection import conectar
from database.caixa_db import verificar_caixa_aberto
from database.movimentacoes_db import registrar_movimentacao


# ==================================================
# TRATAMENTO TEXTO
# ==================================================
def tratar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


# ==================================================
# CADASTRAR CONTA A RECEBER
# ==================================================
def cadastrar_conta_receber(
    cliente_id,
    descricao,
    valor,
    vencimento,
    observacoes=""
):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:
        descricao = tratar_texto(descricao)
        observacoes = tratar_texto(observacoes)
        valor = float(valor)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        cursor.execute("""
            INSERT INTO contas_receber (
                cliente_id,
                descricao,
                valor,
                vencimento,
                observacoes,
                status,
                criado_em
            )
            VALUES (%s, %s, %s, %s, %s, 'Pendente', NOW())
        """, (
            cliente_id,
            descricao,
            valor,
            vencimento,
            observacoes
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro cadastrar conta receber:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# LISTAR CONTAS
# ==================================================
def listar_contas():

    conn = conectar()
    if conn is None:
        return pd.DataFrame()

    try:
        df = pd.read_sql("""
            SELECT *
            FROM contas_receber
            ORDER BY vencimento ASC
        """, conn)

        return df.fillna("")

    except Exception as erro:
        print("Erro listar contas:", erro)
        return pd.DataFrame()

    finally:
        conn.close()


# ==================================================
# RECEBER CONTA (AGORA COMPLETO)
# ==================================================
def receber_conta(conta_id, origem_financeira="CAIXA", conta_bancaria_id=None):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT descricao, valor, status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise ValueError("Conta não encontrada.")

        descricao = tratar_texto(conta[0])
        valor = float(conta[1])
        status = tratar_texto(conta[2]).lower()

        if status == "recebido":
            raise ValueError("Conta já recebida.")

        caixa_id = None

        # ==========================================
        # CAIXA
        # ==========================================
        if origem_financeira.upper() == "CAIXA":

            caixa = verificar_caixa_aberto()

            if caixa is None:
                raise ValueError("Nenhum caixa aberto.")

            caixa_id = caixa[0]

            registrar_movimentacao(
                caixa_id=caixa_id,
                tipo="entrada",
                valor=valor,
                descricao=descricao,
                categoria="recebimento",
                origem="contas_receber",
                data_movimentacao=datetime.now()
            )

        # ==========================================
        # BANCO
        # ==========================================
        elif origem_financeira.upper() == "BANCO":

            if conta_bancaria_id is None:
                raise ValueError("Conta bancária não informada.")

            cursor.execute("""
                UPDATE contas_bancarias
                SET saldo = saldo + %s
                WHERE id = %s
            """, (valor, conta_bancaria_id))

        else:
            raise ValueError("Origem inválida.")

        # ==========================================
        # SALVAR ORIGEM
        # ==========================================
        cursor.execute("""
            UPDATE contas_receber
            SET status = 'Recebido',
                data_recebimento = NOW(),
                forma_pagamento = %s,
                caixa_id = %s,
                conta_bancaria_id = %s
            WHERE id = %s
        """, (
            origem_financeira,
            caixa_id,
            conta_bancaria_id,
            conta_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro receber conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ATUALIZAR CONTA (COM ESTORNO REAL)
# ==================================================
def atualizar_conta_receber(conta_id, descricao, valor, vencimento, status):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        descricao = tratar_texto(descricao)
        valor = float(valor)
        status = tratar_texto(status).lower()

        # ==========================================
        # BUSCAR DADOS
        # ==========================================
        cursor.execute("""
            SELECT status, valor, forma_pagamento, caixa_id, conta_bancaria_id
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            raise ValueError("Conta não encontrada.")

        status_antigo = tratar_texto(conta[0]).lower()
        valor_antigo = float(conta[1])
        forma_pagamento = tratar_texto(conta[2]).upper()
        caixa_id = conta[3]
        conta_banco_id = conta[4]

        # ==========================================
        # ESTORNO AUTOMÁTICO
        # ==========================================
        if status_antigo == "recebido" and status == "pendente":

            # 🔹 CAIXA
            if forma_pagamento == "CAIXA" and caixa_id:

                registrar_movimentacao(
                    caixa_id=caixa_id,
                    tipo="saida",
                    valor=valor_antigo,
                    descricao=f"Estorno: {descricao}",
                    categoria="estorno",
                    origem="contas_receber",
                    data_movimentacao=datetime.now()
                )

            # 🔹 BANCO
            elif forma_pagamento == "BANCO" and conta_banco_id:

                cursor.execute("""
                    UPDATE contas_bancarias
                    SET saldo = saldo - %s
                    WHERE id = %s
                """, (valor_antigo, conta_banco_id))

        # ==========================================
        # DATA RECEBIMENTO
        # ==========================================
        if status == "recebido":
            data_recebimento = datetime.now()
        else:
            data_recebimento = None

        # ==========================================
        # UPDATE FINAL
        # ==========================================
        cursor.execute("""
            UPDATE contas_receber
            SET descricao = %s,
                valor = %s,
                vencimento = %s,
                status = %s,
                data_recebimento = %s
            WHERE id = %s
        """, (
            descricao,
            valor,
            vencimento,
            status.capitalize(),
            data_recebimento,
            conta_id
        ))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro atualizar conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# EXCLUIR CONTA
# ==================================================
def excluir_conta_receber(conta_id):

    conn = conectar()
    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT status
            FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conta = cursor.fetchone()

        if not conta:
            return False

        if tratar_texto(conta[0]).lower() == "recebido":
            return "recebido"

        cursor.execute("""
            DELETE FROM contas_receber
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro excluir conta:", erro)
        return False

    finally:
        cursor.close()
        conn.close()