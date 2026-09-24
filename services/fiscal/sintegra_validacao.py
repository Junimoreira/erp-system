def _somente_digitos(valor):
    return "".join(
        caractere
        for caractere in str(
            valor or ""
        )
        if caractere.isdigit()
    )


def validar_itens_entrada(
    itens
):
    inconsistencias = []

    for linha in itens or []:
        compra_id = linha.get(
            "compra_id"
        )

        item_compra_id = linha.get(
            "item_compra_id"
        )

        prefixo = (
            f"Compra {compra_id}, "
            f"item {item_compra_id}"
        )

        chave_nfe = _somente_digitos(
            linha.get(
                "chave_nfe"
            )
        )

        if len(chave_nfe) != 44:
            inconsistencias.append(
                f"{prefixo}: chave da NF-e "
                "ausente ou invalida."
            )

        if linha.get(
            "documento_fiscal_id"
        ) is None:
            inconsistencias.append(
                f"{prefixo}: documento fiscal "
                "nao localizado pela chave."
            )
            continue

        tipo_movimento = str(
            linha.get(
                "tipo_movimento"
            ) or ""
        ).strip().upper()

        if tipo_movimento != "ENTRADA":
            inconsistencias.append(
                f"{prefixo}: documento fiscal "
                "nao esta classificado como ENTRADA."
            )

        try:
            modelo = int(
                linha.get(
                    "modelo"
                )
            )
        except (TypeError, ValueError):
            modelo = None

        if modelo != 55:
            inconsistencias.append(
                f"{prefixo}: modelo fiscal "
                "de entrada deve ser 55."
            )

        numero_item_xml = linha.get(
            "numero_item_xml"
        )

        try:
            numero_item_xml = int(
                numero_item_xml
            )
        except (TypeError, ValueError):
            numero_item_xml = None

        if (
            numero_item_xml is None
            or numero_item_xml <= 0
        ):
            inconsistencias.append(
                f"{prefixo}: numero_item_xml "
                "ausente ou invalido."
            )

        cfop_entrada = _somente_digitos(
            linha.get(
                "cfop_entrada"
            )
        )

        if len(cfop_entrada) != 4:
            inconsistencias.append(
                f"{prefixo}: cfop_entrada "
                "ausente ou invalido."
            )

        # ==================================================
        # CLASSIFICACAO DO REGISTRO 50
        #
        # A competencia nao pode ser liberada enquanto
        # existir item sem classificacao fiscal final.
        # ==================================================

        classificacao_registro_50 = str(
            linha.get(
                "classificacao_registro_50"
            )
            or ""
        ).strip().upper()

        classificacoes_validas_registro_50 = {
            "TRIBUTADA",
            "ISENTA_NAO_TRIBUTADA",
            "OUTRAS",
        }

        if (
            classificacao_registro_50
            not in classificacoes_validas_registro_50
        ):
            inconsistencias.append(
                f"{prefixo}: classificacao do "
                "Registro 50 ausente, pendente "
                "ou invalida."
            )

        documento_item_id = linha.get(
            "documento_fiscal_item_id"
        )

        numero_item_fiscal = linha.get(
            "numero_item_fiscal"
        )

        if documento_item_id is None:
            inconsistencias.append(
                f"{prefixo}: item fiscal nao "
                "localizado pelo numero_item_xml."
            )
        elif (
            numero_item_xml is not None
            and numero_item_fiscal is not None
        ):
            try:
                numero_item_fiscal = int(
                    numero_item_fiscal
                )
            except (TypeError, ValueError):
                numero_item_fiscal = None

            if (
                numero_item_fiscal
                != numero_item_xml
            ):
                inconsistencias.append(
                    f"{prefixo}: numero_item_xml "
                    "diverge do item fiscal."
                )

        xml_canonico = (
            linha.get(
                "xml_processado"
            )
            or linha.get(
                "xml_original"
            )
        )

        if not xml_canonico:
            inconsistencias.append(
                f"{prefixo}: XML fiscal canonico "
                "nao esta armazenado."
            )

    return inconsistencias


def validar_pendencias_data_entrada(
    pendencias
):
    inconsistencias = []

    compras_processadas = set()

    for linha in pendencias or []:
        compra_id = linha.get(
            "compra_id"
        )

        if compra_id in compras_processadas:
            continue

        compras_processadas.add(
            compra_id
        )

        numero = (
            linha.get(
                "numero"
            )
            or linha.get(
                "numero_nfe"
            )
            or ""
        )

        data_emissao = linha.get(
            "data_emissao"
        )

        mensagem = (
            f"Compra {compra_id}"
        )

        if numero:
            mensagem += (
                f", NF-e {numero}"
            )

        mensagem += (
            ": data_entrada ausente."
        )

        if data_emissao:
            mensagem += (
                " Documento localizado pela "
                f"data de emissao {data_emissao}; "
                "a data de emissao nao foi usada "
                "como data de entrada."
            )

        inconsistencias.append(
            mensagem
        )

    return inconsistencias


def validar_competencia_entrada(
    itens,
    pendencias_data_entrada=None
):
    inconsistencias = []

    inconsistencias.extend(
        validar_itens_entrada(
            itens
        )
    )

    inconsistencias.extend(
        validar_pendencias_data_entrada(
            pendencias_data_entrada
        )
    )

    return {
        "valido":
            len(inconsistencias) == 0,

        "quantidade_itens":
            len(itens or []),

        "quantidade_inconsistencias":
            len(inconsistencias),

        "inconsistencias":
            inconsistencias,
    }
