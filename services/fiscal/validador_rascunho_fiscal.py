# ============================================================
# VALIDADOR FINAL DO RASCUNHO FISCAL
#
# RESPONSABILIDADE:
# - Validar o rascunho já montado
# - Centralizar os bloqueios antes da futura geração do XML
#
# IMPORTANTE:
# - NÃO gera XML
# - NÃO assina
# - NÃO transmite
# - NÃO altera banco
# ============================================================


def validar_rascunho_fiscal(
    rascunho
):

    erros = []
    avisos = []

    if not isinstance(
        rascunho,
        dict
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "pronto_para_transmitir": False,
            "erros": [
                "Rascunho fiscal inválido."
            ],
            "avisos": []
        }

    # --------------------------------------------------------
    # MODELO
    # --------------------------------------------------------
    modelo = rascunho.get(
        "modelo"
    )

    if modelo not in (
        55,
        65
    ):

        erros.append(
            "Modelo fiscal inválido."
        )

    # --------------------------------------------------------
    # SÉRIE / NÚMERO
    # --------------------------------------------------------
    serie = rascunho.get(
        "serie"
    )

    numero = rascunho.get(
        "numero_sugerido"
    )

    if serie is None:

        erros.append(
            "Série fiscal não informada."
        )

    if numero is None:

        erros.append(
            "Número fiscal não informado."
        )

    # --------------------------------------------------------
    # AMBIENTE
    # --------------------------------------------------------
    ambiente = rascunho.get(
        "ambiente"
    )

    if ambiente not in (
        1,
        2
    ):

        erros.append(
            "Ambiente fiscal inválido."
        )

    # --------------------------------------------------------
    # EMITENTE
    # --------------------------------------------------------
    emitente = rascunho.get(
        "emitente"
    )

    if not isinstance(
        emitente,
        dict
    ):

        erros.append(
            "Emitente não informado."
        )

    else:

        campos_emitente = [
            "cnpj",
            "razao_social",
            "inscricao_estadual",
            "crt",
            "uf",
            "codigo_municipio_ibge"
        ]

        for campo in campos_emitente:

            if not emitente.get(
                campo
            ):

                erros.append(
                    (
                        "Emitente sem campo obrigatório: "
                        f"{campo}."
                    )
                )

    # --------------------------------------------------------
    # DESTINATÁRIO
    # --------------------------------------------------------
    destinatario = rascunho.get(
        "destinatario"
    )

    if not isinstance(
        destinatario,
        dict
    ):

        erros.append(
            "Bloco de destinatário não informado."
        )

    else:

        identificado = destinatario.get(
            "identificado"
        )

        if identificado:

            dados = destinatario.get(
                "dados"
            )

            if not isinstance(
                dados,
                dict
            ):

                erros.append(
                    (
                        "Destinatário identificado sem "
                        "dados cadastrais."
                    )
                )

    # --------------------------------------------------------
    # ITENS
    # --------------------------------------------------------
    itens = rascunho.get(
        "itens",
        []
    )

    if not itens:

        erros.append(
            "Documento fiscal sem itens."
        )

    else:

        for item in itens:

            numero_item = item.get(
                "numero_item"
            )

            if not item.get(
                "produto_id"
            ):

                erros.append(
                    (
                        f"Item {numero_item}: "
                        "produto não informado."
                    )
                )

            if not item.get(
                "descricao"
            ):

                erros.append(
                    (
                        f"Item {numero_item}: "
                        "descrição não informada."
                    )
                )

            if not item.get(
                "ncm"
            ):

                erros.append(
                    (
                        f"Item {numero_item}: "
                        "NCM não informado."
                    )
                )

            if not item.get(
                "cfop"
            ):

                erros.append(
                    (
                        f"Item {numero_item}: "
                        "CFOP não informado."
                    )
                )

            if not item.get(
                "csosn"
            ):

                erros.append(
                    (
                        f"Item {numero_item}: "
                        "CSOSN não informado."
                    )
                )

            quantidade = item.get(
                "quantidade"
            )

            if (
                quantidade is None
                or
                quantidade <= 0
            ):

                erros.append(
                    (
                        f"Item {numero_item}: "
                        "quantidade inválida."
                    )
                )

    # --------------------------------------------------------
    # PAGAMENTO
    # --------------------------------------------------------
    pagamento = rascunho.get(
        "pagamento"
    )

    if not isinstance(
        pagamento,
        dict
    ):

        erros.append(
            "Bloco de pagamento não informado."
        )

    else:

        dados_pagamento = pagamento.get(
            "dados"
        )

        if not isinstance(
            dados_pagamento,
            dict
        ):

            erros.append(
                "Dados de pagamento não informados."
            )

        else:

            if not dados_pagamento.get(
                "tPag"
            ):

                erros.append(
                    "Código tPag não informado."
                )

            if dados_pagamento.get(
                "valor"
            ) is None:

                erros.append(
                    "Valor do pagamento não informado."
                )

        for aviso in pagamento.get(
            "avisos",
            []
        ):

            avisos.append(
                aviso
            )

    # --------------------------------------------------------
    # TOTAIS
    # --------------------------------------------------------
    totais = rascunho.get(
        "totais"
    )

    if not isinstance(
        totais,
        dict
    ):

        erros.append(
            "Bloco de totais não informado."
        )

    else:

        dados_totais = totais.get(
            "dados"
        )

        if not isinstance(
            dados_totais,
            dict
        ):

            erros.append(
                "Dados dos totais não informados."
            )

        else:

            diferenca = dados_totais.get(
                "diferenca_pagamento"
            )

            if diferenca is None:

                erros.append(
                    (
                        "Diferença de pagamento "
                        "não calculada."
                    )
                )

            elif diferenca != 0:

                erros.append(
                    (
                        "Totais apresentam divergência "
                        "entre pagamento e valor final."
                    )
                )

    # --------------------------------------------------------
    # AVISOS DA VALIDAÇÃO DOS ITENS
    # --------------------------------------------------------
    validacao = rascunho.get(
        "validacao"
    )

    if isinstance(
        validacao,
        dict
    ):

        for item in validacao.get(
            "itens",
            []
        ):

            for aviso in item.get(
                "avisos",
                []
            ):

                if aviso not in avisos:

                    avisos.append(
                        aviso
                    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------
    pode_gerar_xml = (
        len(
            erros
        ) == 0
    )

    # Por enquanto, ainda NÃO consideramos pronto para
    # transmissão se existirem avisos fiscais pendentes.
    pronto_para_transmitir = (
        pode_gerar_xml
        and
        len(
            avisos
        ) == 0
    )

    return {
        "sucesso":
            pode_gerar_xml,

        "pode_gerar_xml":
            pode_gerar_xml,

        "pronto_para_transmitir":
            pronto_para_transmitir,

        "erros":
            erros,

        "avisos":
            avisos
    }