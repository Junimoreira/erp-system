from database.vendas_fiscal_db import (
    montar_venda_para_emissao
)

from database.configuracoes_fiscais_db import (
    buscar_configuracao_fiscal
)

from services.fiscal.validador_venda_fiscal import (
    validar_venda_fiscal
)

from services.fiscal.destinatario_fiscal import (
    montar_destinatario_fiscal
)

from services.fiscal.pagamento_fiscal import (
    montar_pagamento_fiscal
)

from services.fiscal.totais_fiscais import (
    montar_totais_fiscais
)


from services.fiscal.calculo_ibs_cbs import (
    calcular_ibs_cbs
)


# ============================================================
# MONTAR RASCUNHO DE DOCUMENTO FISCAL
#
# IMPORTANTE:
# - NÃO gera XML
# - NÃO assina
# - NÃO transmite para SEFAZ
# - NÃO altera venda
# - NÃO altera produto
# - Apenas consolida dados já validados pelo motor fiscal
# ============================================================
def montar_rascunho_documento_fiscal(
    venda_id,
    modelo,
    uf_destino
):

    # --------------------------------------------------------
    # VALIDAR MODELO
    # --------------------------------------------------------
    if modelo not in (
        55,
        65
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Modelo fiscal inválido. Use 55 ou 65."
        }

    # --------------------------------------------------------
    # CONFIGURAÇÃO DA EMPRESA
    # --------------------------------------------------------
    configuracao = (
        buscar_configuracao_fiscal()
    )

    if not configuracao:

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Configuração fiscal da empresa não encontrada."
        }

    # --------------------------------------------------------
    # CARREGAR VENDA
    # --------------------------------------------------------
    resultado_venda = (
        montar_venda_para_emissao(
            venda_id
        )
    )

    if not resultado_venda.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                resultado_venda.get(
                    "mensagem"
                )
        }

    venda = resultado_venda.get(
        "venda"
    )

    if not venda:

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Venda não carregada corretamente."
        }

    # --------------------------------------------------------
    # DESTINATÁRIO
    # --------------------------------------------------------
    resultado_destinatario = (
        montar_destinatario_fiscal(
            cliente_id=venda.get(
                "cliente_id"
            ),
            modelo=modelo
        )
    )

    if not resultado_destinatario.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Destinatário bloqueado pela validação fiscal.",
            "venda_id":
                venda_id,
            "modelo":
                modelo,
            "destinatario":
                resultado_destinatario
        }

    # --------------------------------------------------------
    # PAGAMENTO
    # --------------------------------------------------------
    resultado_pagamento = (
        montar_pagamento_fiscal(
            forma_pagamento=venda.get(
                "forma_pagamento"
            ),
            valor_pago=venda.get(
                "valor_final"
            ),
            autorizacao_cartao=venda.get(
                "autorizacao_cartao"
            )
        )
    )

    if not resultado_pagamento.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Pagamento bloqueado pela validação fiscal.",
            "venda_id":
                venda_id,
            "modelo":
                modelo,
            "destinatario":
                resultado_destinatario,
            "pagamento":
                resultado_pagamento
        }

    # --------------------------------------------------------
    # TOTAIS
    # --------------------------------------------------------
    resultado_totais = (
        montar_totais_fiscais(
            venda=venda,
            resultado_pagamento=
                resultado_pagamento
        )
    )

    if not resultado_totais.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Totais bloqueados pela validação fiscal.",
            "venda_id":
                venda_id,
            "modelo":
                modelo,
            "destinatario":
                resultado_destinatario,
            "pagamento":
                resultado_pagamento,
            "totais":
                resultado_totais
        }

    # --------------------------------------------------------
    # VALIDAR FISCALMENTE A VENDA
    # --------------------------------------------------------
    validacao = validar_venda_fiscal(
        venda=venda,
        uf_destino=uf_destino,
        modelo=modelo
    )

    if not validacao.get(
        "pode_emitir"
    ):

        return {
            "sucesso": False,
            "pode_gerar_xml": False,
            "mensagem":
                "Venda bloqueada pela validação fiscal.",
            "venda_id":
                venda_id,
            "modelo":
                modelo,
            "destinatario":
                resultado_destinatario,
            "pagamento":
                resultado_pagamento,
            "totais":
                resultado_totais,
            "validacao":
                validacao
        }

    # --------------------------------------------------------
    # DEFINIR SÉRIE E NÚMERO
    # --------------------------------------------------------
    if modelo == 55:

        serie = configuracao.get(
            "serie_nfe"
        )

        proximo_numero = configuracao.get(
            "proximo_numero_nfe"
        )

    else:

        serie = configuracao.get(
            "serie_nfce"
        )

        proximo_numero = configuracao.get(
            "proximo_numero_nfce"
        )

    # --------------------------------------------------------
    # ITENS FISCAIS
    #
    # Nesta etapa ainda NÃO geramos XML.
    # Apenas consolidamos os dados fiscais já validados.
    # --------------------------------------------------------
    itens_fiscais = []

    for item in validacao.get(
        "itens",
        []
    ):

        # --------------------------------------------------------
        # IBS / CBS
        #
        # Em 2026, para CRT 1 (Simples Nacional), o motor mantém
        # o cálculo bloqueado por padrão. Assim, preservamos a
        # classificação fiscal validada sem inventar alíquotas.
        #
        # Quando as alíquotas aplicáveis ao ERP estiverem
        # parametrizadas, elas deverão ser fornecidas aqui pelo
        # motor/configuração fiscal.
        # --------------------------------------------------------
        resultado_ibs_cbs = calcular_ibs_cbs(
            base_calculo=item.get(
                "subtotal"
            ),
            cst=item.get(
                "cst_ibs_cbs"
            ),
            classificacao_tributaria=item.get(
                "classificacao_tributaria"
            ),
            data_referencia=venda.get(
                "data_venda"
            ),
            crt=configuracao.get(
                "crt"
            ),
            aliquota_ibs_uf=None,
            aliquota_ibs_municipal=None,
            aliquota_cbs=None,
            habilitado=True,
            permitir_simples_2026=False
        )

        itens_fiscais.append(
            {
                # ------------------------------------------------
                # IDENTIFICAÇÃO DO ITEM
                # ------------------------------------------------
                "numero_item":
                    item.get(
                        "numero_item"
                    ),

                "produto_id":
                    item.get(
                        "produto_id"
                    ),

                "descricao":
                    item.get(
                        "produto_nome"
                    ),

                "codigo_barras":
                    item.get(
                        "codigo_barras"
                    ),

                # ------------------------------------------------
                # DADOS COMERCIAIS
                # ------------------------------------------------
                "quantidade":
                    item.get(
                        "quantidade"
                    ),

                "preco_unitario":
                    item.get(
                        "preco_unitario"
                    ),

                "subtotal":
                    item.get(
                        "subtotal"
                    ),

                # ------------------------------------------------
                # CLASSIFICAÇÃO FISCAL
                # ------------------------------------------------
                "ncm":
                    item.get(
                        "ncm"
                    ),

                "cest":
                    item.get(
                        "cest"
                    ),

                "origem_mercadoria":
                    item.get(
                        "origem_mercadoria"
                    ),

                # ------------------------------------------------
                # ICMS
                # ------------------------------------------------
                "perfil_icms":
                    item.get(
                        "perfil_icms"
                    ),

                "cfop":
                    item.get(
                        "cfop"
                    ),

                "csosn":
                    item.get(
                        "csosn"
                    ),

                # ------------------------------------------------
                # PIS / COFINS
                # ------------------------------------------------
                "cst_pis":
                    item.get(
                        "cst_pis"
                    ),

                "aliquota_pis":
                    item.get(
                        "aliquota_pis"
                    ),

                "cst_cofins":
                    item.get(
                        "cst_cofins"
                    ),

                "aliquota_cofins":
                    item.get(
                        "aliquota_cofins"
                    ),

                # ------------------------------------------------
                # IBS / CBS
                # ------------------------------------------------
                "cst_ibs_cbs":
                    item.get(
                        "cst_ibs_cbs"
                    ),

                "classificacao_tributaria":
                    item.get(
                        "classificacao_tributaria"
                    ),

                "ibs_cbs_validado":
                    item.get(
                        "ibs_cbs_validado"
                    ),

                "ibs_cbs_vigente":
                    item.get(
                        "ibs_cbs_vigente"
                    ),

                "ibs_cbs_permitido_modelo":
                    item.get(
                        "ibs_cbs_permitido_modelo"
                    ),

                "ibs_cbs_ind_nfe":
                    item.get(
                        "ibs_cbs_ind_nfe"
                    ),

                "ibs_cbs_ind_nfce":
                    item.get(
                        "ibs_cbs_ind_nfce"
                    ),

                "ibs_cbs_descricao":
                    item.get(
                        "ibs_cbs_descricao"
                    ),

                # ------------------------------------------------
                # CÁLCULO IBS / CBS
                # ------------------------------------------------
                "ibs_cbs_calcular":
                    resultado_ibs_cbs.get(
                        "calcular"
                    ),

                "base_calculo_ibs_cbs":
                    resultado_ibs_cbs.get(
                        "base_calculo"
                    ),

                "aliquota_ibs_uf":
                    resultado_ibs_cbs.get(
                        "pIBSUF"
                    ),

                "aliquota_ibs_municipal":
                    resultado_ibs_cbs.get(
                        "pIBSMun"
                    ),

                "aliquota_cbs":
                    resultado_ibs_cbs.get(
                        "pCBS"
                    ),

                "valor_ibs_uf":
                    resultado_ibs_cbs.get(
                        "vIBSUF"
                    ),

                "valor_ibs_municipal":
                    resultado_ibs_cbs.get(
                        "vIBSMun"
                    ),

                "valor_ibs":
                    resultado_ibs_cbs.get(
                        "vIBS"
                    ),

                "valor_cbs":
                    resultado_ibs_cbs.get(
                        "vCBS"
                    ),

                "ibs_cbs_calculo_sucesso":
                    resultado_ibs_cbs.get(
                        "sucesso"
                    ),

                "ibs_cbs_calculo_erros":
                    resultado_ibs_cbs.get(
                        "erros",
                        []
                    ),

                "ibs_cbs_calculo_avisos":
                    resultado_ibs_cbs.get(
                        "avisos",
                        []
                    )
            }
        )

    # --------------------------------------------------------
    # RASCUNHO
    # --------------------------------------------------------
    return {
        "sucesso": True,
        "pode_gerar_xml": True,

        "modelo":
            modelo,

        "serie":
            serie,

        "numero_sugerido":
            proximo_numero,

        "ambiente":
            configuracao.get(
                "ambiente"
            ),

        # ----------------------------------------------------
        # EMITENTE
        # ----------------------------------------------------
        "emitente": {
            "cnpj":
                configuracao.get(
                    "cnpj"
                ),

            "razao_social":
                configuracao.get(
                    "razao_social"
                ),

            "nome_fantasia":
                configuracao.get(
                    "nome_fantasia"
                ),

            "inscricao_estadual":
                configuracao.get(
                    "inscricao_estadual"
                ),

            "crt":
                configuracao.get(
                    "crt"
                ),

            # ------------------------------------------------
            # ENDEREÇO DO EMITENTE
            # ------------------------------------------------
            "logradouro":
                configuracao.get(
                    "logradouro"
                ),

            "numero":
                configuracao.get(
                    "numero"
                ),

            "complemento":
                configuracao.get(
                    "complemento"
                ),

            "bairro":
                configuracao.get(
                    "bairro"
                ),

            "cidade":
                configuracao.get(
                    "cidade"
                ),

            "codigo_municipio_ibge":
                configuracao.get(
                    "codigo_municipio_ibge"
                ),

            "uf":
                configuracao.get(
                    "uf"
                ),

            "cep":
                configuracao.get(
                    "cep"
                ),

            "codigo_pais":
                configuracao.get(
                    "codigo_pais"
                ),

            "pais":
                configuracao.get(
                    "pais"
                )
        },

        # ----------------------------------------------------
        # DESTINATÁRIO
        # ----------------------------------------------------
        "destinatario": {
            "identificado":
                resultado_destinatario.get(
                    "identificado"
                ),

            "tipo":
                resultado_destinatario.get(
                    "tipo"
                ),

            "dados":
                resultado_destinatario.get(
                    "destinatario"
                ),

            "avisos":
                resultado_destinatario.get(
                    "avisos",
                    []
                )
        },

        # ----------------------------------------------------
        # PAGAMENTO
        # ----------------------------------------------------
        "pagamento": {
            "dados":
                resultado_pagamento.get(
                    "pagamento"
                ),

            "avisos":
                resultado_pagamento.get(
                    "avisos",
                    []
                )
        },

        # ----------------------------------------------------
        # TOTAIS
        # ----------------------------------------------------
        "totais": {
            "dados":
                resultado_totais.get(
                    "totais"
                ),

            "avisos":
                resultado_totais.get(
                    "avisos",
                    []
                )
        },

        # ----------------------------------------------------
        # VENDA
        # ----------------------------------------------------
        "venda": {
            "id":
                venda.get(
                    "id"
                ),

            "cliente_id":
                venda.get(
                    "cliente_id"
                ),

            "data_venda":
                venda.get(
                    "data_venda"
                ),

            "valor_total":
                venda.get(
                    "valor_total"
                ),

            "desconto":
                venda.get(
                    "desconto"
                ),

            "valor_final":
                venda.get(
                    "valor_final"
                ),

            "forma_pagamento":
                venda.get(
                    "forma_pagamento"
                )
        },

        "uf_destino":
            uf_destino,

        "itens":
            itens_fiscais,

        "validacao":
            validacao
    }