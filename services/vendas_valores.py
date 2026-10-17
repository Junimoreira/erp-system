"""Valores comerciais em Decimal; frete é separado do preço dos produtos."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTAVOS = Decimal('0.01')
MODALIDADES = {'0', '1', '2', '3', '4', '9'}


def moeda(valor, nome='Valor'):
    try:
        numero = Decimal(str(valor))
        if not numero.is_finite() or numero < 0 or numero != numero.quantize(CENTAVOS):
            raise ValueError()
        return numero.quantize(CENTAVOS)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{nome} deve ser não negativo, finito e ter até duas casas decimais.')


def modalidade(valor, frete):
    valor = str(valor)
    if valor not in MODALIDADES:
        raise ValueError('Selecione a modalidade de transporte.')
    if frete > 0 and valor == '9':
        raise ValueError('Frete cobrado exige modalidade de transporte diferente de sem ocorrência.')
    return valor


def calcular(itens, frete):
    if not itens:
        raise ValueError('Venda sem itens.')
    frete = moeda(frete, 'Frete')
    bruto = Decimal('0.00')
    descontos = Decimal('0.00')
    normalizados = []
    for item in itens:
        quantidade = Decimal(str(item['quantidade']))
        if not quantidade.is_finite() or quantidade <= 0:
            raise ValueError('Quantidade inválida.')
        preco = moeda(item.get('preco_unitario', item.get('preco')), 'Preço')
        subtotal = (quantidade * preco).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        desconto = moeda(item.get('desconto') or 0, 'Desconto')
        if desconto > subtotal:
            raise ValueError('Desconto maior que o subtotal do produto.')
        bruto += subtotal
        descontos += desconto
        normalizados.append(dict(item, preco_unitario=preco, subtotal=subtotal,
                                 desconto=desconto, valor_final=subtotal-desconto))
    return {'valor_total': bruto, 'desconto': descontos, 'frete': frete,
            'valor_final': bruto-descontos+frete, 'itens': normalizados}
