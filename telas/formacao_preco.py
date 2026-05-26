import streamlit as st
from services.finance_service import calcular_preco_venda


def tela_formacao_preco():

    st.title("💰 Formação de Preço de Venda")

    custo = st.number_input("Custo do produto", min_value=0.0)

    imposto = st.number_input("Impostos (%)", min_value=0.0)
    frete = st.number_input("Frete (%)", min_value=0.0)
    taxa_cartao = st.number_input("Taxa cartão (%)", min_value=0.0)
    margem = st.number_input("Margem de lucro (%)", min_value=0.0)

    st.divider()
    st.info("💡 Dica: Insira valores em percentual (ex: 10 = 10%)")

    if st.button("Calcular preço"):

        try:
            preco = calcular_preco_venda(
                custo,
                imposto,
                frete,
                taxa_cartao,
                margem
            )

            st.success(f"💰 Preço de venda sugerido: R$ {preco:.2f}")

        except Exception as e:
            st.error(str(e))