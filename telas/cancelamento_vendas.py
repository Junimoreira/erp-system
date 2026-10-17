"""Prévia e cancelamento de venda a prazo ainda pendente, para Diretor/admin."""
import streamlit as st
from database.cancelamento_vendas import preparar_cancelamento, cancelar_venda_pendente


def mostrar_cancelamento_vendas():
    if (not st.session_state.get('logado') or not st.session_state.get('id') or
            str(st.session_state.get('perfil','')).strip().lower() not in ('admin','diretor')):
        return
    usuario={k:st.session_state.get(k) for k in ('logado','id','usuario','perfil')}
    with st.expander('Cancelar venda a prazo ainda não recebida'):
        st.caption('Cancela a venda e os títulos pendentes, devolvendo os itens ao estoque. '
                   'Preserva os registros. Vendas com nota não cancelada, recebimento ou movimento financeiro são bloqueadas.')
        numero=st.number_input('Número da venda para cancelar', min_value=1, value=None,
                               step=1, key='cancelamento_venda_numero')
        if st.button('Conferir efeitos do cancelamento',key='cancelamento_venda_preparar'):
            st.session_state.pop('cancelamento_venda_previa',None)
            try:
                if numero is None:
                    raise ValueError('Informe o número da venda.')
                st.session_state['cancelamento_venda_previa']=preparar_cancelamento(int(numero),usuario)
            except Exception as erro:
                st.error(str(erro))
        previa=st.session_state.get('cancelamento_venda_previa')
        if not previa or numero is None or int(numero)!=previa['plano']['venda']['id']:
            return
        plano=previa['plano']; venda=plano['venda']
        chave='cancelamento_venda_'+previa['token']
        st.warning(f"Venda {venda['id']} | Cliente ID {venda.get('cliente_id')} | "
                   f"Total R$ {venda['valor_final']:.2f} | {venda.get('forma_pagamento')}")
        st.write('Títulos que passarão a CANCELADO:')
        st.dataframe([{'Título':t['id'],'Descrição':t['descricao'],'Valor':t['valor'],
                       'Status atual':t['status']} for t in plano['titulos']],hide_index=True)
        st.write('Devolução ao estoque:')
        st.dataframe(plano['estoque'],hide_index=True)
        motivo=st.text_area('Motivo do cancelamento (mínimo 15 caracteres)',max_chars=500,
                            key=chave+'_motivo')
        confirmar=st.checkbox(f"Confirmo cancelar a venda {venda['id']} e seus títulos pendentes, "
                             'com a devolução de estoque mostrada acima.',key=chave+'_confirmacao')
        if st.button('Cancelar venda e títulos pendentes',disabled=not confirmar,key=chave+'_executar'):
            try:
                cancelar_venda_pendente(venda['id'],motivo,previa['token'],usuario)
            except Exception as erro:
                st.error(str(erro))
            else:
                st.session_state.pop('cancelamento_venda_previa',None)
                st.success(f"Venda {venda['id']} cancelada com auditoria. Títulos cancelados e estoque devolvido. "
                           'Nenhum recebimento ou saída de dinheiro foi gerado.')
