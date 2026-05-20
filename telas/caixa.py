# telas/caixa.py

import streamlit as st
import pandas as pd
from datetime import datetime

from database.movimentacoes_db import (
    registrar_movimentacao,
    listar_movimentacoes,
    atualizar_movimentacao,
    excluir_movimentacao
)

from database.caixa_db import (
    verificar_caixa_aberto,
    abrir_caixa,
    fechar_caixa,
    resumo_caixa,
    listar_movimentacoes_caixa
)


# ==================================================
# TELA CAIXA
# ==================================================
def tela_caixa():

    abas = st.tabs([
        "💰 Caixa",
        "➕ Movimentar Caixa"
    ])

    # ==================================================
    # ABA CAIXA
    # ==================================================
    with abas[0]:

        st.subheader("💰 Controle de Caixa")

        # ==================================================
        # VERIFICA CAIXA
        # ==================================================
        caixa = verificar_caixa_aberto()

        caixa_aberto = False

        if caixa is not None:

            if isinstance(caixa, pd.DataFrame):

                if not caixa.empty:

                    caixa = caixa.iloc[0]
                    caixa_aberto = True

            elif isinstance(caixa, pd.Series):

                caixa_aberto = True

            elif isinstance(caixa, dict):

                if len(caixa) > 0:
                    caixa_aberto = True

        # ==================================================
        # SEM CAIXA ABERTO
        # ==================================================
        if not caixa_aberto:

            st.warning("🔓 Nenhum caixa aberto.")

            valor_inicial = st.number_input(
                "Valor Inicial",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                key="valor_inicial_caixa"
            )

            usuario = st.text_input(
                "Operador",
                value="Administrador",
                key="operador_caixa"
            )

            if st.button(
                "🚀 Abrir Caixa",
                key="btn_abrir_caixa"
            ):

                sucesso = abrir_caixa(
                    usuario=usuario,
                    saldo_inicial=float(valor_inicial)
                )

                if sucesso:

                    st.success("✅ Caixa aberto com sucesso!")
                    st.rerun()

                else:

                    st.error("❌ Erro ao abrir caixa.")

        # ==================================================
        # CAIXA ABERTO
        # ==================================================
        else:

            caixa_id = int(caixa["id"])

            st.success("🟢 Caixa Aberto")

            resumo = resumo_caixa(caixa_id)

            if resumo is None:

                resumo = {
                    "entradas": 0,
                    "saidas": 0
                }

            entradas = float(
                resumo.get("entradas", 0)
            )

            saidas = float(
                resumo.get("saidas", 0)
            )

            saldo_inicial = float(
                caixa.get("saldo_inicial", 0)
            )

            saldo_atual = (
                saldo_inicial
                + entradas
                - saidas
            )

            # ==================================================
            # MÉTRICAS
            # ==================================================
            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Saldo Inicial",
                    f"R$ {saldo_inicial:,.2f}"
                )

            with col2:

                st.metric(
                    "Entradas",
                    f"R$ {entradas:,.2f}"
                )

            with col3:

                st.metric(
                    "Saídas",
                    f"R$ {saidas:,.2f}"
                )

            st.divider()

            st.metric(
                "💰 Saldo Atual",
                f"R$ {saldo_atual:,.2f}"
            )

            # ==================================================
            # MOVIMENTAÇÕES
            # ==================================================
            st.subheader("📋 Movimentações")

            df = listar_movimentacoes_caixa(
                caixa_id
            )

            if df is not None and not df.empty:

                df_exibir = df.copy()

                # ==================================================
                # FORMATA VALORES
                # ==================================================
                if "valor" in df_exibir.columns:

                    df_exibir["valor"] = df_exibir[
                        "valor"
                    ].apply(
                        lambda x: f"R$ {float(x):,.2f}"
                    )

                # ==================================================
                # FORMATA DATAS
                # ==================================================
                if "data_movimentacao" in df_exibir.columns:

                    df_exibir["data_movimentacao"] = pd.to_datetime(
                        df_exibir["data_movimentacao"],
                        errors="coerce"
                    )

                    df_exibir["data_movimentacao"] = df_exibir[
                        "data_movimentacao"
                    ].dt.strftime("%d/%m/%Y %H:%M")

                st.dataframe(
                    df_exibir,
                    width="stretch"
                )

                # ==================================================
                # EDITAR / EXCLUIR
                # ==================================================
                st.divider()

                st.subheader(
                    "✏️ Editar / Excluir Movimentação"
                )

                movs = listar_movimentacoes()

                if movs is not None and not movs.empty:

                    opcoes = {
                        f"{row['id']} - {row['descricao']}": row
                        for _, row in movs.iterrows()
                    }

                    selecionado = st.selectbox(
                        "Selecione a movimentação",
                        list(opcoes.keys()),
                        key="select_movimentacao"
                    )

                    mov = opcoes[selecionado]

                    novo_tipo = st.selectbox(
                        "Tipo",
                        ["entrada", "saida"],
                        index=0 if mov["tipo"] == "entrada" else 1,
                        key="editar_movimentacao_tipo"
                    )

                    novo_valor = st.number_input(
                        "Valor da Movimentação",
                        min_value=0.0,
                        value=float(mov["valor"]),
                        format="%.2f",
                        key="editar_movimentacao_valor"
                    )

                    nova_descricao = st.text_input(
                        "Descrição da Movimentação",
                        value=mov["descricao"]
                        if mov["descricao"]
                        else "",
                        key="editar_movimentacao_descricao"
                    )

                    lista_origens = [
                        "Sangria",
                        "Reforço",
                        "Despesa",
                        "Ajuste"
                    ]

                    origem_atual = (
                        mov["origem"]
                        if mov["origem"] in lista_origens
                        else "Ajuste"
                    )

                    nova_origem = st.selectbox(
                        "Origem",
                        lista_origens,
                        index=lista_origens.index(
                            origem_atual
                        ),
                        key="editar_movimentacao_origem"
                    )

                    col_ed1, col_ed2 = st.columns(2)

                    # ==================================================
                    # ATUALIZAR
                    # ==================================================
                    with col_ed1:

                        if st.button(
                            "💾 Atualizar Movimentação",
                            key="btn_atualizar_mov"
                        ):

                            sucesso = atualizar_movimentacao(

                                int(mov["id"]),
                                novo_tipo,
                                float(novo_valor),
                                nova_descricao,
                                nova_origem

                            )

                            if sucesso:

                                st.success(
                                    "✅ Movimentação atualizada!"
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "❌ Erro ao atualizar."
                                )

                    # ==================================================
                    # EXCLUIR
                    # ==================================================
                    with col_ed2:

                        if st.button(
                            "🗑️ Excluir Movimentação",
                            key="btn_excluir_mov"
                        ):

                            sucesso = excluir_movimentacao(
                                int(mov["id"])
                            )

                            if sucesso:

                                st.success(
                                    "✅ Movimentação excluída!"
                                )

                                st.rerun()

                            else:

                                st.error(
                                    "❌ Erro ao excluir."
                                )

            else:

                st.info(
                    "Nenhuma movimentação registrada."
                )

            st.divider()

            # ==================================================
            # FECHAMENTO
            # ==================================================
            st.subheader("🔒 Fechar Caixa")

            valor_conferido = st.number_input(
                "Valor Conferido no Caixa",
                min_value=0.0,
                value=float(saldo_atual),
                format="%.2f",
                key="valor_conferido_caixa"
            )

            diferenca = (
                float(valor_conferido)
                - float(saldo_atual)
            )

            if diferenca == 0:

                st.success(
                    "✅ Caixa conferido sem diferenças."
                )

            elif diferenca > 0:

                st.warning(
                    f"⚠️ Sobra no caixa: "
                    f"R$ {diferenca:,.2f}"
                )

            else:

                st.error(
                    f"❌ Falta no caixa: "
                    f"R$ {abs(diferenca):,.2f}"
                )

            # ==================================================
            # FECHAR CAIXA
            # ==================================================
            if st.button(
                "💾 Fechar Caixa",
                key="btn_fechar_caixa"
            ):

                sucesso = fechar_caixa(
                    caixa_id=int(caixa_id),
                    total_entradas=float(entradas),
                    total_saidas=float(saidas),
                    saldo_final=float(saldo_atual),
                    valor_conferido=float(valor_conferido),
                    diferenca=float(diferenca)
                )

                if sucesso:

                    st.success(
                        "✅ Caixa fechado com sucesso!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Erro ao fechar caixa."
                    )

    # ==================================================
    # ABA MOVIMENTAR CAIXA
    # ==================================================
    with abas[1]:

        st.subheader("➕ Nova Movimentação")

        caixa = verificar_caixa_aberto()

        if caixa is None:

            st.warning(
                "Abra um caixa antes de registrar movimentações."
            )

            return

        caixa_id = int(caixa["id"])

        tipo = st.selectbox(
            "Tipo",
            ["entrada", "saida"],
            key="nova_movimentacao_tipo"
        )

        valor = st.number_input(
            "Valor",
            min_value=0.0,
            value=0.0,
            format="%.2f",
            key="nova_movimentacao_valor"
        )

        descricao = st.text_input(
            "Descrição",
            key="nova_movimentacao_descricao"
        )

        origem = st.selectbox(
            "Origem",
            [
                "Sangria",
                "Reforço",
                "Despesa",
                "Ajuste"
            ],
            key="nova_movimentacao_origem"
        )

        if st.button(
            "💾 Registrar Movimentação",
            key="btn_registrar_movimentacao"
        ):

            if valor <= 0:

                st.warning(
                    "Informe um valor maior que zero."
                )

            else:

                sucesso = registrar_movimentacao(

                    caixa_id=int(caixa_id),
                    tipo=tipo,
                    valor=float(valor),
                    descricao=descricao,
                    origem=origem,
                    data_movimentacao=datetime.now()

                )

                if sucesso:

                    st.success(
                        "✅ Movimentação registrada!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "❌ Erro ao registrar."
                    )