"""Edição comercial sem mudar o total ou movimentar estoque/financeiro."""
import hashlib
import json
from database.connection import conectar
from services.vendas_valores import calcular, moeda, modalidade


def _autor(usuario):
    if (not usuario.get('logado') or not usuario.get('id') or
            str(usuario.get('perfil', '')).strip().lower() not in ('admin', 'diretor')):
        raise PermissionError('Edição permitida somente ao Diretor/administrador autenticado.')


def _foto(cursor, venda_id, bloquear=False):
    cursor.execute('''SELECT id, status, valor_total, desconto, valor_final,
                      COALESCE(frete,0), COALESCE(mod_frete,'9')
                      FROM vendas WHERE id=%s''' + (' FOR UPDATE' if bloquear else ''), (venda_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError('Venda não encontrada.')
    venda = dict(zip(('id','status','valor_total','desconto','valor_final','frete','mod_frete'), row))
    cursor.execute('''SELECT id, produto_id, quantidade, preco_unitario, subtotal,
                      COALESCE(desconto,0), COALESCE(valor_final,subtotal)
                      FROM itens_venda WHERE venda_id=%s ORDER BY id''' +
                   (' FOR UPDATE' if bloquear else ''), (venda_id,))
    venda['itens'] = [dict(zip(('item_id','produto_id','quantidade','preco_unitario',
                               'subtotal','desconto','valor_final'), r)) for r in cursor.fetchall()]
    if not venda['itens']:
        raise ValueError('Venda sem itens.')
    return venda


def _token(venda):
    return hashlib.sha256(json.dumps(venda, sort_keys=True, default=str).encode()).hexdigest()


def _bloqueios(cursor, venda_id, venda):
    if str(venda['status']).strip().lower() not in ('concluída','concluida'):
        raise ValueError('Somente vendas concluídas podem ter os valores corrigidos.')
    cursor.execute('''SELECT numero, status FROM documentos_fiscais WHERE venda_id=%s
                     AND UPPER(COALESCE(status,'')) <> 'CANCELADO' LIMIT 1''', (venda_id,))
    doc = cursor.fetchone()
    if doc:
        raise ValueError(f'Existe documento fiscal não cancelado: {doc[0]}, status {doc[1]}.')
    cursor.execute('SELECT 1 FROM marketplace_pedidos WHERE venda_id=%s LIMIT 1', (venda_id,))
    if cursor.fetchone():
        raise ValueError('Venda vinculada à integração marketplace. Corrija pela origem do pedido para não divergir da emissão.')


def carregar_edicao(venda_id, usuario):
    _autor(usuario)
    conn = conectar()
    if conn is None:
        raise RuntimeError('Banco indisponível.')
    try:
        with conn.cursor() as cur:
            venda = _foto(cur, venda_id)
            _bloqueios(cur, venda_id, venda)
        return dict(venda, token=_token(venda))
    finally:
        conn.close()


def salvar_edicao(venda_id, precos, frete, mod_frete, motivo, token, usuario):
    _autor(usuario)
    motivo = ' '.join(str(motivo or '').split())
    if not 15 <= len(motivo) <= 500:
        raise ValueError('Informe um motivo entre 15 e 500 caracteres.')
    conn = conectar()
    if conn is None:
        raise RuntimeError('Banco indisponível.')
    try:
        with conn.cursor() as cur:
            antes = _foto(cur, venda_id, bloquear=True)
            _bloqueios(cur, venda_id, antes)
            if _token(antes) != token:
                raise ValueError('A venda mudou desde a abertura. Carregue novamente.')
            mapa = {int(k): v for k, v in precos.items()}
            if set(mapa) != {int(i['item_id']) for i in antes['itens']}:
                raise ValueError('Os itens da venda não conferem.')
            itens = [dict(i, preco_unitario=mapa[int(i['item_id'])]) for i in antes['itens']]
            depois = calcular(itens, frete)
            depois['mod_frete'] = modalidade(mod_frete, depois['frete'])
            if depois['valor_final'] != moeda(antes['valor_final']):
                raise ValueError('O total deve permanecer igual ao original. Alterar o recebimento exige outro fluxo financeiro.')
            if depois['desconto'] != moeda(antes['desconto'] or 0):
                raise ValueError('Os descontos dos itens divergem do cabeçalho. Necessária conferência antes de editar.')
            for item in depois['itens']:
                cur.execute('''UPDATE itens_venda SET preco_unitario=%s, subtotal=%s,
                               valor_final=%s WHERE id=%s AND venda_id=%s''',
                            (item['preco_unitario'], item['subtotal'], item['valor_final'],
                             item['item_id'], venda_id))
                if cur.rowcount != 1:
                    raise RuntimeError('Falha ao atualizar item.')
            cur.execute('''UPDATE vendas SET valor_total=%s, frete=%s, mod_frete=%s
                           WHERE id=%s''',
                        (depois['valor_total'], depois['frete'], depois['mod_frete'], venda_id))
            if cur.rowcount != 1:
                raise RuntimeError('Falha ao atualizar venda.')
            cur.execute('''INSERT INTO erp_edicoes_valores_vendas
                           (venda_id, usuario_id, usuario, motivo, antes, depois)
                           VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb)''',
                        (venda_id, usuario['id'], usuario.get('usuario') or '', motivo,
                         json.dumps(antes, default=str), json.dumps(depois, default=str)))
        conn.commit()
        return depois
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
