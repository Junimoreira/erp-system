from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _texto(v):
    if v is None:
        return None
    t=str(v).strip()
    return None if t.upper() in ('','NONE','NULL','NAN','<NA>') else t


def _decimal(v, padrao=Decimal('0')):
    if v is None:
        return padrao
    try:
        return Decimal(str(v).strip().replace(',','.'))
    except (InvalidOperation, ValueError, TypeError):
        return padrao


def _q(v, casas='0.01'):
    return _decimal(v).quantize(Decimal(casas), rounding=ROUND_HALF_UP)


def _data(v):
    if v is None:
        return date.today()
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return datetime.fromisoformat(str(v).strip()).date()


def _validar(cst, cclass):
    erros=[]
    cst=_texto(cst); cclass=_texto(cclass)
    if not cst or len(cst)!=3 or not cst.isdigit():
        erros.append('CST IBS/CBS inválido.')
    if not cclass or len(cclass)!=6 or not cclass.isdigit():
        erros.append('cClassTrib inválido.')
    if cst and cclass and len(cst)==3 and len(cclass)==6 and cclass[:3]!=cst:
        erros.append('Os três primeiros dígitos do cClassTrib devem coincidir com o CST.')
    return cst,cclass,erros


def calcular_ibs_cbs(*, base_calculo, cst, classificacao_tributaria, data_referencia=None,
                      crt=None, aliquota_ibs_uf=None, aliquota_ibs_municipal=None,
                      aliquota_cbs=None, habilitado=True, permitir_simples_2026=False):
    erros=[]; avisos=[]
    base=_q(base_calculo)
    if base<0: erros.append('Base de cálculo não pode ser negativa.')
    cst,cclass,e=_validar(cst,classificacao_tributaria); erros.extend(e)
    d=_data(data_referencia)
    crt=_texto(crt)
    if not habilitado:
        avisos.append('Cálculo IBS/CBS desabilitado pela configuração fiscal.')
    if crt=='1' and d.year==2026 and not permitir_simples_2026:
        avisos.append('CRT 1 em 2026: cálculo IBS/CBS bloqueado por padrão; a aplicação poderá habilitar exceções quando cabíveis.')
        return {'sucesso':len(erros)==0,'calcular':False,'base_calculo':base,'cst_ibs_cbs':cst,'classificacao_tributaria':cclass,
                'pIBSUF':Decimal('0.0000'),'pIBSMun':Decimal('0.0000'),'pCBS':Decimal('0.0000'),
                'vIBSUF':Decimal('0.00'),'vIBSMun':Decimal('0.00'),'vIBS':Decimal('0.00'),'vCBS':Decimal('0.00'),
                'erros':erros,'avisos':avisos}
    if not habilitado or erros:
        return {'sucesso':False if erros else True,'calcular':False,'base_calculo':base,'cst_ibs_cbs':cst,'classificacao_tributaria':cclass,
                'pIBSUF':Decimal('0.0000'),'pIBSMun':Decimal('0.0000'),'pCBS':Decimal('0.0000'),
                'vIBSUF':Decimal('0.00'),'vIBSMun':Decimal('0.00'),'vIBS':Decimal('0.00'),'vCBS':Decimal('0.00'),
                'erros':erros,'avisos':avisos}
    def aliq(v,n):
        if v is None:
            erros.append(f'{n} não informada.')
            return Decimal('0')
        x=_decimal(v,None)
        if x is None or x<0:
            erros.append(f'{n} inválida.')
            return Decimal('0')
        return x
    puf=aliq(aliquota_ibs_uf,'Alíquota IBS UF')
    pmun=aliq(aliquota_ibs_municipal,'Alíquota IBS Municipal')
    pcbs=aliq(aliquota_cbs,'Alíquota CBS')
    if erros:
        return {'sucesso':False,'calcular':False,'base_calculo':base,'cst_ibs_cbs':cst,'classificacao_tributaria':cclass,
                'pIBSUF':puf,'pIBSMun':pmun,'pCBS':pcbs,'vIBSUF':Decimal('0.00'),'vIBSMun':Decimal('0.00'),'vIBS':Decimal('0.00'),'vCBS':Decimal('0.00'),'erros':erros,'avisos':avisos}
    vuf=_q(base*puf/Decimal('100')); vmun=_q(base*pmun/Decimal('100')); vibs=_q(vuf+vmun); vcbs=_q(base*pcbs/Decimal('100'))
    return {'sucesso':True,'calcular':True,'base_calculo':base,'cst_ibs_cbs':cst,'classificacao_tributaria':cclass,
            'pIBSUF':puf.quantize(Decimal('0.0001')),'pIBSMun':pmun.quantize(Decimal('0.0001')),'pCBS':pcbs.quantize(Decimal('0.0001')),
            'vIBSUF':vuf,'vIBSMun':vmun,'vIBS':vibs,'vCBS':vcbs,'erros':[],'avisos':avisos}


def gerar_resumo_ibs_cbs(itens):
    total={'vBCIBSCBS':Decimal('0.00'),'vIBSUF':Decimal('0.00'),'vIBSMun':Decimal('0.00'),'vIBS':Decimal('0.00'),'vCBS':Decimal('0.00')}
    for i in itens or []:
        total['vBCIBSCBS']+=_q(i.get('base_calculo'))
        total['vIBSUF']+=_q(i.get('vIBSUF'))
        total['vIBSMun']+=_q(i.get('vIBSMun'))
        total['vIBS']+=_q(i.get('vIBS'))
        total['vCBS']+=_q(i.get('vCBS'))
    return {k:_q(v) for k,v in total.items()}