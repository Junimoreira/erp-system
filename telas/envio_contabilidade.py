from datetime import date
import streamlit as st
from services.fiscal.envio_contabilidade import consultar_documentos, gerar_pacote


def tela_envio_contabilidade():
    st.title('📦 Envio à Contabilidade')
    st.caption('XMLs de produção armazenados no ERP, agrupados por mês de emissão.')
    st.info('Primeira versão: entradas, NF-e e NFC-e. Eventos de cancelamento, CC-e, inutilizações e DANFEs ainda não são incluídos.')
    hoje = date.today()
    with st.form('competencia_contabilidade'):
        col1, col2 = st.columns(2)
        ano = col1.number_input('Ano', min_value=2000, max_value=2100, value=hoje.year, step=1)
        mes = col2.selectbox('Mês', range(1, 13), index=None, placeholder='Selecione o mês', format_func=lambda m: f'{m:02d}')
        gerar = st.form_submit_button('Conferir e gerar pacote')
    if gerar:
        st.session_state.pop('pacote_contabilidade', None)
        if mes is None:
            st.warning('Selecione o mês.')
            return
        try:
            with st.spinner('Consultando documentos e conferindo XMLs...'):
                documentos = consultar_documentos(int(ano), mes)
                dados = gerar_pacote(documentos, int(ano), mes)
            st.session_state['pacote_contabilidade'] = (int(ano), mes, dados)
        except Exception as erro:
            st.error(f'Não foi possível gerar o pacote: {erro}')
    resultado = st.session_state.get('pacote_contabilidade')
    if resultado:
        ano_p, mes_p, (zip_bytes, resumo, pendencias, quantidade) = resultado
        st.subheader(f'Competência {mes_p:02d}/{ano_p}')
        c1, c2, c3 = st.columns(3)
        c1.metric('Documentos de produção', len(resumo))
        c2.metric('XMLs incluídos', quantidade)
        c3.metric('Pendências', len(pendencias))
        if pendencias:
            st.warning('Existem pendências. Confira a relação antes de encaminhar o pacote.')
            st.dataframe(pendencias, use_container_width=True, hide_index=True)
        if not resumo:
            st.info('Nenhum documento de produção cadastrado para esse período.')
        else:
            with st.expander('Resumo dos documentos'):
                st.dataframe(resumo, use_container_width=True, hide_index=True)
            st.download_button('Baixar ZIP para conferência e envio', zip_bytes,
                               file_name=f'Fiscal_{ano_p}_{mes_p:02d}.zip', mime='application/zip')
