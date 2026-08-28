import re
from pathlib import Path

from services.fiscal.rascunho_documento_fiscal import (
    montar_rascunho_documento_fiscal
)

from services.fiscal.gerador_xml_nfe import (
    gerar_xml_nfe
)

from services.fiscal.assinador_xml_nfe import (
    assinar_xml_nfe
)

from services.fiscal.envi_nfe import (
    gerar_envi_nfe
)

from services.fiscal.sefaz_autorizacao_nfe import (
    autorizar_nfe_homologacao_mg,
    consultar_recibo_autorizacao_mg,
)

from services.fiscal.nfe_processada import (
    montar_nfe_processada
)

from database.documentos_fiscais_db import (
    finalizar_documento_fiscal_autorizado,
    buscar_documento_autorizado_por_venda
)

from services.fiscal.validador_xsd_nfe import (
    validar_arquivo_nfe_xsd
)


# ============================================================
# SCHEMAS XSD
# ============================================================
XSD_NFE = Path(
    "schemas/nfe/oficial/PL_010e_v1.02/nfe_v4.00.xsd"
)

XSD_ENVI_NFE = Path(
    "schemas/nfe/oficial/PL_010e_v1.02/"
    "enviNFe_v4.00_local.xsd"
)

XSD_NFE_PROC = Path(
    "schemas/nfe/oficial/PL_010e_v1.02/"
    "procNFe_v4.00.xsd"
)


# ============================================================
# NORMALIZAR CAMINHO
# ============================================================
def _normalizar_caminho(
    caminho
):

    if isinstance(
        caminho,
        Path
    ):
        return caminho

    return Path(
        caminho
    )


# ============================================================
# EXTRAIR XML DE RESULTADO
# ============================================================
def _extrair_xml_resultado(
    resultado
):

    if not isinstance(
        resultado,
        dict
    ):
        return None

    return (
        resultado.get(
            "xml"
        )
        or
        resultado.get(
            "xml_assinado"
        )
        or
        resultado.get(
            "xml_envi_nfe"
        )
        or
        resultado.get(
            "xml_processado"
        )
    )


# ============================================================
# SALVAR XML
# ============================================================
def _salvar_xml(
    caminho,
    conteudo
):

    caminho = _normalizar_caminho(
        caminho
    )

    caminho.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if isinstance(
        conteudo,
        bytes
    ):

        caminho.write_bytes(
            conteudo
        )

    else:

        caminho.write_text(
            str(
                conteudo
            ),
            encoding="utf-8"
        )

    return caminho


# ============================================================
# VALIDAR XML COM XSD OBRIGATÃ“RIO
# ============================================================
def _validar_xsd_obrigatorio(
    caminho_xml,
    caminho_xsd,
    etapa
):

    resultado = validar_arquivo_nfe_xsd(
        caminho_xml=Path(
            caminho_xml
        ),
        caminho_xsd=Path(
            caminho_xsd
        )
    )

    if not resultado.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": etapa,
            "mensagem": (
                "Falha ao executar validaÃ§Ã£o XSD."
            ),
            "validacao":
                resultado
        }

    if not resultado.get(
        "valido"
    ):

        return {
            "sucesso": False,
            "etapa": etapa,
            "mensagem": (
                "XML nÃ£o atende ao XSD."
            ),
            "validacao":
                resultado
        }

    return {
        "sucesso": True,
        "etapa": etapa,
        "validacao":
            resultado
    }


# ============================================================
# VALIDAR XML ESTRUTURAL ANTES DA ASSINATURA
#
# Antes da assinatura, o XML pode falhar no XSD somente
# pela ausÃªncia esperada de Signature.
# ============================================================
def _validar_xml_estrutural(
    caminho_xml
):

    resultado = validar_arquivo_nfe_xsd(
        caminho_xml=Path(
            caminho_xml
        ),
        caminho_xsd=XSD_NFE
    )

    if not resultado.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "XSD_ESTRUTURAL",
            "mensagem": (
                "Falha ao executar validaÃ§Ã£o XSD "
                "do XML estrutural."
            ),
            "validacao":
                resultado
        }

    if not resultado.get(
        "xml_bem_formado"
    ):

        return {
            "sucesso": False,
            "etapa": "XSD_ESTRUTURAL",
            "mensagem": (
                "XML estrutural nÃ£o estÃ¡ bem formado."
            ),
            "validacao":
                resultado
        }

    if resultado.get(
        "valido"
    ):

        return {
            "sucesso": True,
            "etapa": "XSD_ESTRUTURAL",
            "validacao":
                resultado
        }

    erros = resultado.get(
        "erros",
        []
    )

    if not erros:

        return {
            "sucesso": False,
            "etapa": "XSD_ESTRUTURAL",
            "mensagem": (
                "XML estrutural foi marcado como invÃ¡lido "
                "sem detalhamento de erro."
            ),
            "validacao":
                resultado
        }

    for erro in erros:

        mensagem = str(
            erro.get(
                "mensagem",
                ""
            )
        )

        erro_esperado = (
            "Missing child element"
            in
            mensagem
            and
            "Signature"
            in
            mensagem
        )

        if not erro_esperado:

            return {
                "sucesso": False,
                "etapa": "XSD_ESTRUTURAL",
                "mensagem": (
                    "XML estrutural possui erro XSD "
                    "diferente da ausÃªncia esperada "
                    "da assinatura."
                ),
                "validacao":
                    resultado
            }

    return {
        "sucesso": True,
        "etapa": "XSD_ESTRUTURAL",
        "validacao":
            resultado
    }


# ============================================================
# EXTRAIR cStat DOS PROTOCOLOS
# ============================================================
def _extrair_cstats_protocolos(
    retorno
):

    if not isinstance(
        retorno,
        dict
    ):
        return []

    cstats = []

    for protocolo in retorno.get(
        "protocolos",
        []
    ) or []:

        cstat = str(
            protocolo.get(
                "cStat",
                ""
            )
        ).strip()

        if cstat:
            cstats.append(
                cstat
            )

    return cstats


# ============================================================
# EXTRAIR RECIBO DO RETORNO / xMotivo
#
# Alguns retornos de duplicidade podem trazer o nRec
# somente dentro de xMotivo, por exemplo:
# "Duplicidade de NF-e [nRec: 310000000000000]"
# ============================================================
def _extrair_numero_recibo_retorno(
    retorno
):

    if not isinstance(
        retorno,
        dict
    ):
        return None

    numero_recibo = retorno.get(
        "nRec"
    )

    if numero_recibo:

        numero = "".join(
            caractere
            for caractere in str(
                numero_recibo
            )
            if caractere.isdigit()
        )

        if numero:
            return numero

    textos = [
        retorno.get(
            "xMotivo_lote"
        )
    ]

    for protocolo in retorno.get(
        "protocolos",
        []
    ) or []:

        textos.append(
            protocolo.get(
                "xMotivo"
            )
        )

    for texto in textos:

        if not texto:
            continue

        correspondencia = re.search(
            r"\bnRec\s*:\s*(\d+)\b",
            str(
                texto
            ),
            flags=re.IGNORECASE
        )

        if correspondencia:

            return correspondencia.group(
                1
            )

    return None


# ============================================================
# RECUPERAR AUTORIZAÃ‡ÃƒO POR RECIBO
#
# Usado quando a autorizaÃ§Ã£o direta retorna duplicidade
# (especialmente cStat 204/539) e hÃ¡ um nRec recuperÃ¡vel.
#
# IMPORTANTE:
# - nÃ£o retransmite a NF-e
# - somente consulta NFeRetAutorizacao4
# ============================================================
def _recuperar_autorizacao_por_recibo(
    retorno_original,
    caminho_certificado,
    senha_certificado,
    timeout
):

    cstats = (
        _extrair_cstats_protocolos(
            retorno_original
        )
    )

    if not any(
        cstat in (
            "204",
            "539"
        )
        for cstat in cstats
    ):

        return {
            "tentou": False,
            "recuperado": False,
            "numero_recibo": None,
            "resultado_consulta": None,
            "mensagem": (
                "Retorno nÃ£o exige recuperaÃ§Ã£o "
                "automÃ¡tica por recibo."
            )
        }

    numero_recibo = (
        _extrair_numero_recibo_retorno(
            retorno_original
        )
    )

    if not numero_recibo:

        return {
            "tentou": False,
            "recuperado": False,
            "numero_recibo": None,
            "resultado_consulta": None,
            "mensagem": (
                "Duplicidade identificada, mas nenhum "
                "nRec foi encontrado. NÃƒO retransmitir "
                "automaticamente a NF-e."
            )
        }

    resultado_consulta = (
        consultar_recibo_autorizacao_mg(
            numero_recibo=
                numero_recibo,
            caminho_certificado=
                caminho_certificado,
            senha=
                senha_certificado,
            ambiente=
                2,
            timeout=
                timeout
        )
    )

    if not resultado_consulta.get(
        "sucesso_http"
    ):

        return {
            "tentou": True,
            "recuperado": False,
            "numero_recibo":
                numero_recibo,
            "resultado_consulta":
                resultado_consulta,
            "mensagem": (
                "NÃ£o foi possÃ­vel consultar o recibo. "
                "NÃƒO retransmitir a NF-e."
            )
        }

    retorno_consulta = (
        resultado_consulta.get(
            "retorno"
        )
        or
        {}
    )

    if not retorno_consulta.get(
        "autorizado"
    ):

        return {
            "tentou": True,
            "recuperado": False,
            "numero_recibo":
                numero_recibo,
            "resultado_consulta":
                resultado_consulta,
            "mensagem": (
                "Recibo consultado, mas nÃ£o foi recuperada "
                "uma autorizaÃ§Ã£o cStat 100/150. "
                "NÃƒO retransmitir automaticamente a NF-e."
            )
        }

    resposta_bruta = (
        resultado_consulta.get(
            "resposta_bruta"
        )
    )

    if not resposta_bruta:

        return {
            "tentou": True,
            "recuperado": False,
            "numero_recibo":
                numero_recibo,
            "resultado_consulta":
                resultado_consulta,
            "mensagem": (
                "AutorizaÃ§Ã£o recuperada pelo recibo, mas "
                "a resposta bruta nÃ£o foi preservada."
            )
        }

    return {
        "tentou": True,
        "recuperado": True,
        "numero_recibo":
            numero_recibo,
        "resultado_consulta":
            resultado_consulta,
        "retorno":
            retorno_consulta,
        "resposta_bruta":
            resposta_bruta,
        "mensagem": (
            "AutorizaÃ§Ã£o recuperada com sucesso "
            "pela consulta do recibo."
        )
    }


# ============================================================
# EMITIR NF-e EM HOMOLOGAÃ‡ÃƒO
#
# FLUXO:
#
# 1. montar rascunho
# 2. gerar XML estrutural
# 2.1 validar XML estrutural
# 3. assinar XML
# 3.1 validar XML assinado
# 4. gerar enviNFe
# 4.1 validar enviNFe
# 5. transmitir SEFAZ
# 6. exigir autorizaÃ§Ã£o
# 7. montar nfeProc
# 7.1 validar nfeProc
# 8. finalizar documento + numeraÃ§Ã£o em transaÃ§Ã£o Ãºnica
#
# IMPORTANTE:
# - homologaÃ§Ã£o somente
# - modelo 55
# - recupera automaticamente autorizaÃ§Ã£o por recibo
#   quando houver cStat 204/539 e nRec disponÃ­vel
# - nÃ£o retransmite automaticamente apÃ³s retorno ambÃ­guo
# ============================================================
def emitir_nfe_homologacao(
    venda_id,
    uf_destino,
    caminho_certificado,
    senha_certificado,
    diretorio_saida=None,
    timeout=60
):

    modelo = 55

    if diretorio_saida is None:

        diretorio_saida = Path(
            "xml/gerados_teste"
        )

    else:

        diretorio_saida = (
            _normalizar_caminho(
                diretorio_saida
            )
        )

    caminho_certificado = (
        _normalizar_caminho(
            caminho_certificado
        )
    )

    # ========================================================
    # 0 - TRAVA CONTRA DUPLICIDADE POR VENDA
    #
    # Antes de gerar XML, assinar ou transmitir, verifica se
    # esta venda já possui documento fiscal AUTORIZADO.
    #
    # Por segurança:
    # - falha na consulta ao banco BLOQUEIA a emissão;
    # - documento autorizado encontrado BLOQUEIA a emissão;
    # - somente "não encontrado" permite continuar.
    # ========================================================
    consulta_documento = (
        buscar_documento_autorizado_por_venda(
            venda_id
        )
    )

    if not consulta_documento.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "VERIFICAR_VENDA_FATURADA",
            "mensagem": (
                consulta_documento.get(
                    "mensagem"
                )
                or
                "Não foi possível verificar se a venda já possui NF-e autorizada."
            ),
            "venda_id": venda_id,
            "consulta_documento":
                consulta_documento,
            "nao_retransmitir": True
        }

    if consulta_documento.get(
        "encontrado"
    ):

        documento_existente = (
            consulta_documento.get(
                "documento"
            )
            or
            {}
        )

        return {
            "sucesso": False,
            "etapa": "VENDA_JA_FATURADA",
            "mensagem": (
                "Esta venda já possui documento fiscal autorizado. "
                "Uma nova NF-e não será gerada nem transmitida."
            ),
            "venda_id": venda_id,
            "documento_existente":
                documento_existente,
            "modelo":
                documento_existente.get(
                    "modelo"
                ),
            "serie":
                documento_existente.get(
                    "serie"
                ),
            "numero":
                documento_existente.get(
                    "numero"
                ),
            "chave_acesso":
                documento_existente.get(
                    "chave_acesso"
                ),
            "protocolo":
                documento_existente.get(
                    "protocolo"
                ),
            "cstat":
                documento_existente.get(
                    "cstat"
                ),
            "xmotivo":
                documento_existente.get(
                    "xmotivo"
                ),
            "data_autorizacao":
                documento_existente.get(
                    "data_autorizacao"
                ),
            "nao_retransmitir": True
        }

    # ========================================================
    # 1 - RASCUNHO
    # ========================================================
    rascunho = (
        montar_rascunho_documento_fiscal(
            venda_id=venda_id,
            modelo=modelo,
            uf_destino=uf_destino
        )
    )

    if not rascunho.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "RASCUNHO",
            "mensagem": (
                rascunho.get(
                    "mensagem"
                )
                or
                "Falha ao montar rascunho fiscal."
            ),
            "rascunho":
                rascunho
        }

    if not rascunho.get(
        "pode_gerar_xml"
    ):

        return {
            "sucesso": False,
            "etapa": "RASCUNHO",
            "mensagem": (
                rascunho.get(
                    "mensagem"
                )
                or
                "Venda bloqueada pela validaÃ§Ã£o fiscal."
            ),
            "rascunho":
                rascunho
        }

    serie = rascunho.get(
        "serie"
    )

    numero = rascunho.get(
        "numero_sugerido"
    )

    ambiente = rascunho.get(
        "ambiente"
    )

    if ambiente != 2:

        return {
            "sucesso": False,
            "etapa": "AMBIENTE",
            "mensagem": (
                "O emissor de teste aceita somente "
                "ambiente de homologaÃ§Ã£o."
            )
        }

    # ========================================================
    # NOMES DOS ARQUIVOS
    # ========================================================
    prefixo = (
        f"nfe_55_serie_{serie}_numero_{numero}"
    )

    caminho_estrutural = (
        diretorio_saida
        /
        f"{prefixo}_estrutural.xml"
    )

    caminho_assinado = (
        diretorio_saida
        /
        f"{prefixo}_assinada.xml"
    )

    caminho_envi = (
        diretorio_saida
        /
        f"envi_nfe_serie_{serie}_numero_{numero}.xml"
    )

    caminho_retorno_sefaz = (
        diretorio_saida
        /
        f"retorno_sefaz_serie_{serie}_numero_{numero}.xml"
    )

    caminho_retorno_recibo = (
        diretorio_saida
        /
        f"retorno_recibo_sefaz_serie_{serie}_numero_{numero}.xml"
    )

    caminho_processado = (
        diretorio_saida
        /
        f"{prefixo}_processada.xml"
    )

    # ========================================================
    # 2 - GERAR XML ESTRUTURAL
    # ========================================================
    resultado_xml = (
        gerar_xml_nfe(
            rascunho
        )
    )

    if not resultado_xml.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "GERAR_XML",
            "mensagem":
                "Falha ao gerar XML da NF-e.",
            "resultado":
                resultado_xml
        }

    xml_estrutural = (
        _extrair_xml_resultado(
            resultado_xml
        )
    )

    if not xml_estrutural:

        return {
            "sucesso": False,
            "etapa": "GERAR_XML",
            "mensagem":
                "Gerador nÃ£o retornou XML."
        }

    _salvar_xml(
        caminho_estrutural,
        xml_estrutural
    )

    # ========================================================
    # 2.1 - VALIDAR XML ESTRUTURAL
    # ========================================================
    validacao_estrutural = (
        _validar_xml_estrutural(
            caminho_estrutural
        )
    )

    if not validacao_estrutural.get(
        "sucesso"
    ):

        return validacao_estrutural

    # ========================================================
    # 3 - ASSINAR XML
    # ========================================================
    resultado_assinatura = (
        assinar_xml_nfe(
            xml=caminho_estrutural,
            caminho_certificado=
                caminho_certificado,
            senha=senha_certificado
        )
    )

    if not resultado_assinatura.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "ASSINATURA",
            "mensagem":
                "Falha ao assinar NF-e.",
            "resultado":
                resultado_assinatura
        }

    xml_assinado = (
        _extrair_xml_resultado(
            resultado_assinatura
        )
    )

    if not xml_assinado:

        return {
            "sucesso": False,
            "etapa": "ASSINATURA",
            "mensagem":
                "Assinador nÃ£o retornou XML assinado."
        }

    _salvar_xml(
        caminho_assinado,
        xml_assinado
    )

    # ========================================================
    # 3.1 - VALIDAR XML ASSINADO
    # ========================================================
    validacao_assinado = (
        _validar_xsd_obrigatorio(
            caminho_xml=
                caminho_assinado,
            caminho_xsd=
                XSD_NFE,
            etapa=
                "XSD_ASSINADO"
        )
    )

    if not validacao_assinado.get(
        "sucesso"
    ):

        return validacao_assinado

    # ========================================================
    # 4 - GERAR enviNFe
    #
    # idLote temporariamente derivado de sÃ©rie/nÃºmero.
    # ========================================================
    id_lote = int(
        f"{serie}{numero}"
    )

    resultado_envi = (
        gerar_envi_nfe(
            nfes=[
                caminho_assinado
            ],
            id_lote=id_lote,
            ind_sinc=1
        )
    )

    if not resultado_envi.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "ENVI_NFE",
            "mensagem":
                "Falha ao gerar enviNFe.",
            "resultado":
                resultado_envi
        }

    xml_envi = (
        _extrair_xml_resultado(
            resultado_envi
        )
    )

    if not xml_envi:

        return {
            "sucesso": False,
            "etapa": "ENVI_NFE",
            "mensagem":
                "Gerador nÃ£o retornou enviNFe."
        }

    _salvar_xml(
        caminho_envi,
        xml_envi
    )

    # ========================================================
    # 4.1 - VALIDAR enviNFe
    # ========================================================
    validacao_envi = (
        _validar_xsd_obrigatorio(
            caminho_xml=
                caminho_envi,
            caminho_xsd=
                XSD_ENVI_NFE,
            etapa=
                "XSD_ENVI_NFE"
        )
    )

    if not validacao_envi.get(
        "sucesso"
    ):

        return validacao_envi

    # ========================================================
    # 5 - TRANSMITIR
    # ========================================================
    resultado_sefaz = (
        autorizar_nfe_homologacao_mg(
            origem_envi_nfe=
                caminho_envi,
            caminho_certificado=
                caminho_certificado,
            senha=
                senha_certificado,
            timeout=
                timeout
        )
    )

    # ========================================================
    # 5.1 - PRESERVAR RETORNO BRUTO DA SEFAZ
    #
    # O retorno é salvo imediatamente após a comunicação,
    # antes de qualquer análise de autorização/rejeição.
    # Assim, cStat/xMotivo e o SOAP retornado não se perdem
    # mesmo que a emissão seja rejeitada ou a tela recarregue.
    # ========================================================
    resposta_bruta_inicial = (
        resultado_sefaz.get(
            "resposta_bruta"
        )
    )

    if resposta_bruta_inicial:
        _salvar_xml(
            caminho_retorno_sefaz,
            resposta_bruta_inicial
        )

    # --------------------------------------------------------
    # Se houve falha HTTP DEPOIS da tentativa de envio,
    # o estado pode ser incerto.
    #
    # NÃ£o retransmitir automaticamente.
    # --------------------------------------------------------
    if not resultado_sefaz.get(
        "sucesso_http"
    ):

        return {
            "sucesso": False,
            "etapa": "SEFAZ_HTTP",
            "mensagem": (
                "Falha na comunicaÃ§Ã£o com a SEFAZ. "
                "Como o envio pode ter sido iniciado, "
                "NÃƒO retransmitir automaticamente a NF-e."
            ),
            "resultado":
                resultado_sefaz,
            "estado_incerto":
                bool(
                    resultado_sefaz.get(
                        "enviado"
                    )
                ),
            "arquivos": {
                "estrutural":
                    str(
                        caminho_estrutural
                    ),
                "assinado":
                    str(
                        caminho_assinado
                    ),
                "envi_nfe":
                    str(
                        caminho_envi
                    )
            }
        }

    retorno_sefaz_original = (
        resultado_sefaz.get(
            "retorno"
        )
        or
        {}
    )

    retorno_sefaz = (
        retorno_sefaz_original
    )

    resposta_bruta = (
        resultado_sefaz.get(
            "resposta_bruta"
        )
    )

    recuperacao_recibo = {
        "tentou": False,
        "recuperado": False,
        "numero_recibo": None,
        "resultado_consulta": None,
        "mensagem": None
    }

    # ========================================================
    # 6 - EXIGIR AUTORIZAÃ‡ÃƒO
    #
    # Se vier duplicidade 204/539, tentar recuperar o
    # protocolo pelo nRec SEM retransmitir a NF-e.
    # ========================================================
    if not retorno_sefaz.get(
        "autorizado"
    ):

        recuperacao_recibo = (
            _recuperar_autorizacao_por_recibo(
                retorno_original=
                    retorno_sefaz_original,
                caminho_certificado=
                    caminho_certificado,
                senha_certificado=
                    senha_certificado,
                timeout=
                    timeout
            )
        )

        if recuperacao_recibo.get(
            "recuperado"
        ):

            retorno_sefaz = (
                recuperacao_recibo.get(
                    "retorno"
                )
                or
                {}
            )

            resposta_bruta = (
                recuperacao_recibo.get(
                    "resposta_bruta"
                )
            )

            if resposta_bruta:
                _salvar_xml(
                    caminho_retorno_recibo,
                    resposta_bruta
                )

        else:

            cstats = (
                _extrair_cstats_protocolos(
                    retorno_sefaz_original
                )
            )

            duplicidade = any(
                cstat in (
                    "204",
                    "539"
                )
                for cstat in cstats
            )

            return {
                "sucesso": False,
                "etapa":
                    (
                        "SEFAZ_DUPLICIDADE"
                        if duplicidade
                        else
                        "SEFAZ_RETORNO"
                    ),
                "mensagem":
                    (
                        recuperacao_recibo.get(
                            "mensagem"
                        )
                        if duplicidade
                        else
                        "NF-e nÃ£o autorizada pela SEFAZ."
                    ),
                "retorno":
                    retorno_sefaz_original,
                "resposta_bruta":
                    resultado_sefaz.get(
                        "resposta_bruta"
                    ),
                "recuperacao_recibo":
                    recuperacao_recibo,
                "nao_retransmitir":
                    duplicidade,
                "arquivos": {
                    "estrutural":
                        str(
                            caminho_estrutural
                        ),
                    "assinado":
                        str(
                            caminho_assinado
                        ),
                    "envi_nfe":
                        str(
                            caminho_envi
                        ),
                    "retorno_sefaz":
                        str(
                            caminho_retorno_sefaz
                        )
                }
            }

    if not resposta_bruta:

        return {
            "sucesso": False,
            "etapa": "SEFAZ_RETORNO",
            "mensagem": (
                "SEFAZ autorizou a NF-e, mas a resposta "
                "bruta nÃ£o foi preservada. "
                "NÃƒO retransmitir a NF-e."
            ),
            "retorno_sefaz":
                retorno_sefaz,
            "recuperacao_recibo":
                recuperacao_recibo,
            "nao_retransmitir":
                True
        }

    # ========================================================
    # 7 - MONTAR nfeProc
    # ========================================================
    resultado_processado = (
        montar_nfe_processada(
            origem_nfe_assinada=
                caminho_assinado,
            resposta_sefaz=
                resposta_bruta
        )
    )

    if not resultado_processado.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "NFE_PROC",
            "mensagem":
                "Falha ao montar nfeProc.",
            "resultado":
                resultado_processado
        }

    xml_processado = (
        _extrair_xml_resultado(
            resultado_processado
        )
    )

    if not xml_processado:

        return {
            "sucesso": False,
            "etapa": "NFE_PROC",
            "mensagem":
                "Montagem do nfeProc nÃ£o retornou XML."
        }

    _salvar_xml(
        caminho_processado,
        xml_processado
    )

    # ========================================================
    # 7.1 - VALIDAR nfeProc
    # ========================================================
    validacao_processado = (
        _validar_xsd_obrigatorio(
            caminho_xml=
                caminho_processado,
            caminho_xsd=
                XSD_NFE_PROC,
            etapa=
                "XSD_NFE_PROC"
        )
    )

    if not validacao_processado.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "XSD_NFE_PROC",
            "mensagem": (
                "NF-e foi autorizada pela SEFAZ, "
                "mas o nfeProc nÃ£o passou no XSD. "
                "NÃƒO retransmitir a NF-e."
            ),
            "validacao":
                validacao_processado,
            "retorno_sefaz":
                retorno_sefaz,
            "recuperacao_recibo":
                recuperacao_recibo,
            "chave_acesso":
                resultado_xml.get(
                    "chave_acesso"
                ),
            "arquivos": {
                "estrutural":
                    str(
                        caminho_estrutural
                    ),
                "assinado":
                    str(
                        caminho_assinado
                    ),
                "envi_nfe":
                    str(
                        caminho_envi
                    ),
                "processado":
                    str(
                        caminho_processado
                    ),
                "retorno_sefaz":
                    str(
                        caminho_retorno_sefaz
                    )
            }
        }

    # ========================================================
    # 8 - FINALIZAÃ‡ÃƒO TRANSACIONAL
    # ========================================================
    resultado_finalizacao = (
        finalizar_documento_fiscal_autorizado(
            xml_processado=
                caminho_processado,
            xml_assinado=
                caminho_assinado,
            venda_id=
                venda_id,
            origem_documento=
                "ERP_HOMOLOGACAO"
        )
    )

    if not resultado_finalizacao.get(
        "sucesso"
    ):

        return {
            "sucesso": False,
            "etapa": "FINALIZACAO",
            "mensagem": (
                "NF-e foi autorizada pela SEFAZ, "
                "mas houve falha na finalizaÃ§Ã£o local. "
                "NÃƒO retransmitir a NF-e."
            ),
            "resultado":
                resultado_finalizacao,
            "retorno_sefaz":
                retorno_sefaz,
            "chave_acesso":
                resultado_xml.get(
                    "chave_acesso"
                ),
            "arquivos": {
                "estrutural":
                    str(
                        caminho_estrutural
                    ),
                "assinado":
                    str(
                        caminho_assinado
                    ),
                "envi_nfe":
                    str(
                        caminho_envi
                    ),
                "processado":
                    str(
                        caminho_processado
                    ),
                "retorno_sefaz":
                    str(
                        caminho_retorno_sefaz
                    )
            }
        }

    # ========================================================
    # RESULTADO FINAL
    # ========================================================
    return {
        "sucesso": True,
        "etapa": "CONCLUIDO",
        "mensagem":
            "NF-e emitida e finalizada com sucesso.",
        "venda_id":
            venda_id,
        "modelo":
            modelo,
        "serie":
            serie,
        "numero":
            numero,
        "chave_acesso":
            resultado_xml.get(
                "chave_acesso"
            ),
        "digest_value":
            resultado_assinatura.get(
                "digest_value"
            ),
        "retorno_sefaz":
            retorno_sefaz,
        "recuperacao_recibo":
            recuperacao_recibo,
        "finalizacao":
            resultado_finalizacao,
        "arquivos": {
            "estrutural":
                str(
                    caminho_estrutural
                ),
            "assinado":
                str(
                    caminho_assinado
                ),
            "envi_nfe":
                str(
                    caminho_envi
                ),
            "processado":
                str(
                    caminho_processado
                ),
            "retorno_sefaz":
                str(
                    caminho_retorno_sefaz
                )
        }
    }