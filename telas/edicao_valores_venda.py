"""Edição na aba Histórico, com total fixo e auditoria."""
import streamlit as st
from database.edicao_valores_venda import carregar_edicao, salvar_edicao
from services.vendas_valores import calcular

MODALIDADES = {
    '0': '0 — Frete contratado pelo remetente (CIF)',
    '1': '1 — Frete contratado pelo destinatário (FOB)',
    '2': '2 — Frete contratado por terceiros',
    '3': '3 — Transporte próprio do remetente',
    '4': '4 — Transporte próprio do destinatário',
    '9': '9 — Sem ocorrência de transporte',
}


def mostrar_edicao_valores():
    if (not st.session_state.get('logado') or not st.session_state.get('id') or
            str(st.session_state.get('perfil', '')).strip().lower() not in ('admin','diretor')):
        return
    usuario = {k: st.session_state.get(k) for k in ('logado','id','usuario','perfil')}
    with st.expander('Editar preço e frete de venda concluída'):
        st.caption('Mantém o total, os descontos e as quantidades. Não movimenta estoque nem financeiro. '
                   'Não emita nota para a mesma venda durante a edição.')
        venda_id = st.number_input('Número da venda para corrigir', min_value=1, value=None,
                                   step=1, key='edicao_valores_numero')
        if st.button('Carregar venda para edição', key='edicao_valores_carregar'):
            st.session_state.pop('edicao_valores_dados', None)
            try:
                if venda_id is None:
                    raise ValueError('Informe o número da venda.')
                st.session_state['edicao_valores_dados'] = carregar_edicao(int(venda_id), usuario)
            except Exception as erro:
                st.error(str(erro))
        venda = st.session_state.get('edicao_valores_dados')
        if not venda or venda_id is None or int(venda_id) != venda['id']:
            return
        chave = 'edicao_valores_' + venda['token']
        st.write(f"Venda {venda['id']} — total original: R$ {venda['valor_final']:.2f}")
        precos = {}
        itens = []
        for item in venda['itens']:
            preco = st.number_input(
                f"Preço unitário — produto {item['produto_id']} / item {item['item_id']}",
                min_value=0.0, value=float(item['preco_unitario']), step=0.01,
                format='%.2f', key=chave + '_preco_' + str(item['item_id']))
            st.caption(f"Quantidade mantida: {item['quantidade']} | Desconto mantido: R$ {item['desconto']:.2f}")
            precos[item['item_id']] = preco
            itens.append(dict(item, preco_unitario=preco))
        frete = st.number_input('Frete cobrado do cliente (R$)', min_value=0.0,
                               value=float(venda['frete']), step=0.01, format='%.2f',
                               key=chave + '_frete')
        opcoes = list(MODALIDADES)
        atual = str(venda.get('mod_frete') or '9')
        mod_frete = st.selectbox('Modalidade do transporte', options=opcoes,
                                 index=opcoes.index(atual) if atual in opcoes else None,
                                 format_func=lambda k: MODALIDADES[k], key=chave + '_modalidade')
        try:
            previa = calcular(itens, frete)
        except ValueError as erro:
            st.error(str(erro))
            return
        st.write(f"Produtos: R$ {previa['valor_total']:.2f} | Frete: R$ {previa['frete']:.2f} | "
                 f"Desconto: R$ {previa['desconto']:.2f} | Total: R$ {previa['valor_final']:.2f}")
        total_confere = previa['valor_final'] == venda['valor_final']
        if not total_confere:
            st.warning('Ajuste os valores para manter o total original. O salvamento ficará bloqueado.')
        motivo = st.text_area('Motivo da correção (mínimo 15 caracteres)', max_chars=500,
                              key=chave + '_motivo')
        confirmar = st.checkbox('Confirmo a correção dos valores acima, mantendo o total original.',
                                 key=chave + '_confirmar')
        if st.button('Salvar correção de preço e frete', disabled=not (confirmar and total_confere),
                     key=chave + '_salvar'):
            try:
                salvar_edicao(venda['id'], precos, frete, mod_frete, motivo, venda['token'], usuario)
            except Exception as erro:
                st.error(str(erro))
            else:
                st.session_state.pop('edicao_valores_dados', None)
                for k in ('emissao_nfe_rascunho', 'emissao_nfe_resultado'):
                    st.session_state.pop(k, None)
                st.success('Correção salva com auditoria. Estoque, recebimentos e total foram preservados. '
                           'Prepare novamente a NF-e e confira produto e frete antes de transmitir.')
