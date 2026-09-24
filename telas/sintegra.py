import calendar
from datetime import date

import streamlit as st

from database.sintegra_db import (
    listar_itens_entrada_competencia,
    listar_nfce_saida_competencia,
    listar_pendencias_data_entrada,
)
from services.fiscal.sintegra_validacao import (
    validar_competencia_entrada,
)
from database.configuracoes_fiscais_db import (
    buscar_configuracao_fiscal,
)
from services.fiscal.sintegra_xml import (
    ler_xml_sintegra,
)
from services.fiscal.sintegra import (
    gerar_registro_10,
    gerar_registro_11,
    gerar_registro_54,
    gerar_registros_54_despesas_acessorias,
    gerar_registros_50_agrupados,
    preparar_itens_registro_50,
    gerar_registros_61_61r,
    gerar_registros_75,
    montar_arquivo_sintegra,
    serializar_arquivo_sintegra,
)


MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def _periodo_competencia(ano, mes):
    ultimo_dia = calendar.monthrange(
        ano,
        mes,
    )[1]

    return (
        date(ano, mes, 1),
        date(ano, mes, ultimo_dia),
    )


def _competencia_encerrada(ano, mes):
    hoje = date.today()

    return (
        (ano, mes)
        <
        (hoje.year, hoje.month)
    )


def _documentos_entrada(itens):
    documentos = set()

    for item in itens or []:
        identificador = (
            item.get("documento_fiscal_id")
            or item.get("fiscal_documento_id")
            or item.get("chave_acesso")
            or item.get("chave_nfe")
            or item.get("compra_id")
        )

        if identificador is not None:
            documentos.add(
                str(identificador)
            )

    return len(documentos)


def _documentos_nfce(documentos):
    identificadores = set()

    for documento in documentos or []:
        identificador = (
            documento.get("id")
            or documento.get("chave_acesso")
        )

        if identificador is not None:
            identificadores.add(
                str(identificador)
            )

    return len(identificadores)




def _normalizar_documento_para_sintegra(
    documento,
):
    """
    Adapta o documento lido do XML para
    o contrato usado pelos Registros
    61, 61R e 75.

    Nao altera o documento original.
    """
    normalizado = dict(
        documento or {}
    )

    itens_normalizados = []

    for item_original in (
        normalizado.get("itens")
        or []
    ):
        item = dict(
            item_original
        )

        icms_existente = item.get(
            "icms"
        )

        if isinstance(
            icms_existente,
            dict,
        ):
            icms = dict(
                icms_existente
            )
        else:
            icms = {}

        campos_icms = (
            "grupo_icms",
            "origem",
            "cst",
            "csosn",
            "base_icms",
            "aliquota_icms",
            "valor_icms",
            "base_icms_st",
            "aliquota_icms_st",
            "valor_icms_st",
        )

        for campo in campos_icms:
            if (
                campo not in icms
                and campo in item
            ):
                icms[campo] = item.get(
                    campo
                )

        item["icms"] = icms

        ipi_existente = item.get(
            "ipi"
        )

        if isinstance(
            ipi_existente,
            dict,
        ):
            ipi = dict(
                ipi_existente
            )
        else:
            ipi = {}

        campos_ipi = (
            "cst_ipi",
            "base_ipi",
            "aliquota_ipi",
            "valor_ipi",
        )

        for campo in campos_ipi:
            if (
                campo not in ipi
                and campo in item
            ):
                ipi[campo] = item.get(
                    campo
                )

        item["ipi"] = ipi

        itens_normalizados.append(
            item
        )

    normalizado["itens"] = (
        itens_normalizados
    )

    return normalizado


def _documentos_xml_entrada(
    itens_entrada,
):
    documentos = []
    ids_processados = set()

    for item in itens_entrada or []:
        documento_id = item.get(
            "documento_fiscal_id"
        )

        if documento_id is None:
            raise ValueError(
                "Entrada sem documento "
                "fiscal vinculado."
            )

        if documento_id in ids_processados:
            continue

        xml = (
            item.get("xml_processado")
            or item.get("xml_original")
        )

        if not xml:
            raise ValueError(
                "Documento fiscal "
                f"{documento_id} sem XML canonico."
            )

        documento = ler_xml_sintegra(
            xml
        )

        documentos.append(
            _normalizar_documento_para_sintegra(
                documento
            )
        )

        ids_processados.add(
            documento_id
        )

    return documentos


def _documentos_xml_nfce(
    documentos_nfce,
):
    documentos = []

    for registro in (
        documentos_nfce
        or []
    ):
        xml = (
            registro.get(
                "xml_processado"
            )
            or registro.get(
                "xml_original"
            )
        )

        if not xml:
            identificador = (
                registro.get("id")
                or registro.get("numero")
                or "desconhecido"
            )

            raise ValueError(
                "NFC-e "
                f"{identificador} sem XML "
                "autorizado armazenado."
            )

        documento = ler_xml_sintegra(
            xml
        )

        documento = (
            _normalizar_documento_para_sintegra(
                documento
            )
        )

        if str(
            documento.get(
                "modelo",
                ""
            )
        ).strip() != "65":
            raise ValueError(
                "Documento informado como "
                "NFC-e nao possui modelo 65 "
                "no XML."
            )

        documentos.append(
            documento
        )

    return documentos



def _agrupar_entradas_por_documento(
    itens_entrada,
):
    documentos = {}

    for item in itens_entrada or []:
        documento_id = item.get(
            "documento_fiscal_id"
        )

        if documento_id is None:
            raise ValueError(
                "Item de entrada sem documento "
                "fiscal vinculado."
            )

        documentos.setdefault(
            documento_id,
            [],
        ).append(item)

    return documentos


def _gerar_registros_entrada(
    itens_entrada,
):
    registros_50 = []
    registros_54 = []

    documentos = (
        _agrupar_entradas_por_documento(
            itens_entrada
        )
    )

    for documento_id, itens_banco in (
        documentos.items()
    ):
        primeiro = itens_banco[0]

        xml = (
            primeiro.get("xml_processado")
            or primeiro.get("xml_original")
        )

        if not xml:
            raise ValueError(
                "Documento fiscal "
                f"{documento_id} sem XML canonico."
            )

        dados_xml = ler_xml_sintegra(
            xml
        )

        itens_preparados = (
            preparar_itens_registro_50(
                dados_xml.get(
                    "itens",
                    [],
                ),
                itens_banco,
            )
        )

        emitente = (
            dados_xml.get("emitente")
            or {}
        )

        totais = (
            dados_xml.get("totais")
            or {}
        )

        cnpj_emitente = (
            emitente.get("cnpj")
            or primeiro.get("emitente_cnpj")
        )

        ie_emitente = (
            emitente.get(
                "inscricao_estadual"
            )
            or ""
        )

        uf_emitente = (
            emitente.get("uf")
            or primeiro.get("emitente_uf")
            or ""
        )

        modelo = (
            dados_xml.get("modelo")
            or primeiro.get("modelo")
        )

        serie = (
            dados_xml.get("serie")
            or primeiro.get("serie")
        )

        numero = (
            dados_xml.get("numero")
            or primeiro.get("numero")
        )

        data_documento = (
            dados_xml.get("data_emissao")
            or primeiro.get("data_emissao")
        )

        valor_documento = totais.get(
            "valor_nota",
            primeiro.get(
                "valor_total",
                0,
            ),
        )

        registros_50.extend(
            gerar_registros_50_agrupados(
                itens=itens_preparados,
                cnpj=cnpj_emitente,
                inscricao_estadual=(
                    ie_emitente
                ),
                data_documento=(
                    data_documento
                ),
                uf=uf_emitente,
                modelo=modelo,
                serie=serie,
                numero=numero,
                emitente=True,
                valor_contabil_documento=(
                    valor_documento
                ),
                situacao="N",
            )
        )

        for item in itens_preparados:
            registros_54.append(
                gerar_registro_54(
                    cnpj=cnpj_emitente,
                    modelo=modelo,
                    serie=serie,
                    numero=numero,
                    cfop=item.get(
                        "cfop_entrada"
                    ),
                    cst=(
                        item.get("cst")
                        or item.get("csosn")
                    ),
                    numero_item=item.get(
                        "numero_item"
                    ),
                    codigo_produto=(
                        item.get(
                            "codigo_produto"
                        )
                        or ""
                    ),
                    quantidade=item.get(
                        "quantidade",
                        0,
                    ),
                    valor_produto=item.get(
                        "valor_produto",
                        0,
                    ),
                    valor_desconto=item.get(
                        "valor_desconto",
                        0,
                    ),
                    base_icms=item.get(
                        "base_icms",
                        0,
                    ),
                    base_icms_st=item.get(
                        "base_icms_st",
                        0,
                    ),
                    valor_ipi=item.get(
                        "valor_ipi",
                        0,
                    ),
                    aliquota_icms=item.get(
                        "aliquota_icms",
                        0,
                    ),
                    permitir_codigo_vazio=False,
                )
            )

        if itens_preparados:
            primeiro_item = (
                itens_preparados[0]
            )

            registros_54.extend(
                gerar_registros_54_despesas_acessorias(
                    cnpj=cnpj_emitente,
                    modelo=modelo,
                    serie=serie,
                    numero=numero,
                    cfop=primeiro_item.get(
                        "cfop_entrada"
                    ),
                    cst=(
                        primeiro_item.get("cst")
                        or primeiro_item.get(
                            "csosn"
                        )
                    ),
                    valor_frete=totais.get(
                        "valor_frete",
                        0,
                    ),
                    valor_seguro=totais.get(
                        "valor_seguro",
                        0,
                    ),
                    valor_outras_despesas=(
                        totais.get(
                            "valor_outras_despesas",
                            0,
                        )
                    ),
                )
            )

    return (
        registros_50,
        registros_54,
    )


def _montar_sintegra_competencia(
    *,
    ano,
    mes,
    data_inicial,
    data_final,
    itens_entrada,
    documentos_nfce,
    contato,
    telefone,
):
    configuracao = (
        buscar_configuracao_fiscal()
    )

    if not configuracao:
        raise ValueError(
            "Configuracao fiscal ativa "
            "nao encontrada."
        )

    cnpj = configuracao.get(
        "cnpj"
    )

    inscricao_estadual = (
        configuracao.get(
            "inscricao_estadual"
        )
    )

    registro_10 = gerar_registro_10(
        cnpj=cnpj,
        inscricao_estadual=(
            inscricao_estadual
        ),
        razao_social=configuracao.get(
            "razao_social"
        ),
        municipio=configuracao.get(
            "cidade"
        ),
        uf=configuracao.get("uf"),
        data_inicial=data_inicial,
        data_final=data_final,
        fax="",
        codigo_estrutura="3",
        natureza_operacoes="3",
        finalidade="1",
    )

    registro_11 = gerar_registro_11(
        logradouro=configuracao.get(
            "logradouro"
        ),
        numero=configuracao.get(
            "numero"
        ),
        complemento=configuracao.get(
            "complemento"
        ),
        bairro=configuracao.get(
            "bairro"
        ),
        cep=configuracao.get(
            "cep"
        ),
        contato=contato,
        telefone=telefone,
    )

    (
        registros_50,
        registros_54,
    ) = _gerar_registros_entrada(
        itens_entrada
    )

    documentos_entrada_xml = (
        _documentos_xml_entrada(
            itens_entrada
        )
    )

    documentos_nfce_xml = (
        _documentos_xml_nfce(
            documentos_nfce
        )
    )

    saidas = gerar_registros_61_61r(
        documentos_nfce_xml,
        mes=mes,
        ano=ano,
    )

    registros_61 = saidas.get(
        "registro_61",
        [],
    )

    registros_61r = saidas.get(
        "registro_61r",
        [],
    )

    documentos_registro_75 = (
        documentos_entrada_xml
        + documentos_nfce_xml
    )

    registros_75 = gerar_registros_75(
        documentos_registro_75,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    montagem = montar_arquivo_sintegra(
        registro_10=registro_10,
        registro_11=registro_11,
        registros_50=registros_50,
        registros_54=registros_54,
        registros_61=registros_61,
        registros_61r=registros_61r,
        registros_75=registros_75,
        cnpj=cnpj,
        inscricao_estadual=(
            inscricao_estadual
        ),
    )

    conteudo = serializar_arquivo_sintegra(
        montagem
    )

    return {
        "montagem": montagem,
        "conteudo": conteudo,
        "registros_50": registros_50,
        "registros_54": registros_54,
        "registros_61": registros_61,
        "registros_61r": registros_61r,
        "registros_75": registros_75,
    }

def tela_sintegra():
    st.title("SINTEGRA")

    st.caption(
        "Geracao e conferencia mensal do arquivo SINTEGRA."
    )

    hoje = date.today()

    col_mes, col_ano = st.columns(2)

    with col_mes:
        mes = st.selectbox(
            "Mes da competencia",
            options=list(MESES.keys()),
            format_func=lambda valor: (
                f"{valor:02d} - {MESES[valor]}"
            ),
            index=hoje.month - 1,
            key="sintegra_mes",
        )

    with col_ano:
        anos = list(
            range(
                hoje.year - 10,
                hoje.year + 2,
            )
        )

        ano = st.selectbox(
            "Ano da competencia",
            options=anos,
            index=anos.index(
                hoje.year
            ),
            key="sintegra_ano",
        )

    data_inicial, data_final = (
        _periodo_competencia(
            ano,
            mes,
        )
    )

    encerrada = _competencia_encerrada(
        ano,
        mes,
    )

    st.info(
        "Competencia selecionada: "
        f"{data_inicial.strftime('%d/%m/%Y')} "
        "a "
        f"{data_final.strftime('%d/%m/%Y')}"
    )

    if encerrada:
        st.success(
            "Competencia encerrada. "
            "Pode ser preparada para geracao "
            "do arquivo mensal definitivo."
        )
    else:
        st.warning(
            "Competencia ainda nao encerrada. "
            "A conferencia pode ser realizada, "
            "mas o arquivo mensal definitivo "
            "nao sera liberado antes do fechamento."
        )

    st.divider()

    if st.button(
        "Validar competencia",
        type="primary",
        key="sintegra_validar",
    ):
        try:
            with st.spinner(
                "Consultando dados fiscais..."
            ):
                itens_entrada = (
                    listar_itens_entrada_competencia(
                        data_inicial,
                        data_final,
                    )
                )

                pendencias = (
                    listar_pendencias_data_entrada(
                        data_inicial,
                        data_final,
                    )
                )

                documentos_nfce = (
                    listar_nfce_saida_competencia(
                        data_inicial,
                        data_final,
                    )
                )

                resultado_validacao = (
                    validar_competencia_entrada(
                        itens_entrada,
                        pendencias,
                    )
                )

            st.session_state[
                "sintegra_resultado"
            ] = {
                "ano": ano,
                "mes": mes,
                "data_inicial": data_inicial,
                "data_final": data_final,
                "encerrada": encerrada,
                "itens_entrada": itens_entrada,
                "pendencias": pendencias,
                "documentos_nfce": documentos_nfce,
                "validacao": resultado_validacao,
            }

        except Exception as erro:
            st.session_state.pop(
                "sintegra_resultado",
                None,
            )

            st.error(
                "Nao foi possivel validar "
                f"a competencia: {erro}"
            )

    resultado = st.session_state.get(
        "sintegra_resultado"
    )

    if not resultado:
        return

    if (
        resultado.get("ano") != ano
        or resultado.get("mes") != mes
    ):
        st.info(
            "Mes ou ano alterado. "
            "Clique em Validar competencia "
            "para atualizar a conferencia."
        )
        return

    itens_entrada = resultado[
        "itens_entrada"
    ]

    pendencias = resultado[
        "pendencias"
    ]

    documentos_nfce = resultado[
        "documentos_nfce"
    ]

    validacao = resultado[
        "validacao"
    ]

    st.subheader(
        "Resumo da competencia"
    )

    coluna_1, coluna_2, coluna_3, coluna_4 = (
        st.columns(4)
    )

    coluna_1.metric(
        "NF-e de entrada",
        _documentos_entrada(
            itens_entrada
        ),
    )

    coluna_2.metric(
        "Itens de entrada",
        len(itens_entrada or []),
    )

    coluna_3.metric(
        "NFC-e autorizadas",
        _documentos_nfce(
            documentos_nfce
        ),
    )

    coluna_4.metric(
        "Pendencias de entrada",
        len(pendencias or []),
    )

    st.divider()

    inconsistencias = []

    if isinstance(
        validacao,
        dict,
    ):
        inconsistencias = (
            validacao.get(
                "inconsistencias",
                [],
            )
            or validacao.get(
                "erros",
                [],
            )
            or []
        )

    elif isinstance(
        validacao,
        (list, tuple),
    ):
        inconsistencias = list(
            validacao
        )

    elif validacao is False:
        inconsistencias = [
            "A validacao da competencia "
            "nao foi aprovada."
        ]

    if inconsistencias:
        st.error(
            "Foram encontradas inconsistencias "
            "que impedem a geracao definitiva."
        )

        for inconsistencia in inconsistencias:
            st.write(
                f"- {inconsistencia}"
            )

    elif pendencias:
        st.error(
            "Existem documentos de entrada "
            "sem data de entrada definida."
        )

    else:
        st.success(
            "Conferencia estrutural concluida "
            "sem bloqueios identificados."
        )

    st.divider()

    st.subheader(
        "Geracao do arquivo"
    )

    if not resultado["encerrada"]:
        st.warning(
            "O TXT definitivo permanece bloqueado "
            "porque a competencia ainda esta aberta."
        )

    elif inconsistencias or pendencias:
        st.warning(
            "O TXT definitivo permanece bloqueado "
            "ate a correcao das inconsistencias."
        )

    else:
        st.success(
            "Competencia apta para geracao "
            "do arquivo SINTEGRA."
        )

        coluna_contato, coluna_telefone = (
            st.columns(2)
        )

        with coluna_contato:
            contato = st.text_input(
                "Contato do estabelecimento",
                value=(
                    "ELCIO AUGUSTO "
                    "MOREIRA JUNIOR"
                ),
                key="sintegra_contato",
            )

        with coluna_telefone:
            telefone = st.text_input(
                "Telefone",
                value="35998697369",
                key="sintegra_telefone",
            )

        try:
            resultado_arquivo = (
                _montar_sintegra_competencia(
                    ano=ano,
                    mes=mes,
                    data_inicial=data_inicial,
                    data_final=data_final,
                    itens_entrada=(
                        itens_entrada
                    ),
                    documentos_nfce=(
                        documentos_nfce
                    ),
                    contato=contato,
                    telefone=telefone,
                )
            )

            montagem = resultado_arquivo[
                "montagem"
            ]

            st.subheader(
                "Registros preparados"
            )

            resumo = montagem.get(
                "contagem",
                {},
            )

            if resumo:
                st.json(resumo)

            conteudo = resultado_arquivo[
                "conteudo"
            ]

            if isinstance(
                conteudo,
                str,
            ):
                arquivo_download = (
                    conteudo.encode(
                        "latin-1"
                    )
                )
            else:
                arquivo_download = conteudo

            nome_arquivo = (
                f"SINT_{mes:02d}{ano}.txt"
            )

            st.download_button(
                "Baixar arquivo SINTEGRA",
                data=arquivo_download,
                file_name=nome_arquivo,
                mime="text/plain",
                key="sintegra_download",
            )

            st.caption(
                "O download nao transmite "
                "o arquivo para a SEFAZ. "
                "Valide o TXT no Validador "
                "SINTEGRA antes do envio."
            )

        except Exception as erro:
            st.error(
                "Nao foi possivel montar "
                f"o arquivo SINTEGRA: {erro}"
            )
