import streamlit as st
from datetime import date

from services.finance_service import fechar_caixa_diario


# ==================================================
# TELA: FECHAMENTO DE CAIXA
# ==================================================
def tela_fechamento_caixa():

    st.title("📊 Fechamento de Caixa Diário")

    st.write(
        "Aqui você pode conferir todas as movimentações do dia "
        "e calcular o saldo final do caixa."
    )

    st.divider()

    # ==========================================
    # SELEÇÃO DE DATA
    # ==========================================
    data_referencia = st.date_input(
        "Selecione a data do fechamento",
        value=date.today()
    )

    # ==========================================
    # BOTÃO GERAR FECHAMENTO
    # ==========================================
    if st.button("📌 Gerar fechamento"):

        resultado = fechar_caixa_diario(data_referencia)

        if resultado is None:

            st.error("Erro ao gerar fechamento de caixa.")
            return

        st.subheader("📌 Resumo do Caixa")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("💰 Entradas", f"R$ {resultado['entradas']:.2f}")
            st.metric("↩ Estornos de entrada", f"R$ {resultado['estornos_entrada']:.2f}")

        with col2:
            st.metric("💸 Saídas", f"R$ {resultado['saidas']:.2f}")
            st.metric("↩ Estornos de saída", f"R$ {resultado['estornos_saida']:.2f}")

        st.divider()

        st.success(f"💼 SALDO FINAL DO DIA: R$ {resultado['saldo_final']:.2f}")

        st.caption(f"Data analisada: {resultado['data']}")

    else:

        st.info("Selecione uma data e clique em 'Gerar fechamento' para visualizar o caixa do dia.")