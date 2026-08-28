from datetime import datetime
from pathlib import Path

import pandas as pd
from lxml import etree

from database.configuracoes_fiscais_db import (
    buscar_cnpj_empresa,
    avancar_numero_fiscal_autorizado,
)

from database.connection import conectar
from services.fiscal.xml_fiscal_reader import (
    ler_xml_fiscal,
)


# ============================================================
# NORMALIZAR DATA
# ============================================================
def _normalizar_data_iso(valor):

    if not valor:
        return None

    if isinstance(
        valor,
        datetime
    ):
        return valor

    try:

        texto = str(
            valor
        ).strip()

        if not texto:
            return None

        return datetime.fromisoformat(
            texto.replace(
                "Z",
                "+00:00"
            )
        )

    except Exception:
        return None


# ============================================================
# LER CONTEÚDO XML COMO TEXTO
# ============================================================
def _xml_para_texto(
    origem
):

    if isinstance(
        origem,
        Path
    ):

        if not origem.is_file():

            raise ValueError(
                "Arquivo XML não encontrado."
            )

        return origem.read_text(
            encoding="utf-8"
        )

    if isinstance(
        origem,
        bytes
    ):

        return origem.decode(
            "utf-8"
        )

    if isinstance(
        origem,
        str
    ):

        texto = origem.strip()

        if texto.startswith(
            "<"
        ):

            return origem

        caminho = Path(
            origem
        )

        if caminho.is_file():

            return caminho.read_text(
                encoding="utf-8"
            )

        raise ValueError(
            "Arquivo XML não encontrado."
        )

    raise ValueError(
        "Tipo de origem XML não suportado."
    )


# ============================================================
# EXTRAIR PROTOCOLO DO nfeProc
# ============================================================
def _extrair_protocolo_nfe_proc(
    xml_processado
):

    texto = _xml_para_texto(
        xml_processado
    )

    parser = etree.XMLParser(
        remove_blank_text=False,
        resolve_entities=False,
        no_network=True
    )

    raiz = etree.fromstring(
        texto.encode(
            "utf-8"
        ),
        parser
    )

    protocolos = raiz.xpath(
        ".//*[local-name()='protNFe']"
    )

    if len(
        protocolos
    ) != 1:

        raise ValueError(
            (
                "O XML processado deve possuir "
                "exatamente um protNFe."
            )
        )

    inf_prot_list = protocolos[0].xpath(
        "./*[local-name()='infProt']"
    )

    if not inf_prot_list:

        raise ValueError(
            "protNFe sem infProt."
        )

    inf_prot = inf_prot_list[0]

    def texto_local(
        nome
    ):

        elementos = inf_prot.xpath(
            "./*[local-name()=$nome]",
            nome=nome
        )

        if not elementos:

            return None

        valor = elementos[0].text

        if valor is None:

            return None

        valor = valor.strip()

        return valor or None

    return {
        "tp_amb":
            texto_local(
                "tpAmb"
            ),

        "chave_acesso":
            texto_local(
                "chNFe"
            ),

        "data_autorizacao":
            _normalizar_data_iso(
                texto_local(
                    "dhRecbto"
                )
            ),

        "protocolo":
            texto_local(
                "nProt"
            ),

        "digest_value":
            texto_local(
                "digVal"
            ),

        "cstat":
            texto_local(
                "cStat"
            ),

        "xmotivo":
            texto_local(
                "xMotivo"
            )
    }


# ============================================================
# DEFINIR TIPO DE MOVIMENTO
# ============================================================
def _definir_tipo_movimento(
    nota
):

    cnpj_empresa = (
        buscar_cnpj_empresa()
    )

    if not cnpj_empresa:

        raise ValueError(
            "Configuração fiscal da empresa "
            "não encontrada."
        )

    emitente_cnpj = (
        nota.get(
            "emitente",
            {}
        ).get(
            "cnpj"
        )
    )

    destinatario_cnpj = (
        nota.get(
            "destinatario",
            {}
        ).get(
            "cnpj"
        )
    )

    if emitente_cnpj == cnpj_empresa:
        return "SAIDA"

    if destinatario_cnpj == cnpj_empresa:
        return "ENTRADA"

    return "DESCONHECIDO"


# ============================================================
# INSERIR ITENS DO DOCUMENTO
# ============================================================
def _inserir_itens_documento(
    cursor,
    documento_id,
    itens
):

    quantidade_itens = 0

    for item in itens or []:

        cursor.execute(
            """
            INSERT INTO documentos_fiscais_itens (
                documento_fiscal_id,
                numero_item,
                codigo_produto,
                codigo_barras,
                descricao,
                ncm,
                cest,
                cfop,
                unidade,
                quantidade,
                valor_unitario,
                valor_produto,
                valor_desconto,
                origem_icms,
                cst_icms,
                csosn,
                cst_pis,
                cst_cofins,
                cst_ibs_cbs,
                classificacao_tributaria,
                valor_ibs,
                valor_cbs
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s
            )
            """,
            (
                documento_id,
                item.get("numero_item"),
                item.get("codigo_produto"),
                item.get("codigo_barras"),
                item.get("descricao"),
                item.get("ncm"),
                item.get("cest"),
                item.get("cfop"),
                item.get("unidade"),
                item.get("quantidade"),
                item.get("valor_unitario"),
                item.get("valor_produto"),
                item.get("valor_desconto"),
                item.get("origem_icms"),
                item.get("cst_icms"),
                item.get("csosn"),
                item.get("cst_pis"),
                item.get("cst_cofins"),
                item.get("cst_ibs_cbs"),
                item.get("classificacao_tributaria"),
                item.get("valor_ibs"),
                item.get("valor_cbs")
            )
        )

        quantidade_itens += 1

    return quantidade_itens


# ============================================================
# BUSCAR DOCUMENTO POR CHAVE
# ============================================================
def buscar_documento_por_chave(
    chave_acesso
):

    conn = conectar()

    if conn is None:
        return None

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                chave_acesso,
                modelo,
                serie,
                numero,
                tipo_movimento,
                finalidade,
                ambiente,
                natureza_operacao,
                data_emissao,
                emitente_cnpj,
                emitente_nome,
                emitente_uf,
                destinatario_documento,
                destinatario_nome,
                destinatario_uf,
                valor_produtos,
                valor_frete,
                valor_desconto,
                valor_total,
                protocolo,
                status,
                xml_original,
                origem_documento,
                criado_em,
                venda_id,
                cstat,
                xmotivo,
                digest_value,
                data_autorizacao,
                xml_assinado,
                xml_processado,
                atualizado_em
            FROM documentos_fiscais
            WHERE chave_acesso = %s
            LIMIT 1
            """,
            (
                chave_acesso,
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            "id",
            "chave_acesso",
            "modelo",
            "serie",
            "numero",
            "tipo_movimento",
            "finalidade",
            "ambiente",
            "natureza_operacao",
            "data_emissao",
            "emitente_cnpj",
            "emitente_nome",
            "emitente_uf",
            "destinatario_documento",
            "destinatario_nome",
            "destinatario_uf",
            "valor_produtos",
            "valor_frete",
            "valor_desconto",
            "valor_total",
            "protocolo",
            "status",
            "xml_original",
            "origem_documento",
            "criado_em",
            "venda_id",
            "cstat",
            "xmotivo",
            "digest_value",
            "data_autorizacao",
            "xml_assinado",
            "xml_processado",
            "atualizado_em"
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar documento fiscal:",
            erro
        )

        return None

    finally:

        conn.close()


# ============================================================
# BUSCAR DOCUMENTO AUTORIZADO POR VENDA
#
# TRAVA DE SEGURANÇA:
# - usada antes da transmissão para evitar segunda NF-e
#   autorizada para a mesma venda;
# - diferencia "não encontrado" de falha de banco;
# - não altera dados e não faz commit.
# ============================================================
def buscar_documento_autorizado_por_venda(
    venda_id
):

    if venda_id is None:

        return {
            "sucesso": False,
            "encontrado": False,
            "documento": None,
            "mensagem": (
                "Venda não informada para consulta fiscal."
            )
        }

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "encontrado": False,
            "documento": None,
            "mensagem": (
                "Não foi possível conectar ao banco de dados "
                "para verificar documento autorizado da venda."
            )
        }

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                venda_id,
                chave_acesso,
                modelo,
                serie,
                numero,
                protocolo,
                status,
                valor_total,
                cstat,
                xmotivo,
                data_autorizacao,
                origem_documento,
                criado_em,
                atualizado_em,
                xml_assinado,
                xml_processado
            FROM documentos_fiscais
            WHERE venda_id = %s
              AND status = 'AUTORIZADO'
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                venda_id,
            )
        )

        registro = cursor.fetchone()

        if registro is None:

            return {
                "sucesso": True,
                "encontrado": False,
                "documento": None,
                "mensagem": (
                    "Nenhum documento fiscal autorizado "
                    "encontrado para esta venda."
                )
            }

        colunas = [
            "id",
            "venda_id",
            "chave_acesso",
            "modelo",
            "serie",
            "numero",
            "protocolo",
            "status",
            "valor_total",
            "cstat",
            "xmotivo",
            "data_autorizacao",
            "origem_documento",
            "criado_em",
            "atualizado_em",
            "xml_assinado",
            "xml_processado",
        ]

        documento = dict(
            zip(
                colunas,
                registro
            )
        )

        return {
            "sucesso": True,
            "encontrado": True,
            "documento": documento,
            "mensagem": (
                "Documento fiscal autorizado encontrado "
                "para esta venda."
            )
        }

    except Exception as erro:

        print(
            "Erro ao buscar documento autorizado por venda:",
            erro
        )

        return {
            "sucesso": False,
            "encontrado": False,
            "documento": None,
            "mensagem": (
                "Falha ao verificar se a venda já possui "
                f"documento fiscal autorizado: {erro}"
            )
        }

    finally:

        conn.close()


# ============================================================
# REGISTRAR DOCUMENTO AUTORIZADO PELO ERP
# ============================================================
def registrar_documento_autorizado(
    xml_processado,
    xml_assinado,
    venda_id=None,
    origem_documento="ERP",
    conn=None
):

    conexao_externa = (
        conn is not None
    )

    if not conexao_externa:

        conn = conectar()

        if conn is None:

            return {
                "sucesso": False,
                "duplicado": False,
                "documento_id": None,
                "mensagem": (
                    "Não foi possível conectar "
                    "ao banco de dados."
                )
            }

    try:

        xml_processado_texto = _xml_para_texto(
            xml_processado
        )

        xml_assinado_texto = _xml_para_texto(
            xml_assinado
        )

        protocolo_dados = (
            _extrair_protocolo_nfe_proc(
                xml_processado_texto
            )
        )

        cstat = protocolo_dados.get(
            "cstat"
        )

        if cstat not in (
            "100",
            "150"
        ):

            raise ValueError(
                (
                    "Documento não autorizado para registro. "
                    f"cStat={cstat or '?'} "
                    f"xMotivo={protocolo_dados.get('xmotivo') or '?'}"
                )
            )

        protocolo = protocolo_dados.get(
            "protocolo"
        )

        if not protocolo:

            raise ValueError(
                "XML processado sem número de protocolo."
            )

        nota = ler_xml_fiscal(
            xml_processado_texto
        )

        if not isinstance(
            nota,
            dict
        ):

            raise ValueError(
                "Leitor fiscal não retornou dados válidos "
                "para o XML processado."
            )

        chave_acesso = nota.get(
            "chave_acesso"
        )

        if not chave_acesso:

            raise ValueError(
                "XML processado sem chave de acesso."
            )

        if (
            protocolo_dados.get(
                "chave_acesso"
            )
            !=
            chave_acesso
        ):

            raise ValueError(
                (
                    "A chave do protocolo não corresponde "
                    "à chave do XML processado."
                )
            )

        modelo = nota.get(
            "modelo"
        )

        if modelo not in (
            55,
            65
        ):

            raise ValueError(
                (
                    "Modelo fiscal não suportado no "
                    "registro pós-autorização."
                )
            )

        nota_assinada = ler_xml_fiscal(
            xml_assinado_texto
        )

        if not isinstance(
            nota_assinada,
            dict
        ):

            raise ValueError(
                "Leitor fiscal não retornou dados válidos "
                "para o XML assinado."
            )

        chave_assinada = nota_assinada.get(
            "chave_acesso"
        )

        if chave_assinada != chave_acesso:

            raise ValueError(
                (
                    "A chave do XML assinado não corresponde "
                    "à chave do XML processado."
                )
            )

        emitente = nota.get(
            "emitente",
            {}
        )

        destinatario = nota.get(
            "destinatario",
            {}
        )

        emitente_cnpj = (
            emitente.get("cnpj")
            or emitente.get("cpf")
        )

        destinatario_documento = (
            destinatario.get("cnpj")
            or destinatario.get("cpf")
        )

        tipo_movimento = (
            _definir_tipo_movimento(
                nota
            )
        )

        if tipo_movimento != "SAIDA":

            raise ValueError(
                (
                    "O registro pós-autorização do ERP "
                    "aceita somente documento de SAÍDA."
                )
            )

        data_emissao = _normalizar_data_iso(
            nota.get(
                "data_emissao"
            )
        )

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                status,
                protocolo,
                cstat
            FROM documentos_fiscais
            WHERE chave_acesso = %s
            LIMIT 1
            """,
            (
                chave_acesso,
            )
        )

        existente = cursor.fetchone()

        if existente:

            if not conexao_externa:
                conn.rollback()

            return {
                "sucesso": True,
                "duplicado": True,
                "documento_id": existente[0],
                "chave_acesso": chave_acesso,
                "status": existente[1],
                "protocolo": existente[2],
                "cstat": existente[3],
                "mensagem": (
                    "Documento fiscal já registrado "
                    "anteriormente."
                )
            }

        cursor.execute(
            """
            INSERT INTO documentos_fiscais (
                chave_acesso,
                modelo,
                serie,
                numero,
                tipo_movimento,
                finalidade,
                ambiente,
                natureza_operacao,
                data_emissao,
                emitente_cnpj,
                emitente_nome,
                emitente_uf,
                destinatario_documento,
                destinatario_nome,
                destinatario_uf,
                valor_produtos,
                valor_frete,
                valor_desconto,
                valor_total,
                protocolo,
                status,
                xml_original,
                origem_documento,
                venda_id,
                cstat,
                xmotivo,
                digest_value,
                data_autorizacao,
                xml_assinado,
                xml_processado,
                atualizado_em
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, CURRENT_TIMESTAMP
            )
            RETURNING id
            """,
            (
                chave_acesso,
                modelo,
                nota.get("serie"),
                nota.get("numero"),
                tipo_movimento,
                nota.get("finalidade"),
                nota.get("ambiente"),
                nota.get("natureza_operacao"),
                data_emissao,
                emitente_cnpj,
                emitente.get("razao_social"),
                emitente.get("uf"),
                destinatario_documento,
                destinatario.get("nome"),
                destinatario.get("uf"),
                nota.get("valor_produtos"),
                nota.get("valor_frete"),
                nota.get("valor_desconto"),
                nota.get("valor_total"),
                protocolo,
                "AUTORIZADO",
                None,
                origem_documento,
                venda_id,
                cstat,
                protocolo_dados.get("xmotivo"),
                protocolo_dados.get("digest_value"),
                protocolo_dados.get("data_autorizacao"),
                xml_assinado_texto,
                xml_processado_texto
            )
        )

        documento_id = (
            cursor.fetchone()[0]
        )

        quantidade_itens = (
            _inserir_itens_documento(
                cursor=cursor,
                documento_id=documento_id,
                itens=nota.get(
                    "itens",
                    []
                )
            )
        )

        if not conexao_externa:
            conn.commit()

        return {
            "sucesso": True,
            "duplicado": False,
            "documento_id": documento_id,
            "venda_id": venda_id,
            "chave_acesso": chave_acesso,
            "modelo": modelo,
            "serie": nota.get("serie"),
            "numero": nota.get("numero"),
            "protocolo": protocolo,
            "cstat": cstat,
            "xmotivo": protocolo_dados.get("xmotivo"),
            "digest_value": protocolo_dados.get("digest_value"),
            "data_autorizacao": protocolo_dados.get("data_autorizacao"),
            "status": "AUTORIZADO",
            "quantidade_itens": quantidade_itens,
            "valor_total": nota.get("valor_total"),
            "mensagem": (
                "Documento fiscal autorizado registrado "
                "com sucesso."
            )
        }

    except Exception as erro:

        if not conexao_externa:
            conn.rollback()

        print(
            "Erro ao registrar documento autorizado:",
            erro
        )

        return {
            "sucesso": False,
            "duplicado": False,
            "documento_id": None,
            "mensagem": str(
                erro
            )
        }

    finally:

        if (
            not conexao_externa
            and
            conn is not None
        ):
            conn.close()


# ============================================================
# FINALIZAR DOCUMENTO FISCAL AUTORIZADO
# ============================================================
def finalizar_documento_fiscal_autorizado(
    xml_processado,
    xml_assinado,
    venda_id=None,
    origem_documento="ERP"
):

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "documento": None,
            "numeracao": None,
            "mensagem": (
                "Não foi possível conectar "
                "ao banco de dados."
            )
        }

    try:

        resultado_documento = (
            registrar_documento_autorizado(
                xml_processado=xml_processado,
                xml_assinado=xml_assinado,
                venda_id=venda_id,
                origem_documento=origem_documento,
                conn=conn
            )
        )

        if not resultado_documento.get(
            "sucesso"
        ):

            raise ValueError(
                (
                    "Falha ao registrar documento fiscal: "
                    f"{resultado_documento.get('mensagem')}"
                )
            )

        modelo = resultado_documento.get(
            "modelo"
        )

        serie = resultado_documento.get(
            "serie"
        )

        numero = resultado_documento.get(
            "numero"
        )

        if resultado_documento.get(
            "duplicado"
        ):

            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    modelo,
                    serie,
                    numero
                FROM documentos_fiscais
                WHERE id = %s
                LIMIT 1
                """,
                (
                    resultado_documento.get(
                        "documento_id"
                    ),
                )
            )

            registro = cursor.fetchone()

            if not registro:

                raise ValueError(
                    (
                        "Documento duplicado identificado, "
                        "mas não foi possível recuperar "
                        "modelo, série e número."
                    )
                )

            (
                modelo,
                serie,
                numero
            ) = registro

        if modelo is None:

            raise ValueError(
                "Modelo fiscal não identificado."
            )

        if serie is None:

            raise ValueError(
                "Série fiscal não identificada."
            )

        if numero is None:

            raise ValueError(
                "Número fiscal não identificado."
            )

        resultado_numeracao = (
            avancar_numero_fiscal_autorizado(
                modelo=modelo,
                serie=serie,
                numero_autorizado=numero,
                conn=conn
            )
        )

        if not resultado_numeracao.get(
            "sucesso"
        ):

            raise ValueError(
                (
                    "Falha ao avançar numeração fiscal: "
                    f"{resultado_numeracao.get('mensagem')}"
                )
            )

        conn.commit()

        return {
            "sucesso": True,
            "documento":
                resultado_documento,
            "numeracao":
                resultado_numeracao,
            "mensagem": (
                "Documento fiscal autorizado finalizado "
                "com sucesso."
            )
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao finalizar documento fiscal autorizado:",
            erro
        )

        return {
            "sucesso": False,
            "documento": None,
            "numeracao": None,
            "mensagem": str(
                erro
            )
        }

    finally:

        conn.close()


# ============================================================
# IMPORTAR XML FISCAL
# ============================================================
def importar_xml_fiscal(
    origem_xml,
    origem_documento="IMPORTACAO"
):

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,
            "mensagem": (
                "Não foi possível conectar "
                "ao banco de dados."
            )
        }

    try:

        nota = ler_xml_fiscal(
            origem_xml
        )

        chave_acesso = nota.get(
            "chave_acesso"
        )

        if not chave_acesso:

            return {
                "sucesso": False,
                "mensagem": (
                    "XML sem chave de acesso."
                )
            }

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM documentos_fiscais
            WHERE chave_acesso = %s
            LIMIT 1
            """,
            (
                chave_acesso,
            )
        )

        existente = cursor.fetchone()

        if existente:

            return {
                "sucesso": False,
                "duplicado": True,
                "documento_id": existente[0],
                "mensagem": (
                    "Documento fiscal já importado."
                )
            }

        emitente = nota.get(
            "emitente",
            {}
        )

        destinatario = nota.get(
            "destinatario",
            {}
        )

        emitente_cnpj = (
            emitente.get("cnpj")
            or emitente.get("cpf")
        )

        destinatario_documento = (
            destinatario.get("cnpj")
            or destinatario.get("cpf")
        )

        tipo_movimento = (
            _definir_tipo_movimento(
                nota
            )
        )

        data_emissao = (
            _normalizar_data_iso(
                nota.get(
                    "data_emissao"
                )
            )
        )

        cursor.execute(
            """
            INSERT INTO documentos_fiscais (
                chave_acesso,
                modelo,
                serie,
                numero,
                tipo_movimento,
                finalidade,
                ambiente,
                natureza_operacao,
                data_emissao,
                emitente_cnpj,
                emitente_nome,
                emitente_uf,
                destinatario_documento,
                destinatario_nome,
                destinatario_uf,
                valor_produtos,
                valor_frete,
                valor_desconto,
                valor_total,
                protocolo,
                status,
                xml_original,
                origem_documento
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            RETURNING id
            """,
            (
                chave_acesso,
                nota.get("modelo"),
                nota.get("serie"),
                nota.get("numero"),
                tipo_movimento,
                nota.get("finalidade"),
                nota.get("ambiente"),
                nota.get("natureza_operacao"),
                data_emissao,
                emitente_cnpj,
                emitente.get("razao_social"),
                emitente.get("uf"),
                destinatario_documento,
                destinatario.get("nome"),
                destinatario.get("uf"),
                nota.get("valor_produtos"),
                nota.get("valor_frete"),
                nota.get("valor_desconto"),
                nota.get("valor_total"),
                nota.get("protocolo"),
                "IMPORTADO",
                nota.get("xml_original"),
                origem_documento
            )
        )

        documento_id = (
            cursor.fetchone()[0]
        )

        quantidade_itens = (
            _inserir_itens_documento(
                cursor=cursor,
                documento_id=documento_id,
                itens=nota.get(
                    "itens",
                    []
                )
            )
        )

        conn.commit()

        return {
            "sucesso": True,
            "duplicado": False,
            "documento_id": documento_id,
            "chave_acesso": chave_acesso,
            "modelo": nota.get("modelo"),
            "numero": nota.get("numero"),
            "tipo_movimento":
                tipo_movimento,
            "quantidade_itens":
                quantidade_itens,
            "valor_total": nota.get("valor_total"),
            "mensagem": (
                "Documento fiscal importado "
                "com sucesso."
            )
        }

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao importar XML fiscal:",
            erro
        )

        return {
            "sucesso": False,
            "mensagem": str(
                erro
            )
        }

    finally:

        conn.close()


# ============================================================
# LISTAR DOCUMENTOS FISCAIS
# ============================================================
def listar_documentos_fiscais():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                data_emissao,
                modelo,
                serie,
                numero,
                tipo_movimento,
                emitente_nome,
                emitente_cnpj,
                destinatario_nome,
                destinatario_documento,
                valor_total,
                protocolo,
                cstat,
                status,
                venda_id,
                chave_acesso,
                origem_documento
            FROM documentos_fiscais
            ORDER BY
                data_emissao DESC,
                id DESC
        """

        return pd.read_sql(
            query,
            conn
        )

    except Exception as erro:

        print(
            "Erro ao listar documentos fiscais:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# LISTAR ITENS DE UM DOCUMENTO
# ============================================================
def listar_itens_documento(
    documento_fiscal_id
):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                numero_item,
                codigo_produto,
                codigo_barras,
                descricao,
                ncm,
                cest,
                cfop,
                unidade,
                quantidade,
                valor_unitario,
                valor_produto,
                valor_desconto,
                origem_icms,
                cst_icms,
                csosn,
                cst_pis,
                cst_cofins,
                cst_ibs_cbs,
                classificacao_tributaria,
                valor_ibs,
                valor_cbs
            FROM documentos_fiscais_itens
            WHERE documento_fiscal_id = %s
            ORDER BY numero_item
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                documento_fiscal_id,
            )
        )

    except Exception as erro:

        print(
            "Erro ao listar itens fiscais:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()