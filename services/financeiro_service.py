from datetime import datetime
from database.connection import conectar
from database.caixa_db import verificar_caixa_aberto
from database.movimentacoes_db import registrar_movimentacao
from database.fluxo_caixa_db import registrar_fluxo_caixa


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

        # ==========================================
        # CAIXA
        # ==========================================
        caixa = verificar_caixa_aberto()

        if caixa is None:
            raise ValueError("Nenhum caixa aberto.")

        caixa_id = caixa[0] if isinstance(caixa, tuple) else caixa["id"]

        # ==========================================
        # MOVIMENTAÇÃO
        # ==========================================
        sucesso_mov = registrar_movimentacao(
            caixa_id=caixa_id,
            tipo="saida",
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            origem=origem,
            data_movimentacao=datetime.now()
        )

        if not sucesso_mov:
            raise ValueError("Falha ao registrar movimentação.")

        # ==========================================
        # FLUXO CAIXA
        # ==========================================
        sucesso_fluxo = registrar_fluxo_caixa(
            tipo="saida",
            valor=valor,
            descricao=descricao,
            origem=origem
        )

        if not sucesso_fluxo:
            raise ValueError("Falha ao registrar fluxo de caixa.")

        # ==========================================
        # CONTAS A PAGAR (SE APLICÁVEL)
        # ==========================================
        if origem == "contas_pagar" and referencia_id is not None:

            cursor.execute("""
                UPDATE contas_pagar
                SET status = 'Pago',
                    data_pagamento = NOW()
                WHERE id = %s
            """, (referencia_id,))

        # ==========================================
        # COMMIT FINAL
        # ==========================================
        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print("Erro processar saída financeira:", erro)

        return False

    finally:

        cursor.close()
        conn.close()