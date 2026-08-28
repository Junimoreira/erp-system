from pathlib import Path

import pandas as pd
import streamlit as st

from database.vendas_db import historico_vendas
from database.vendas_fiscal_db import montar_venda_para_emissao
from database.configuracoes_fiscais_db import (
    buscar_configuracao_fiscal,
    buscar_certificado_fiscal,
)
from database.documentos_fiscais_db import buscar_documento_autorizado_por_venda
from services.fiscal.rascunho_documento_fiscal import montar_rascunho_documento_fiscal
from services.fiscal.emissor_nfe import emitir_nfe_homologacao
from services.fiscal.danfe_nfe import gerar_danfe_nfe


# ============================================================
# FORMATAR MOEDA
# ============================================================
def _formatar_moeda(valor):
    try:
        valor = float(valor or 0)
        texto = f"R$ {valor:,.2f}"
        return texto.replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return "R$ 0,00"


# ============================================================
# FORMATAR AMBIENTE
# ============================================================
def _descricao_ambiente(ambiente):
    try:
        ambiente = int(ambiente)
    except (TypeError, ValueError):
        return "Não configurado"

    if ambiente == 1:
        return "PRODUÇÃO"
    if ambiente == 2:
        return "HOMOLOGAÇÃO"
    return f"AMBIENTE {ambiente}"


# ============================================================
# LISTAR VENDAS ÚNICAS
# ============================================================
def _listar_vendas_para_selecao():
    historico = historico_vendas()

    if historico is None or historico.empty:
        return pd.DataFrame()

    colunas_necessarias = [
        "pedido",
        "cliente",
        "valor_final",
        "forma_pagamento",
        "data_venda",
        "status",
    ]

    for coluna in colunas_necessarias:
        if coluna not in historico.columns:
            return pd.DataFrame()

    vendas = (
        historico[colunas_necessarias]
        .drop_duplicates(subset=["pedido"])
        .copy()
    )

    return vendas.sort_values(by="pedido", ascending=False)


# ============================================================
# FORMATAR OPÇÃO DA VENDA
# ============================================================
def _formatar_opcao_venda(venda):
    venda_id = venda.get("pedido")
    cliente = venda.get("cliente") or "Consumidor não identificado"
    valor = _formatar_moeda(venda.get("valor_final"))
    data_venda = venda.get("data_venda")

    if pd.notna(data_venda):
        try:
            data_texto = pd.to_datetime(data_venda).strftime("%d/%m/%Y %H:%M")
        except Exception:
            data_texto = str(data_venda)
    else:
        data_texto = "-"

    return f"Venda {venda_id} | {cliente} | {valor} | {data_texto}"


# ============================================================
# LIMPAR ESTADO DE EMISSÃO
# ============================================================
def _limpar_estado_emissao():
    chaves = [
        "emissao_nfe_rascunho",
        "emissao_nfe_rascunho_venda",
        "emissao_nfe_rascunho_uf",
        "emissao_nfe_resultado",
        "emissao_nfe_resultado_venda",
        "emissao_nfe_confirmacao",
        "emissao_nfe_senha_certificado",
        "emissao_nfe_limpar_senha",
    ]

    for chave in chaves:
        st.session_state.pop(chave, None)


# ============================================================
# LIMPAR SENHA PENDENTE
# ============================================================
def _limpar_senha_pendente():
    limpar = st.session_state.pop("emissao_nfe_limpar_senha", False)

    if limpar:
        st.session_state.pop("emissao_nfe_senha_certificado", None)
        st.session_state.pop("emissao_nfe_confirmacao", None)


# ============================================================
# VERIFICAR DOCUMENTO JÁ AUTORIZADO PARA A VENDA
# ============================================================
def _buscar_documento_autorizado_venda(venda_id):
    try:
        resultado = buscar_documento_autorizado_por_venda(venda_id)

        if not resultado:
            return None

        if not resultado.get("sucesso"):
            return None

        if not resultado.get("encontrado"):
            return None

        return resultado.get("documento")

    except Exception as erro:
        print("Erro ao verificar documento fiscal da venda:", erro)
        return None


# ============================================================
# DOCUMENTOS DE NF-e J? AUTORIZADA
# ============================================================
def _mostrar_documentos_nfe_autorizada(documento):
    if not documento:
        return

    xml_processado = documento.get("xml_processado")

    if not xml_processado:
        st.warning(
            "A NF-e est? autorizada, mas o XML processado n?o est? "
            "armazenado no banco de dados."
        )
        return

    serie = documento.get("serie") or "sem_serie"
    numero = documento.get("numero") or "sem_numero"

    st.markdown("### \U0001F4C4 Documentos da NF-e")

    col_danfe, col_xml = st.columns(2)

    # --------------------------------------------------------
    # XML PROCESSADO
    # --------------------------------------------------------
    dados_xml = xml_processado.encode("utf-8")

    with col_xml:
        st.download_button(
            "\U0001F4E5 Baixar XML Processado",
            data=dados_xml,
            file_name=f"NFe_{serie}_{numero}_processada.xml",
            mime="application/xml",
            use_container_width=True,
            key=f"download_xml_autorizada_{documento.get('id')}",
        )

    # --------------------------------------------------------
    # DANFE
    # --------------------------------------------------------
    pasta_temporaria = Path("temp") / "danfes"
    pasta_temporaria.mkdir(parents=True, exist_ok=True)

    caminho_xml = (
        pasta_temporaria
        / f"nfe_{serie}_{numero}_processada.xml"
    )

    caminho_pdf = (
        pasta_temporaria
        / f"DANFE_NFe_{serie}_{numero}.pdf"
    )

    try:
        caminho_xml.write_text(
            xml_processado,
            encoding="utf-8",
        )

        resultado_danfe = gerar_danfe_nfe(
            caminho_xml=caminho_xml,
            caminho_pdf=caminho_pdf,
        )

        danfe_pronto = (
            resultado_danfe
            and resultado_danfe.get("sucesso")
            and caminho_pdf.is_file()
        )

    except Exception as erro:
        resultado_danfe = {
            "sucesso": False,
            "erros": [str(erro)],
            "avisos": [],
        }
        danfe_pronto = False

    with col_danfe:
        if danfe_pronto:
            dados_pdf = caminho_pdf.read_bytes()

            st.download_button(
                "\U0001F4C4 Baixar DANFE",
                data=dados_pdf,
                file_name=f"DANFE_NFe_{serie}_{numero}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"download_danfe_autorizada_{documento.get('id')}",
            )
        else:
            st.error("N?o foi poss?vel gerar o DANFE.")

            for erro in resultado_danfe.get("erros") or []:
                st.caption(str(erro))

    if resultado_danfe and resultado_danfe.get("sucesso"):
        for aviso in resultado_danfe.get("avisos") or []:
            st.warning(str(aviso))


# ============================================================
# MOSTRAR ERROS DO DESTINATÁRIO
# ============================================================
def _mostrar_erros_destinatario(destinatario_resultado):
    if not destinatario_resultado:
        return

    dados = (
        destinatario_resultado.get("destinatario")
        or destinatario_resultado.get("dados")
        or {}
    )

    nome = dados.get("nome") or "Cliente"
    erros = destinatario_resultado.get("erros") or []
    avisos = destinatario_resultado.get("avisos") or []

    if erros:
        st.error(f"❌ {nome} não está pronto para emissão fiscal.")
        for erro in erros:
            st.error(str(erro))

    for aviso in avisos:
        st.warning(str(aviso))


# ============================================================
# MOSTRAR EMITENTE
# ============================================================
def _mostrar_emitente(emitente):
    if not emitente:
        return

    st.markdown("### 🏢 Emitente")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Razão Social:**", emitente.get("razao_social") or "-")
        st.write("**Nome Fantasia:**", emitente.get("nome_fantasia") or "-")
        st.write("**CNPJ:**", emitente.get("cnpj") or "-")
        st.write("**Inscrição Estadual:**", emitente.get("inscricao_estadual") or "-")
        st.write("**CRT:**", emitente.get("crt") or "-")

    with col2:
        st.write(
            "**Endereço:**",
            f"{emitente.get('logradouro') or '-'}, {emitente.get('numero') or '-'}",
        )
        st.write("**Bairro:**", emitente.get("bairro") or "-")
        st.write(
            "**Cidade/UF:**",
            f"{emitente.get('cidade') or '-'} / {emitente.get('uf') or '-'}",
        )
        st.write("**CEP:**", emitente.get("cep") or "-")
        st.write("**Código IBGE:**", emitente.get("codigo_municipio_ibge") or "-")


# ============================================================
# MOSTRAR DESTINATÁRIO
# ============================================================
def _mostrar_destinatario(destinatario_resultado):
    if not destinatario_resultado:
        return

    dados = (
        destinatario_resultado.get("dados")
        or destinatario_resultado.get("destinatario")
        or {}
    )

    if not dados:
        return

    st.markdown("### 👤 Destinatário")

    documento = dados.get("cpf") or dados.get("cnpj") or "-"
    endereco = dados.get("endereco") or {}

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Nome:**", dados.get("nome") or "-")
        st.write("**Tipo:**", destinatario_resultado.get("tipo") or "-")
        st.write("**CPF/CNPJ:**", documento)
        st.write("**E-mail:**", dados.get("email") or "-")
        st.write(
            "**Indicador IE:**",
            dados.get("indicador_ie") if dados.get("indicador_ie") is not None else "-",
        )

    with col2:
        st.write(
            "**Endereço:**",
            f"{endereco.get('logradouro') or '-'}, {endereco.get('numero') or '-'}",
        )
        st.write("**Bairro:**", endereco.get("bairro") or "-")
        st.write(
            "**Cidade/UF:**",
            f"{endereco.get('cidade') or '-'} / {endereco.get('uf') or '-'}",
        )
        st.write("**CEP:**", endereco.get("cep") or "-")
        st.write("**Código IBGE:**", endereco.get("codigo_municipio_ibge") or "-")


# ============================================================
# MOSTRAR PAGAMENTO
# ============================================================
def _mostrar_pagamento(pagamento_resultado):
    if not pagamento_resultado:
        return

    dados = pagamento_resultado.get("dados") or {}
    if not dados:
        return

    st.markdown("### 💳 Pagamento")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Forma", dados.get("descricao") or "-")
    with col2:
        st.metric("Código SEFAZ", dados.get("tPag") or "-")
    with col3:
        st.metric("Valor", _formatar_moeda(dados.get("valor")))

    for aviso in pagamento_resultado.get("avisos") or []:
        st.warning(str(aviso))


# ============================================================
# MOSTRAR TOTAIS
# ============================================================
def _mostrar_totais(totais_resultado):
    if not totais_resultado:
        return

    dados = totais_resultado.get("dados") or {}
    if not dados:
        return

    st.markdown("### 💰 Totais")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Soma dos itens", _formatar_moeda(dados.get("soma_itens")))
    with col2:
        st.metric("Desconto", _formatar_moeda(dados.get("desconto")))
    with col3:
        st.metric(
            "Valor da NF-e",
            _formatar_moeda(
                dados.get("valor_final")
            ),
        )
    with col4:
        st.metric("Pagamento", _formatar_moeda(dados.get("valor_pagamento")))

    diferenca = dados.get("diferenca_pagamento")
    if diferenca is not None:
        try:
            diferenca_float = float(diferenca)
        except Exception:
            diferenca_float = 0.0

        if abs(diferenca_float) > 0.009:
            st.warning("⚠️ Existe diferença entre o valor da NF-e e o pagamento.")


# ============================================================
# MOSTRAR VALIDAÇÃO FISCAL
# ============================================================
def _mostrar_validacao_fiscal(validacao):
    if not validacao:
        return

    st.markdown("### 🔍 Validação Fiscal")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Itens", validacao.get("quantidade_itens") or 0)
    with col2:
        st.metric("Liberados", validacao.get("itens_liberados") or 0)
    with col3:
        st.metric("Bloqueados", validacao.get("itens_bloqueados") or 0)
    with col4:
        st.metric("Avisos", validacao.get("total_avisos") or 0)

    for erro in validacao.get("erros_venda") or []:
        st.error(str(erro))

    todos_avisos = []

    for item in validacao.get("itens") or []:
        produto_nome = item.get("produto_nome") or item.get("descricao") or "Produto"

        for erro in item.get("erros") or []:
            st.error(f"{produto_nome}: {erro}")

        for aviso in item.get("avisos") or []:
            todos_avisos.append((produto_nome, aviso))

    if todos_avisos:
        st.markdown("#### ⚠️ Avisos fiscais")
        for produto_nome, aviso in todos_avisos:
            st.warning(f"{produto_nome}: {aviso}")

    if validacao.get("pode_emitir"):
        st.success("✅ A validação fiscal permite a emissão deste documento.")


# ============================================================
# MOSTRAR RESULTADO DA EMISSÃO
# ============================================================
def _mostrar_resultado_emissao(resultado):
    st.divider()
    st.markdown("## 📡 Resultado da emissão")

    if not resultado:
        return

    if not resultado.get("sucesso"):
        st.error("❌ A emissão não foi concluída.")
        st.write("**Etapa:**", resultado.get("etapa") or "-")
        st.write(
            "**Mensagem:**",
            resultado.get("mensagem") or "Falha não especificada.",
        )

        # ====================================================
        # RETORNO DETALHADO DA SEFAZ
        # ====================================================
        retorno = (
            resultado.get("retorno")
            or resultado.get("retorno_sefaz")
            or {}
        )

        if retorno:
            st.markdown("### 📡 Retorno da SEFAZ")

            cstat_lote = retorno.get("cStat_lote")
            motivo_lote = retorno.get("xMotivo_lote")
            numero_recibo = retorno.get("nRec")

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "cStat",
                    cstat_lote or "-",
                )

            with col2:
                st.write(
                    "**Motivo:**",
                    motivo_lote or "-",
                )

            if numero_recibo:
                st.write(
                    "**Recibo:**",
                    numero_recibo,
                )

            protocolos = retorno.get("protocolos") or []

            if protocolos:
                st.markdown("#### Protocolo / rejeição da NF-e")

                for protocolo in protocolos:
                    st.write(
                        "**cStat:**",
                        protocolo.get("cStat") or "-",
                    )

                    st.write(
                        "**Motivo:**",
                        protocolo.get("xMotivo") or "-",
                    )

                    if protocolo.get("nProt"):
                        st.write(
                            "**Protocolo:**",
                            protocolo.get("nProt"),
                        )

                    if protocolo.get("chNFe"):
                        st.write(
                            "**Chave:**",
                            protocolo.get("chNFe"),
                        )

        # ====================================================
        # RESPOSTA TÉCNICA BRUTA DA SEFAZ
        # ====================================================
        resposta_bruta = resultado.get("resposta_bruta")

        if resposta_bruta:
            with st.expander("🔎 Ver resposta técnica da SEFAZ"):
                st.code(
                    resposta_bruta,
                    language="xml",
                )

        # ====================================================
        # PROTEÇÃO CONTRA RETRANSMISSÃO
        # ====================================================
        if resultado.get("nao_retransmitir"):
            st.error(
                "🚫 NÃO retransmita esta NF-e. "
                "O ERP identificou uma situação que precisa "
                "ser conferida antes de um novo envio."
            )

        # ====================================================
        # ARQUIVOS DISPONÍVEIS
        # ====================================================
        arquivos_erro = resultado.get("arquivos") or {}

        if arquivos_erro:
            st.markdown("### 📁 Arquivos disponíveis")

            for nome, caminho in arquivos_erro.items():
                st.write(
                    f"**{nome}:**",
                    caminho,
                )

        return

    st.success("✅ NF-e emitida e finalizada com sucesso.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Série", resultado.get("serie") or "-")
    with col2:
        st.metric("Número", resultado.get("numero") or "-")

    retorno_sefaz = resultado.get("retorno_sefaz") or {}
    protocolos = retorno_sefaz.get("protocolos") or []
    protocolo = protocolos[0] if protocolos else {}

    with col3:
        st.metric("cStat", protocolo.get("cStat") or "-")

    st.write("**Chave de acesso:**", resultado.get("chave_acesso") or "-")
    st.write("**Protocolo:**", protocolo.get("nProt") or "-")
    st.write(
        "**Motivo SEFAZ:**",
        protocolo.get("xMotivo") or retorno_sefaz.get("xMotivo_lote") or "-",
    )

    arquivos = resultado.get("arquivos") or {}

    if arquivos:
        st.markdown("### 📁 Arquivos fiscais")
        for nome, caminho in arquivos.items():
            st.write(f"**{nome}:**", caminho)

    caminho_processado = arquivos.get("processado") if arquivos else None

    if not caminho_processado:
        st.warning("⚠️ O XML processado não foi informado pelo emissor.")
        return

    xml_processado = Path(caminho_processado)

    if not xml_processado.is_file():
        st.warning(
            "⚠️ O XML processado foi informado, mas o arquivo não foi localizado nesta máquina."
        )
        st.code(str(xml_processado), language=None)
        return

    st.divider()
    st.markdown("## 📄 Documentos da NF-e")
    st.caption("O XML processado contém a NF-e autorizada e o protocolo da SEFAZ.")

    serie = resultado.get("serie") or "sem_serie"
    numero = resultado.get("numero") or "sem_numero"

    pasta_danfe = xml_processado.parent / "danfes"
    pasta_danfe.mkdir(parents=True, exist_ok=True)

    caminho_danfe = pasta_danfe / f"danfe_nfe_serie_{serie}_numero_{numero}.pdf"

    try:
        resultado_danfe = gerar_danfe_nfe(
            caminho_xml=xml_processado,
            caminho_pdf=caminho_danfe,
        )
    except Exception as erro:
        resultado_danfe = {
            "sucesso": False,
            "erros": [str(erro)],
            "avisos": [],
        }

    col_danfe, col_xml = st.columns(2)

    with col_danfe:
        danfe_pronto = (
            resultado_danfe
            and resultado_danfe.get("sucesso")
            and caminho_danfe.is_file()
        )

        if danfe_pronto:
            try:
                dados_pdf = caminho_danfe.read_bytes()
                st.download_button(
                    "📄 Baixar DANFE",
                    data=dados_pdf,
                    file_name=f"DANFE_NFe_{serie}_{numero}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"download_danfe_{serie}_{numero}",
                )
            except Exception as erro:
                st.error("Não foi possível preparar o DANFE para download.")
                st.caption(str(erro))
        else:
            st.error("❌ Não foi possível gerar o DANFE.")
            for erro in (resultado_danfe or {}).get("erros") or []:
                st.caption(str(erro))

    with col_xml:
        try:
            dados_xml = xml_processado.read_bytes()
            st.download_button(
                "📥 Baixar XML Processado",
                data=dados_xml,
                file_name=f"NFe_{serie}_{numero}_processada.xml",
                mime="application/xml",
                use_container_width=True,
                key=f"download_xml_nfe_{serie}_{numero}",
            )
        except Exception as erro:
            st.error("Não foi possível preparar o XML para download.")
            st.caption(str(erro))

    if resultado_danfe and resultado_danfe.get("sucesso"):
        protocolo_danfe = resultado_danfe.get("protocolo")

        if protocolo_danfe:
            st.success("✅ DANFE gerado a partir da NF-e autorizada pela SEFAZ.")
        else:
            st.warning("⚠️ O DANFE foi gerado sem protocolo de autorização.")

        for aviso in resultado_danfe.get("avisos") or []:
            st.warning(str(aviso))

        st.caption(f"DANFE: {caminho_danfe}")


# ============================================================
# TELA DE EMISSÃO NF-e
# ============================================================
def tela_emissao_nfe():
    _limpar_senha_pendente()

    st.title("🧾 Emissão de NF-e")
    st.caption("Emissão de Nota Fiscal Eletrônica modelo 55.")

    # ========================================================
    # CONFIGURAÇÃO FISCAL
    # ========================================================
    configuracao = buscar_configuracao_fiscal()

    if not configuracao:
        st.error("Configuração fiscal ativa não encontrada.")
        return

    ambiente = configuracao.get("ambiente")
    serie = configuracao.get("serie_nfe")
    proximo_numero = configuracao.get("proximo_numero_nfe")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Ambiente", _descricao_ambiente(ambiente))
    with col2:
        st.metric("Série NF-e", serie if serie is not None else "-")
    with col3:
        st.metric("Próxima NF-e", proximo_numero if proximo_numero is not None else "-")

    if ambiente == 2:
        st.info("🧪 O emissor está configurado em HOMOLOGAÇÃO.")
    elif ambiente == 1:
        st.error("🚨 ATENÇÃO: o emissor está configurado em PRODUÇÃO.")
        st.warning(
            "A transmissão pela interface está bloqueada enquanto este módulo estiver em fase de homologação."
        )

    st.divider()

    # ========================================================
    # CERTIFICADO
    # ========================================================
    certificado = buscar_certificado_fiscal()

    certificado_pronto = (
        certificado.get("sucesso")
        and certificado.get("configurado")
        and certificado.get("existe")
    )

    if certificado_pronto:
        st.success("🔐 Certificado Digital A1 disponível.")
        st.caption(certificado.get("nome_arquivo") or "")
    else:
        st.error("❌ Certificado Digital A1 indisponível.")
        st.write(
            certificado.get("mensagem")
            or "Configure o certificado em Configurações → Fiscal."
        )

    st.divider()

    # ========================================================
    # VENDAS
    # ========================================================
    vendas = _listar_vendas_para_selecao()

    if vendas.empty:
        st.warning("Nenhuma venda disponível para análise.")
        return

    registros_vendas = vendas.to_dict(orient="records")
    mapa_vendas = {int(venda["pedido"]): venda for venda in registros_vendas}
    ids_vendas = list(mapa_vendas.keys())

    venda_id = st.selectbox(
        "Venda para emissão",
        options=ids_vendas,
        index=None,
        placeholder="Selecione uma venda...",
        format_func=lambda valor: _formatar_opcao_venda(mapa_vendas[valor]),
        key="emissao_nfe_venda_id",
    )

    if venda_id is None:
        _limpar_estado_emissao()
        st.info("Selecione uma venda para iniciar a preparação da NF-e.")
        return

    # ========================================================
    # VENDA JÁ AUTORIZADA
    # ========================================================
    documento_existente = _buscar_documento_autorizado_venda(venda_id)

    if documento_existente:
        st.error("🚫 Esta venda já possui uma NF-e AUTORIZADA registrada no ERP.")
        st.write("**NF-e:**", documento_existente.get("numero") or "-")
        st.write("**Série:**", documento_existente.get("serie") or "-")
        st.write("**Chave:**", documento_existente.get("chave_acesso") or "-")
        st.write("**Protocolo:**", documento_existente.get("protocolo") or "-")
        st.warning("Uma nova emissão para esta venda foi bloqueada para evitar duplicidade.")

        _mostrar_documentos_nfe_autorizada(
            documento_existente
        )

        return

    # ========================================================
    # CARREGAR VENDA
    # ========================================================
    resultado_venda = montar_venda_para_emissao(venda_id)

    if not resultado_venda.get("sucesso"):
        st.error(resultado_venda.get("mensagem") or "Não foi possível carregar a venda.")
        return

    venda = resultado_venda.get("venda") or {}
    itens = venda.get("itens") or []
    venda_historico = mapa_vendas.get(venda_id, {})

    # ========================================================
    # RESUMO
    # ========================================================
    st.markdown("### 📋 Venda selecionada")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Venda", venda_id)
    with col2:
        st.metric("Valor", _formatar_moeda(venda.get("valor_final")))
    with col3:
        st.metric("Forma de pagamento", venda.get("forma_pagamento") or "-")

    st.write("**Cliente:**", venda_historico.get("cliente") or "Consumidor não identificado")
    st.write("**Status da venda:**", venda.get("status") or "-")

    st.divider()

    # ========================================================
    # ITENS
    # ========================================================
    st.markdown("### 📦 Itens da venda")

    if not itens:
        st.warning("A venda não possui itens.")
        return

    tabela_itens = []

    for item in itens:
        tabela_itens.append(
            {
                "Produto": item.get("produto_nome"),
                "Quantidade": item.get("quantidade"),
                "Valor Unitário": _formatar_moeda(item.get("preco_unitario")),
                "Subtotal": _formatar_moeda(item.get("subtotal")),
                "NCM": item.get("ncm"),
                "CEST": item.get("cest"),
                "CFOP Interno": item.get("cfop_saida_interna"),
                "CSOSN Interno": item.get("csosn_saida_interna"),
                "Revisado": "Sim" if item.get("fiscal_revisado") else "Não",
            }
        )

    st.dataframe(
        pd.DataFrame(tabela_itens),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ========================================================
    # PREPARAÇÃO
    # ========================================================
    st.markdown("### 🧾 Preparação fiscal")

    uf_destino = st.selectbox(
        "UF de destino",
        options=["MG", "SP", "RJ", "ES", "PR", "SC", "RS", "GO", "DF", "BA"],
        index=None,
        placeholder="Selecione a UF de destino...",
        key="emissao_nfe_uf_destino",
    )

    if uf_destino is None:
        st.info("Selecione a UF de destino para preparar a NF-e.")
        return

    if st.button(
        "🔎 Preparar NF-e",
        type="primary",
        use_container_width=True,
        key="btn_preparar_nfe",
    ):
        with st.spinner("Preparando dados fiscais..."):
            rascunho = montar_rascunho_documento_fiscal(
                venda_id=venda_id,
                modelo=55,
                uf_destino=uf_destino,
            )

        st.session_state["emissao_nfe_rascunho"] = rascunho
        st.session_state["emissao_nfe_rascunho_venda"] = venda_id
        st.session_state["emissao_nfe_rascunho_uf"] = uf_destino
        st.session_state.pop("emissao_nfe_resultado", None)
        st.session_state.pop("emissao_nfe_resultado_venda", None)

    rascunho = st.session_state.get("emissao_nfe_rascunho")

    if (
        not rascunho
        or st.session_state.get("emissao_nfe_rascunho_venda") != venda_id
        or st.session_state.get("emissao_nfe_rascunho_uf") != uf_destino
    ):
        return

    st.divider()

    # ========================================================
    # RESULTADO DA PREPARAÇÃO
    # ========================================================
    st.markdown("## ✅ Resultado da preparação")

    sucesso = bool(rascunho.get("sucesso"))
    pode_gerar = bool(rascunho.get("pode_gerar_xml"))

    if sucesso and pode_gerar:
        st.success("✅ Venda aprovada para geração do XML da NF-e.")
    else:
        st.error("❌ A venda ainda não está pronta para emissão da NF-e.")

    if rascunho.get("mensagem"):
        st.write("**Mensagem:**", rascunho.get("mensagem"))

    destinatario_resultado = rascunho.get("destinatario") or {}

    if not sucesso:
        _mostrar_erros_destinatario(destinatario_resultado)

        for erro in rascunho.get("erros") or []:
            st.error(str(erro))

        st.info(
            "Corrija o cadastro fiscal ou os dados indicados acima e prepare novamente a NF-e."
        )
        return

    # ========================================================
    # CABEÇALHO FISCAL
    # ========================================================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Modelo", rascunho.get("modelo") or "-")
    with col2:
        st.metric("Série", rascunho.get("serie") or "-")
    with col3:
        st.metric("Número", rascunho.get("numero_sugerido") or "-")
    with col4:
        st.metric("UF destino", rascunho.get("uf_destino") or "-")

    st.divider()
    _mostrar_emitente(rascunho.get("emitente"))
    st.divider()
    _mostrar_destinatario(destinatario_resultado)
    st.divider()

    # ========================================================
    # TRIBUTAÇÃO
    # ========================================================
    st.markdown("### 📑 Tributação preparada")

    tabela_fiscal = []
    for item in rascunho.get("itens") or []:
        tabela_fiscal.append(
            {
                "Item": item.get("numero_item"),
                "Produto": item.get("descricao"),
                "NCM": item.get("ncm"),
                "CEST": item.get("cest"),
                "Origem": item.get("origem_mercadoria"),
                "CFOP": item.get("cfop"),
                "CSOSN": item.get("csosn"),
                "CST PIS": item.get("cst_pis"),
                "Alíquota PIS": item.get("aliquota_pis"),
                "CST COFINS": item.get("cst_cofins"),
                "Alíquota COFINS": item.get("aliquota_cofins"),
                "CST IBS/CBS": item.get("cst_ibs_cbs"),
                "Classificação IBS/CBS": item.get("classificacao_tributaria"),
            }
        )

    st.dataframe(
        pd.DataFrame(tabela_fiscal),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    _mostrar_pagamento(rascunho.get("pagamento"))
    st.divider()
    _mostrar_totais(rascunho.get("totais"))
    st.divider()
    _mostrar_validacao_fiscal(rascunho.get("validacao"))
    st.divider()

    # ========================================================
    # REVISÃO FINAL
    # ========================================================
    st.markdown("## 📋 Revisão final")

    totais_dados = ((rascunho.get("totais") or {}).get("dados") or {})

    st.write("**Venda:**", venda_id)
    st.write("**Modelo:** 55")
    st.write("**Série:**", rascunho.get("serie") or "-")
    st.write("**Número previsto:**", rascunho.get("numero_sugerido") or "-")
    st.write("**Ambiente:**", _descricao_ambiente(rascunho.get("ambiente")))
    st.write(
        "**Valor total:**",
        _formatar_moeda(
            totais_dados.get("valor_final")
        ),
    )

    if not pode_gerar:
        return

    st.success("✅ Documento fiscalmente preparado para emissão.")

    # ========================================================
    # EMISSÃO CONTROLADA
    # ========================================================
    st.divider()
    st.markdown("## 📡 Transmissão para a SEFAZ")

    if ambiente != 2:
        st.error("🚫 Emissão bloqueada. Esta tela está habilitada somente para HOMOLOGAÇÃO.")
        return

    if not certificado_pronto:
        st.error("🚫 Emissão bloqueada porque o certificado digital não está disponível.")
        return

    caminho_certificado = certificado.get("caminho")

    if not caminho_certificado:
        st.error("Caminho do certificado não informado.")
        return

    if not Path(caminho_certificado).is_file():
        st.error("O arquivo do certificado não foi localizado nesta máquina.")
        return

    # --------------------------------------------------------
    # CONFERÊNCIA DE NUMERAÇÃO
    # --------------------------------------------------------
    configuracao_atual = buscar_configuracao_fiscal()

    if not configuracao_atual:
        st.error("Não foi possível reconferir a configuração fiscal.")
        return

    serie_atual = configuracao_atual.get("serie_nfe")
    numero_atual = configuracao_atual.get("proximo_numero_nfe")

    if (
        serie_atual != rascunho.get("serie")
        or numero_atual != rascunho.get("numero_sugerido")
    ):
        st.error("🚫 O rascunho ficou desatualizado.")
        st.warning(
            "A série ou o próximo número da NF-e mudou desde a preparação. "
            "Clique novamente em Preparar NF-e antes de transmitir."
        )
        return

    st.warning(
        "⚠️ Ao confirmar abaixo, a NF-e será realmente transmitida para a SEFAZ-MG "
        "no ambiente de HOMOLOGAÇÃO."
    )

    confirmacao = st.checkbox(
        "Confirmo que revisei os dados acima e desejo transmitir esta NF-e em HOMOLOGAÇÃO.",
        value=False,
        key="emissao_nfe_confirmacao",
    )

    senha_certificado = st.text_input(
        "Senha do Certificado Digital A1",
        type="password",
        value="",
        key="emissao_nfe_senha_certificado",
        help="A senha é utilizada apenas durante esta emissão e não é armazenada pelo ERP.",
    )

    senha_preenchida = bool(senha_certificado and senha_certificado.strip())
    pronto_para_emitir = confirmacao and senha_preenchida

    if not confirmacao:
        st.info("Marque a confirmação para liberar o botão de emissão.")
    elif not senha_preenchida:
        st.info("Informe a senha do certificado para liberar a emissão.")

    # --------------------------------------------------------
    # BOTÃO DE EMISSÃO
    # --------------------------------------------------------
    if st.button(
        "📡 Emitir NF-e em Homologação",
        type="primary",
        use_container_width=True,
        disabled=not pronto_para_emitir,
        key="btn_emitir_nfe_homologacao",
    ):
        documento_existente = _buscar_documento_autorizado_venda(venda_id)

        if documento_existente:
            st.error(
                "A emissão foi cancelada porque esta venda já possui documento fiscal autorizado."
            )
            return

        with st.spinner("Transmitindo NF-e para a SEFAZ-MG em homologação..."):
            try:
                resultado_emissao = emitir_nfe_homologacao(
                    venda_id=venda_id,
                    uf_destino=uf_destino,
                    caminho_certificado=caminho_certificado,
                    senha_certificado=senha_certificado,
                )
            except Exception as erro:
                resultado_emissao = {
                    "sucesso": False,
                    "etapa": "EXCECAO_INTERFACE",
                    "mensagem": str(erro),
                }

        # Não alteramos diretamente o widget da senha aqui.
        # A limpeza ocorre no próximo rerun.
        st.session_state["emissao_nfe_limpar_senha"] = True
        st.session_state["emissao_nfe_resultado"] = resultado_emissao
        st.session_state["emissao_nfe_resultado_venda"] = venda_id

    # ========================================================
    # RESULTADO DA EMISSÃO
    # ========================================================
    resultado_emissao = st.session_state.get("emissao_nfe_resultado")
    resultado_venda_id = st.session_state.get("emissao_nfe_resultado_venda")

    if resultado_emissao and resultado_venda_id == venda_id:
        _mostrar_resultado_emissao(resultado_emissao)
