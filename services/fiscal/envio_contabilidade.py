"""Pacote mensal dos XMLs fiscais armazenados no ERP, sem gravar pastas."""
import csv
import hashlib
from datetime import date
from io import BytesIO, StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as ET

NS = {'n': 'http://www.portalfiscal.inf.br/nfe'}


def consultar_documentos(ano, mes):
    from database.connection import conectar
    inicio = date(ano, mes, 1)
    fim = date(ano + (mes == 12), 1 if mes == 12 else mes + 1, 1)
    conn = conectar()
    if conn is None:
        raise RuntimeError('Não foi possível conectar ao banco de dados.')
    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT id, chave_acesso, modelo, serie, numero, tipo_movimento,
                       ambiente, data_emissao, emitente_nome, destinatario_nome,
                       valor_total, status, xml_processado, xml_original
                FROM documentos_fiscais
                WHERE data_emissao >= %s AND data_emissao < %s
                ORDER BY data_emissao, id
            ''', (inicio, fim))
            colunas = [coluna[0] for coluna in cursor.description]
            return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]
    finally:
        conn.close()


def _validar_xml(valor, documento, ano, mes):
    if not valor:
        raise ValueError('XML ausente')
    conteudo = bytes(valor) if isinstance(valor, (bytes, memoryview)) else str(valor).encode('utf-8')
    raiz = ET.fromstring(conteudo, parser=ET.XMLParser(resolve_entities=False, no_network=True))
    if raiz.getroottree().docinfo.doctype:
        raise ValueError("XML com DTD não permitido")
    inf = raiz.find('n:NFe/n:infNFe', NS)
    protocolo = raiz.find('n:protNFe/n:infProt', NS)
    if inf is None or protocolo is None:
        raise ValueError('XML sem protocolo de autorização')
    if protocolo.findtext('n:cStat', namespaces=NS) not in ('100', '150'):
        raise ValueError('Protocolo não autorizado')
    chave = protocolo.findtext('n:chNFe', namespaces=NS) or ''
    if len(chave) != 44 or not chave.isdigit() or inf.get('Id') != 'NFe' + chave:
        raise ValueError('Chave do XML inconsistente')
    if str(documento.get('chave_acesso') or '') != chave:
        raise ValueError('Chave do cadastro difere do XML')
    if inf.findtext('n:ide/n:tpAmb', namespaces=NS) != '1':
        raise ValueError('XML de homologação')
    emissao = inf.findtext('n:ide/n:dhEmi', namespaces=NS) or inf.findtext('n:ide/n:dEmi', namespaces=NS) or ''
    if emissao[:7] != f'{ano:04d}-{mes:02d}':
        raise ValueError('Competência do XML difere do período selecionado')
    modelo = inf.findtext('n:ide/n:mod', namespaces=NS)
    if modelo not in ('55', '65'):
        raise ValueError('Modelo não suportado')
    return conteudo, chave, modelo


def _csv(linhas):
    buffer = StringIO(newline='')
    campos = ['id', 'data_emissao', 'tipo_movimento', 'modelo', 'serie', 'numero',
              'chave_acesso', 'emitente_nome', 'destinatario_nome', 'valor_total',
              'status', 'arquivo', 'conferencia', 'sha256']
    escritor = csv.DictWriter(buffer, campos, extrasaction='ignore', delimiter=';')
    escritor.writeheader()
    for linha in linhas:
        # Evita interpretar nomes ou observações como fórmulas em planilhas.
        escritor.writerow({k: ("'" + str(v) if str(v).startswith(('=', '+', '-', '@')) else v)
                            for k, v in linha.items() if k in campos})
    return buffer.getvalue().encode('utf-8-sig')


def gerar_pacote(documentos, ano, mes):
    date(ano, mes, 1)
    buffer = BytesIO()
    resumo, pendencias, vistos = [], [], {}
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as pacote:
        for documento in documentos:
            if str(documento.get('ambiente')) != '1':
                continue
            linha = {k: v for k, v in documento.items() if not k.startswith('xml_')}
            movimento = str(documento.get('tipo_movimento') or '').upper()
            try:
                if movimento not in ('ENTRADA', 'SAIDA', 'SAÍDA'):
                    raise ValueError('Tipo de movimento não identificado')
                erros = []
                for campo in ('xml_processado', 'xml_original'):
                    try:
                        conteudo, chave, modelo = _validar_xml(documento.get(campo), documento, ano, mes)
                        break
                    except Exception as erro:
                        erros.append(f'{campo}: {erro}')
                else:
                    raise ValueError(' / '.join(erros))
                digest = hashlib.sha256(conteudo).hexdigest()
                if chave in vistos:
                    raise ValueError('Chave duplicada no período; conferir registros ' + str(vistos[chave]))
                vistos[chave] = documento['id']
                pasta = 'Entradas' if movimento == 'ENTRADA' else ('Saidas_NFe' if modelo == '55' else 'Saidas_NFCe')
                arquivo = f'{pasta}/{chave}.xml'
                pacote.writestr(arquivo, conteudo)
                linha.update(arquivo=arquivo, sha256=digest, conferencia='XML autorizado incluído')
                if 'CANCEL' in str(documento.get('status') or '').upper():
                    pendencias.append(dict(linha, conferencia='Documento cancelado: evento de cancelamento não incluído nesta versão'))
            except Exception as erro:
                linha.update(arquivo='', conferencia=str(erro), sha256='')
                pendencias.append(linha.copy())
            resumo.append(linha)
        pacote.writestr('Resumo_documentos.csv', _csv(resumo))
        pacote.writestr('Pendencias.csv', _csv(pendencias))
        pacote.writestr('LEIA-ME.txt', (
            f'Competência: {mes:02d}/{ano}\n'
            'Pacote dos documentos de produção cadastrados no ERP, por data de emissão.\n'
            'Não comprova que todas as notas do mês foram cadastradas.\n'
            'Confira Pendencias.csv antes de encaminhar à contabilidade.\n'
            'Esta versão inclui XMLs de NF-e/NFC-e com protocolo de autorização.\n'
            'Eventos de cancelamento, CC-e, inutilizações e DANFEs não são incluídos.\n'
            'Status e valores do resumo vêm do cadastro; notas canceladas não devem ser somadas como vendas.\n'
        ).encode('utf-8'))
    return buffer.getvalue(), resumo, pendencias, len(vistos)
