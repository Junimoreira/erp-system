# services/finance_service.py

from datetime import datetime

from database.connection import conectar
from database.caixa_db import verificar_caixa_aberto
from database.movimentacoes_db import registrar_movimentacao
from database.fluxo_caixa_db import registrar_fluxo_caixa


# ==================================================
# ENTRADA FINANCEIRA
# ==================================================
def processar_entrada_financeira(
    valor,
    descricao,
    categoria="receita",
    origem="manual",
    referencia_id=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        valor = float(valor)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        ok_mov = registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="entrada",
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            origem=origem,
            data_movimentacao=datetime.now()
        )

        if not ok_mov:
            raise ValueError("Erro movimentação entrada.")

        ok_fluxo = registrar_fluxo_caixa(
            tipo="entrada",
            valor=valor,
            descricao=descricao,
            origem=origem
        )

        if not ok_fluxo:
            raise ValueError("Erro fluxo caixa.")

        if origem == "contas_receber" and referencia_id is not None:

            cursor.execute("""
                UPDATE contas_receber
                SET status = 'Recebido',
                    data_recebimento = NOW()
                WHERE id = %s
            """, (referencia_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro entrada financeira:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# SAÍDA FINANCEIRA
# ==================================================
def processar_saida_financeira(
    valor,
    descricao,
    categoria="despesa",
    origem="manual",
    referencia_id=None
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        valor = float(valor)

        if valor <= 0:
            raise ValueError("Valor inválido.")

        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        ok_mov = registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="saida",
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            origem=origem,
            data_movimentacao=datetime.now()
        )

        if not ok_mov:
            raise ValueError("Erro movimentação saída.")

        ok_fluxo = registrar_fluxo_caixa(
            tipo="saida",
            valor=valor,
            descricao=descricao,
            origem=origem
        )

        if not ok_fluxo:
            raise ValueError("Erro fluxo caixa.")

        if origem == "contas_pagar" and referencia_id is not None:

            cursor.execute("""
                UPDATE contas_pagar
                SET status = 'Pago',
                    data_pagamento = NOW()
                WHERE id = %s
            """, (referencia_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro saída financeira:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ESTORNO SAÍDA
# ==================================================
def estornar_saida_financeira(conta_id, valor, descricao):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        valor = float(valor)

        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="entrada",
            valor=valor,
            descricao=f"Estorno saída: {descricao}",
            categoria="estorno",
            origem="estorno_saida",
            data_movimentacao=datetime.now()
        )

        registrar_fluxo_caixa(
            tipo="entrada",
            valor=valor,
            descricao=f"Estorno: {descricao}",
            origem="estorno_saida"
        )

        cursor.execute("""
            UPDATE contas_pagar
            SET status = 'Pendente',
                data_pagamento = NULL
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro estorno saída:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# ESTORNO ENTRADA
# ==================================================
def estornar_entrada_financeira(conta_id, valor, descricao):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        valor = float(valor)

        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="saida",
            valor=valor,
            descricao=f"Estorno entrada: {descricao}",
            categoria="estorno",
            origem="estorno_entrada",
            data_movimentacao=datetime.now()
        )

        registrar_fluxo_caixa(
            tipo="saida",
            valor=valor,
            descricao=f"Estorno: {descricao}",
            origem="estorno_entrada"
        )

        cursor.execute("""
            UPDATE contas_receber
            SET status = 'Pendente',
                data_recebimento = NULL
            WHERE id = %s
        """, (conta_id,))

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro estorno entrada:", erro)
        return False

    finally:
        cursor.close()
        conn.close()


# ==================================================
# FECHAMENTO DE CAIXA DIÁRIO (CORRIGE SEU ERRO)
# ==================================================
def fechar_caixa_diario():

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE caixa
            SET status = 'Fechado',
                fechado_em = NOW()
            WHERE status = 'Aberto'
        """)

        conn.commit()
        return True

    except Exception as erro:
        conn.rollback()
        print("Erro fechar caixa diário:", erro)
        return False

    finally:
        cursor.close()
        conn.close()

# ========================================
# CALCULAR PREÇO DE VENDA (CORRETO ERP)
# ========================================
def calcular_preco_venda(
    custo,
    imposto=0,
    frete=0,
    taxa_cartao=0,
    margem_lucro=0
):

    custo = float(custo)

    soma_percentual = (
        float(imposto) +
        float(frete) +
        float(taxa_cartao) +
        float(margem_lucro)
    ) / 100

    if soma_percentual >= 1:
        raise ValueError("Soma dos percentuais inválida (>= 100%)")

    preco_venda = custo / (1 - soma_percentual)

    return round(preco_venda, 2)