from database.finance_engine import registrar_movimentacao_financeira


def lancar_financeiro(
    tipo,
    origem,
    meio,
    valor,
    descricao,
    referencia_tipo=None,
    referencia_id=None
):
    """
    Porta única para lançamentos financeiros.

    Toda entrada ou saída deve passar por aqui.
    """

    return registrar_movimentacao_financeira(
        tipo=tipo,
        origem=origem,
        meio=meio,
        valor=valor,
        descricao=descricao,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id
    )