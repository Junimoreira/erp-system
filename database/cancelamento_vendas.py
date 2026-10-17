"""Cancela venda a prazo ainda não recebida, com estoque e títulos na mesma transação."""
import hashlib
import json
import re
import unicodedata
from decimal import Decimal
from database.connection import conectar


def _normalizar(valor):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(valor or '').strip().upper())
                   if not unicodedata.combining(c))


def _autor(usuario):
    if (not usuario or not usuario.get('logado') or not usuario.get('id') or
            _normalizar(usuario.get('perfil')) not in ('ADMIN','DIRETOR')):
        raise PermissionError('Cancelamento permitido somente ao Diretor/admin autenticado.')


def _dinheiro(valor):
    numero = Decimal(str(valor))
    if not numero.is_finite() or numero < 0 or numero != numero.quantize(Decimal('.01')):
        raise ValueError('Valor monetário inválido na venda ou nos títulos.')
    return numero.quantize(Decimal('.01'))


def _token(plano):
    return hashlib.sha256(json.dumps(plano, sort_keys=True, default=str).encode()).hexdigest()


def _plano(cur, venda_id, bloquear=False):
    trava = ' FOR UPDATE' if bloquear else ''
    cur.execute('SELECT to_jsonb(v) FROM vendas v WHERE id=%s' + trava, (venda_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError('Venda não encontrada.')
    venda = row[0]
    if _normalizar(venda.get('status')) != 'CONCLUIDA':
        raise ValueError('A venda não está concluída ou já foi cancelada. Atualize a tela.')
    if _normalizar(venda.get('forma_pagamento')) not in (
            'CARTAO CREDITO','CREDITO','PRAZO','FIADO'):
        raise ValueError('Este fluxo atende vendas a prazo com títulos ainda pendentes. Dinheiro/banco exigem estorno específico.')
    cur.execute('''SELECT numero, status FROM documentos_fiscais WHERE venda_id=%s
                   AND UPPER(COALESCE(status,'')) <> 'CANCELADO' LIMIT 1''', (venda_id,))
    if cur.fetchone():
        raise ValueError('A venda possui documento fiscal não cancelado. Nenhum dado foi alterado.')
    cur.execute('SELECT 1 FROM marketplace_pedidos WHERE venda_id=%s LIMIT 1', (venda_id,))
    if cur.fetchone():
        raise ValueError('Venda vinculada a pedido integrado. Necessária conferência do vínculo antes de cancelar.')
    cur.execute('SELECT 1 FROM erp_cancelamentos_vendas WHERE venda_id=%s', (venda_id,))
    if cur.fetchone():
        raise ValueError('Esta venda já possui auditoria de cancelamento. Não repetir a devolução de estoque.')
    cur.execute('''SELECT id, produto_id, quantidade FROM itens_venda
                   WHERE venda_id=%s ORDER BY id''' + trava, (venda_id,))
    itens = [dict(zip(('id','produto_id','quantidade'), r)) for r in cur.fetchall()]
    if not itens:
        raise ValueError('Venda sem itens; necessária conferência manual.')
    cur.execute('''SELECT to_jsonb(cr) FROM contas_receber cr
                   WHERE descricao LIKE %s ORDER BY id''' + trava,
                (f'Venda #{venda_id} - Parcela %',))
    titulos = [r[0] for r in cur.fetchall()]
    if not titulos:
        raise ValueError('Nenhum título gerado pela venda foi encontrado. Não é seguro cancelar automaticamente.')
    parcelas = []
    soma = Decimal('0.00')
    for titulo in titulos:
        match = re.fullmatch(r'Venda #' + str(venda_id) + r' - Parcela (\d+)/(\d+)',
                             str(titulo.get('descricao') or ''))
        if not match or titulo.get('observacoes') != f'Gerado automaticamente pela venda #{venda_id}':
            raise ValueError('Vínculo do título com a venda é ambíguo; conferir antes de cancelar.')
        parcelas.append((int(match[1]),int(match[2])))
        if titulo.get('cliente_id') != venda.get('cliente_id'):
            raise ValueError('Cliente do título difere do cliente da venda.')
        if _normalizar(titulo.get('status')) != 'PENDENTE':
            raise ValueError('Há título que não está pendente. Necessário tratamento financeiro específico.')
        if any(titulo.get(k) is not None for k in ('data_recebimento','data_pagamento','caixa_id','conta_bancaria_id')):
            raise ValueError('Título possui indício de recebimento ou vínculo financeiro; operação bloqueada.')
        if titulo.get('origem'):
            raise ValueError('Título possui origem financeira preenchida; confira antes de cancelar.')
        soma += _dinheiro(titulo['valor'])
    quantidade_parcelas = len(titulos)
    if sorted(parcelas) != [(i,quantidade_parcelas) for i in range(1,quantidade_parcelas+1)]:
        raise ValueError('Parcelas ausentes, repetidas ou inconsistentes.')
    if soma != _dinheiro(venda['valor_final']):
        raise ValueError('Soma dos títulos difere do total da venda.')
    ids_titulos = [int(t['id']) for t in titulos]
    cur.execute('''SELECT id FROM movimentacoes
                   WHERE (referencia_id=%s AND UPPER(COALESCE(referencia_tipo,''))='VENDA')
                      OR (referencia_id=ANY(%s) AND UPPER(COALESCE(referencia_tipo,''))
                          IN ('CONTAS_RECEBER','CONTA_RECEBER'))
                      OR descricao LIKE %s
                      OR descricao LIKE ANY(%s)
                   LIMIT 1''',
                (venda_id,ids_titulos,f'Venda #{venda_id} %',
                 [f'Recebimento conta #{i}:%' for i in ids_titulos]))
    if cur.fetchone():
        raise ValueError('Existe movimentação financeira vinculada. Nenhum estorno automático será realizado.')
    quantidades = {}
    for item in itens:
        qtd = Decimal(str(item['quantidade']))
        if not qtd.is_finite() or qtd <= 0:
            raise ValueError('Quantidade inválida na venda.')
        pid = int(item['produto_id'])
        quantidades[pid] = quantidades.get(pid,Decimal(0)) + qtd
    estoque = []
    for pid,qtd in sorted(quantidades.items()):
        cur.execute('SELECT estoque FROM produtos WHERE id=%s' + trava, (pid,))
        produto = cur.fetchone()
        if not produto:
            raise ValueError('Produto da venda não encontrado.')
        atual = Decimal(str(produto[0] or 0))
        if not atual.is_finite():
            raise ValueError('Estoque inválido.')
        estoque.append({'produto_id':pid,'quantidade_devolver':str(qtd),
                        'estoque_antes':str(atual),'estoque_depois':str(atual+qtd)})
    return {'venda':venda,'itens':itens,'titulos':titulos,'estoque':estoque}


def preparar_cancelamento(venda_id, usuario):
    _autor(usuario)
    conn = conectar()
    if conn is None:
        raise RuntimeError('Banco indisponível.')
    try:
        with conn.cursor() as cur:
            plano = _plano(cur,int(venda_id))
        return {'plano':plano,'token':_token(plano)}
    finally:
        conn.close()


def cancelar_venda_pendente(venda_id, motivo, token, usuario):
    _autor(usuario)
    motivo = ' '.join(str(motivo or '').split())
    if not 15 <= len(motivo) <= 500:
        raise ValueError('Informe motivo entre 15 e 500 caracteres.')
    venda_id = int(venda_id)
    conn = conectar()
    if conn is None:
        raise RuntimeError('Banco indisponível.')
    try:
        with conn.cursor() as cur:
            plano = _plano(cur,venda_id,bloquear=True)
            if _token(plano) != token:
                raise ValueError('Dados alterados após a conferência. Carregue a prévia novamente.')
            for titulo in plano['titulos']:
                cur.execute('''UPDATE contas_receber SET status='CANCELADO'
                               WHERE id=%s AND UPPER(status)='PENDENTE'
                               AND data_recebimento IS NULL AND data_pagamento IS NULL''',
                            (titulo['id'],))
                if cur.rowcount != 1:
                    raise RuntimeError('Título mudou durante a operação.')
            for estoque in plano['estoque']:
                cur.execute('''UPDATE produtos SET estoque=COALESCE(estoque,0)+%s
                               WHERE id=%s''',
                            (Decimal(estoque['quantidade_devolver']),estoque['produto_id']))
                if cur.rowcount != 1:
                    raise RuntimeError('Falha na devolução do estoque.')
            cur.execute("UPDATE vendas SET status='Cancelada' WHERE id=%s", (venda_id,))
            if cur.rowcount != 1:
                raise RuntimeError('Falha no cancelamento da venda.')
            cur.execute('''INSERT INTO erp_cancelamentos_vendas
                           (venda_id,usuario_id,usuario,motivo,plano)
                           VALUES (%s,%s,%s,%s,%s::jsonb)''',
                        (venda_id,usuario['id'],usuario.get('usuario') or '',motivo,
                         json.dumps(plano,default=str)))
        conn.commit()
        return plano
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
