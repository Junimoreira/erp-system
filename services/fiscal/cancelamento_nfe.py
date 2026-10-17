"""Cancelamento NF-e MG: evento, auditoria durável e recuperação por consulta."""
import os
from pathlib import Path
from lxml import etree
from database.connection import conectar
from database.documentos_fiscais_db import buscar_documento_por_chave
from services.fiscal.sefaz_cancelamento_nfe import (
    gerar_evento_cancelamento, assinar_evento_cancelamento,
    transmitir_evento_cancelamento_mg,
)
from services.fiscal.sefaz_consulta_nfe import consultar_nfe_sefaz_mg

NS = {'n': 'http://www.portalfiscal.inf.br/nfe'}


def _confirmacao(xml, chave, ambiente, consulta=False):
    """Verifica campos na resposta bruta, nunca apenas HTTP 200/lote 128."""
    if not xml:
        return None
    try:
        raiz = etree.fromstring(xml.encode('utf-8') if isinstance(xml, str) else xml,
                               etree.XMLParser(resolve_entities=False, no_network=True))
    except (etree.XMLSyntaxError, ValueError, TypeError):
        return None
    if consulta:
        grupos = raiz.findall('.//n:retConsSitNFe', NS)
        if raiz.tag == '{%s}retConsSitNFe' % NS['n']:
            grupos = [raiz]
        for grupo in grupos:
            if (grupo.findtext('n:chNFe', namespaces=NS) == chave
                    and grupo.findtext('n:tpAmb', namespaces=NS) == str(ambiente)
                    and grupo.findtext('n:cStat', namespaces=NS) in ('101', '151')):
                return {'cstat': grupo.findtext('n:cStat', namespaces=NS),
                        'motivo': grupo.findtext('n:xMotivo', namespaces=NS),
                        'protocolo': None}
    grupos = raiz.findall('.//n:retEvento/n:infEvento', NS)
    for grupo in grupos:
        def texto(tag):
            return grupo.findtext('n:' + tag, namespaces=NS)
        if (texto('chNFe') == chave and texto('tpAmb') == str(ambiente)
                and texto('tpEvento') == '110111' and texto('nSeqEvento') == '1'
                and texto('cStat') in ('135', '155') and texto('nProt')):
            return {'cstat': texto('cStat'), 'motivo': texto('xMotivo'),
                    'protocolo': texto('nProt')}
    return None


def _salvar_retorno(conn, documento, resposta, confirmado, estado):
    with conn.cursor() as cur:
        cur.execute('''UPDATE erp_cancelamentos_nfe SET resposta=%s, resposta_inicial=COALESCE(resposta_inicial, %s),
            protocolo_evento=COALESCE(%s, protocolo_evento), estado=%s,
            atualizado_em=CURRENT_TIMESTAMP WHERE chave_acesso=%s AND ambiente=%s''',
            (resposta, resposta, (confirmado or {}).get('protocolo'), estado,
             documento['chave_acesso'], int(documento['ambiente'])))
        if confirmado:
            cur.execute('''UPDATE documentos_fiscais SET status='CANCELADO',
                cstat=%s, xmotivo=%s, atualizado_em=CURRENT_TIMESTAMP
                WHERE id=%s AND chave_acesso=%s AND ambiente=%s
                  AND status IN ('AUTORIZADO','CANCELADO')''',
                (confirmado['cstat'], confirmado['motivo'], documento['id'],
                 documento['chave_acesso'], int(documento['ambiente'])))
            if cur.rowcount != 1:
                raise RuntimeError('Documento mudou durante o cancelamento. Consulte antes de reemitir.')
    conn.commit()


def cancelar_nfe(chave, justificativa, caminho_certificado, senha, usuario,
                 mercadoria_na_loja=False, permitir_producao=False):
    # Identidade obtida da sessão autenticada, nunca de campo editável da tela.
    if (not usuario.get('logado') or not usuario.get('id')
            or str(usuario.get('perfil', '')).strip().lower() not in ('admin', 'diretor')):
        raise PermissionError('Somente administrador autenticado pode cancelar NF-e.')
    if not mercadoria_na_loja:
        raise ValueError('Confirme que a mercadoria permanece na loja, sem circulação.')
    justificativa = ' '.join(str(justificativa or '').split())
    if not 15 <= len(justificativa) <= 255:
        raise ValueError('A justificativa deve ter entre 15 e 255 caracteres.')
    documento = buscar_documento_por_chave(chave)
    if not documento:
        raise ValueError('Documento não encontrado.')
    ambiente = int(documento['ambiente'])
    chave = str(documento['chave_acesso'])
    if int(documento['modelo']) != 55 or not chave.startswith('31'):
        raise ValueError('Este recurso atende NF-e modelo 55 emitida em MG.')
    if ambiente not in (1, 2):
        raise ValueError('Ambiente do documento inválido.')
    if ambiente == 1 and (not permitir_producao or os.getenv(
            'NFE_PRODUCAO_LIBERADA', 'false').strip().lower() not in
            ('1','true','sim','yes','on')):
        raise ValueError('Cancelamento em produção não liberado.')
    if documento['status'] == 'CANCELADO':
        return {'sucesso': True, 'mensagem': 'Documento já cancelado no ERP.'}
    if documento['status'] != 'AUTORIZADO':
        raise ValueError('Somente documento autorizado pode ser cancelado.')
    if not Path(caminho_certificado or '').is_file() or not senha:
        raise ValueError('Certificado ou senha não informado.')
    conn = conectar()
    if conn is None:
        raise RuntimeError('Banco indisponível; nenhum evento transmitido.')
    bloqueado = False
    try:
        with conn.cursor() as cur:
            # Lock de sessão sobrevive aos commits de auditoria; impede dois envios simultâneos.
            cur.execute('SELECT pg_try_advisory_lock(hashtext(%s), %s)', (chave, ambiente))
            bloqueado = bool(cur.fetchone()[0])
            if not bloqueado:
                raise RuntimeError('Já existe uma operação para esta nota. Aguarde e consulte.')
            cur.execute('SELECT estado FROM erp_cancelamentos_nfe WHERE chave_acesso=%s AND ambiente=%s',
                        (chave, ambiente))
            anterior = cur.fetchone()
        conn.commit()
        if anterior:
            # Se houve timeout/duplicidade/falha local, consulta em vez de reenviar.
            retorno = consultar_nfe_sefaz_mg(chave, caminho_certificado, senha, ambiente=ambiente)
            resposta = retorno.get('resposta') or ''
            confirmado = _confirmacao(resposta, chave, ambiente, consulta=True)
            _salvar_retorno(conn, documento, resposta, confirmado,
                            'CONFIRMADO' if confirmado else 'PENDENTE_CONFERENCIA')
            return {'sucesso': bool(confirmado), 'resposta': resposta,
                    'mensagem': ('Cancelamento confirmado e registrado no ERP.' if confirmado else
                    'Há uma tentativa anterior. A consulta não confirmou cancelamento; nenhum novo evento foi enviado. Verifique o retorno antes de prosseguir.')}
        xml = gerar_evento_cancelamento(chave=chave, protocolo=documento['protocolo'],
            cnpj=documento['emitente_cnpj'], justificativa=justificativa, ambiente=ambiente)
        assinatura = assinar_evento_cancelamento(xml, caminho_certificado, senha)
        if not assinatura.get('sucesso'):
            raise RuntimeError('Falha ao assinar: ' + '; '.join(assinatura.get('erros') or []))
        assinado = assinatura['xml_assinado']
        if isinstance(assinado, bytes):
            assinado = assinado.decode('utf-8')
        with conn.cursor() as cur:
            cur.execute('''INSERT INTO erp_cancelamentos_nfe
                (chave_acesso, ambiente, documento_id, usuario_id, usuario,
                 justificativa, xml_assinado, estado) VALUES (%s,%s,%s,%s,%s,%s,%s,'PREPARADO')''',
                (chave, ambiente, documento['id'], usuario['id'], usuario.get('usuario') or '',
                 justificativa, assinado))
        conn.commit()  # O XML e o autor ficam salvos ANTES da transmissão.
        retorno = transmitir_evento_cancelamento_mg(assinado, caminho_certificado, senha,
                                                    ambiente=ambiente)
        resposta = retorno.get('resposta_bruta') or ''
        confirmado = _confirmacao(resposta, chave, ambiente)
        _salvar_retorno(conn, documento, resposta, confirmado,
                        'CONFIRMADO' if confirmado else 'PENDENTE_CONFERENCIA')
        return {'sucesso': bool(confirmado), 'resposta': resposta,
                'mensagem': ('Cancelamento confirmado e registrado no ERP.' if confirmado else
                'Cancelamento não confirmado. Consulte o retorno. O documento não foi marcado como cancelado.')}
    finally:
        conn.rollback()
        if bloqueado:
            with conn.cursor() as cur:
                cur.execute('SELECT pg_advisory_unlock(hashtext(%s), %s)', (chave, ambiente))
            conn.commit()
        conn.close()
