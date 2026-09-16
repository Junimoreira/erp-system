import streamlit as st

from telas.relatorios_novo.relatorio_gerencial_vendas import (
    tela_relatorio_gerencial_vendas,
)

from telas.relatorios_novo.relatorio_vendas_detalhado import (
    tela_relatorio_vendas_detalhado,
)

from telas.relatorios_novo.relatorio_vendas_diarias import (
    tela_relatorio_vendas_diarias,
)

from telas.relatorios_novo.relatorio_vendas_clientes import (
    tela_relatorio_vendas_clientes,
)

from telas.relatorios.relatorio_formas_pagamento import (
    tela_relatorio_formas_pagamento,
)

from telas.relatorios_novo.relatorio_posicao_estoque import (
    tela_relatorio_posicao_estoque,
)

from telas.relatorios_novo.relatorio_giro_estoque import (
    tela_relatorio_giro_estoque,
)

from telas.relatorios_novo.relatorio_situacao_fiscal_produtos import (
    tela_relatorio_situacao_fiscal_produtos,
)


# ============================================================
# CENTRAL DE RELATÓRIOS
# ============================================================

def tela_relatorios():

    st.title(
        "📊 Central de Relatórios"
    )

    st.caption(
        "Relatórios gerenciais, operacionais "
        "e de conferência do ERP Verde Infância."
    )

    categoria = st.selectbox(
        "Categoria",
        [
            "Vendas",
            "Estoque",
            "Fiscal",
        ],
        index=None,
        placeholder="Selecione...",
        key=(
            "central_relatorios_"
            "categoria"
        ),
    )

    if categoria is None:

        st.info(
            "Selecione uma categoria "
            "para continuar."
        )

        return

    # ========================================================
    # VENDAS
    # ========================================================

    if categoria == "Vendas":

        relatorio = st.selectbox(
            "Relatório",
            [
                "Análise Gerencial de Vendas e Clientes",
                "Vendas por Período",
                "Vendas por Dia",
                "Vendas por Forma de Pagamento",
                "Vendas por Cliente",
            ],
            index=None,
            placeholder="Selecione...",
            key=(
                "central_relatorios_"
                "vendas_tipo"
            ),
        )

        if relatorio is None:

            st.info(
                "Selecione um relatório."
            )

            return

        if (
            relatorio
            ==
            "Análise Gerencial de Vendas e Clientes"
        ):

            tela_relatorio_gerencial_vendas()

        elif (
            relatorio
            ==
            "Vendas por Período"
        ):

            tela_relatorio_vendas_detalhado()

        elif (
            relatorio
            ==
            "Vendas por Dia"
        ):

            tela_relatorio_vendas_diarias()

        elif (
            relatorio
            ==
            "Vendas por Forma de Pagamento"
        ):

            tela_relatorio_formas_pagamento()

        elif (
            relatorio
            ==
            "Vendas por Cliente"
        ):

            tela_relatorio_vendas_clientes()

    # ========================================================
    # ESTOQUE
    # ========================================================

    elif categoria == "Estoque":

        relatorio = st.selectbox(
            "Relatório",
            [
                "Posição de Estoque",
                "Giro e Inteligência de Estoque",
            ],
            index=None,
            placeholder="Selecione...",
            key=(
                "central_relatorios_"
                "estoque_tipo"
            ),
        )

        if relatorio is None:

            st.info(
                "Selecione um relatório."
            )

            return

        if (
            relatorio
            ==
            "Posição de Estoque"
        ):

            tela_relatorio_posicao_estoque()

        elif (
            relatorio
            ==
            "Giro e Inteligência de Estoque"
        ):

            tela_relatorio_giro_estoque()

    # ========================================================
    # FISCAL
    # ========================================================

    elif categoria == "Fiscal":

        relatorio = st.selectbox(
            "Relatorio",
            [
                "Situacao Fiscal dos Produtos",
            ],
            index=None,
            placeholder="Selecione...",
            key=(
                "central_relatorios_"
                "fiscal_tipo"
            ),
        )

        if relatorio is None:

            st.info(
                "Selecione um relatorio."
            )

            return

        if (
            relatorio
            ==
            "Situacao Fiscal dos Produtos"
        ):

            tela_relatorio_situacao_fiscal_produtos()

