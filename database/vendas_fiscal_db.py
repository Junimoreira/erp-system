from database.connection import conectar


# ============================================================
# BUSCAR CABEÇALHO DA VENDA PARA EMISSÃO FISCAL
# ============================================================
def buscar_venda_para_emissao(
    venda_id
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
                cliente_id,
                valor_total,
                desconto,
                valor_final,
                forma_pagamento,
                status,
                data_venda,
                autorizacao_cartao,
                conta_bancaria_id,
                caixa_id
            FROM vendas
            WHERE id = %s
            LIMIT 1
            """,
            (
                venda_id,
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        return {
            "id": registro[0],
            "cliente_id": registro[1],
            "valor_total": registro[2],
            "desconto": registro[3],
            "valor_final": registro[4],
            "forma_pagamento": registro[5],
            "status": registro[6],
            "data_venda": registro[7],
            "autorizacao_cartao": registro[8],
            "conta_bancaria_id": registro[9],
            "caixa_id": registro[10],
        }

    except Exception as erro:

        print(
            "Erro ao buscar venda para emissão fiscal:",
            erro
        )

        return None

    finally:
        conn.close()


# ============================================================
# BUSCAR ITENS DA VENDA PARA EMISSÃO FISCAL
# ============================================================
def buscar_itens_venda_para_emissao(
    venda_id
):

    conn = conectar()

    if conn is None:
        return []

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                iv.id,
                iv.venda_id,
                iv.produto_id,
                iv.quantidade,
                iv.preco_unitario,
                iv.subtotal,

                p.nome,
                p.codigo_barras,
                p.ncm,
                p.cest,
                p.perfil_icms,
                p.cfop_saida_interna,
                p.cfop_saida_interestadual,
                p.csosn_saida_interna,
                p.csosn_saida_interestadual,
                p.cst_ibs_cbs_saida,
                p.classificacao_tributaria_saida,
                p.origem_mercadoria,
                p.fiscal_revisado,
                p.fiscal_fonte,
                p.fiscal_confianca,
                p.fiscal_observacao,
                p.fiscal_atualizado_em

            FROM itens_venda iv

            JOIN produtos p
                ON p.id = iv.produto_id

            WHERE iv.venda_id = %s

            ORDER BY iv.id
            """,
            (
                venda_id,
            )
        )

        registros = cursor.fetchall()

        itens = []

        for registro in registros:

            itens.append(
                {
                    "item_id": registro[0],
                    "venda_id": registro[1],
                    "produto_id": registro[2],
                    "quantidade": registro[3],
                    "preco_unitario": registro[4],
                    "subtotal": registro[5],

                    "produto_nome": registro[6],
                    "codigo_barras": registro[7],
                    "ncm": registro[8],
                    "cest": registro[9],

                    "perfil_icms": registro[10],

                    "cfop_saida_interna": registro[11],
                    "cfop_saida_interestadual": registro[12],

                    "csosn_saida_interna": registro[13],
                    "csosn_saida_interestadual": registro[14],

                    "cst_ibs_cbs_saida": registro[15],

                    "classificacao_tributaria_saida":
                        registro[16],

                    "origem_mercadoria": registro[17],

                    "fiscal_revisado": registro[18],
                    "fiscal_fonte": registro[19],
                    "fiscal_confianca": registro[20],
                    "fiscal_observacao": registro[21],
                    "fiscal_atualizado_em": registro[22],
                }
            )

        return itens

    except Exception as erro:

        print(
            "Erro ao buscar itens da venda para emissão fiscal:",
            erro
        )

        return []

    finally:
        conn.close()


# ============================================================
# MONTAR VENDA COMPLETA PARA EMISSÃO FISCAL
# ============================================================
def montar_venda_para_emissao(
    venda_id
):

    venda = buscar_venda_para_emissao(
        venda_id
    )

    if venda is None:

        return {
            "sucesso": False,
            "mensagem": (
                f"Venda {venda_id} não encontrada."
            ),
            "venda": None
        }

    itens = buscar_itens_venda_para_emissao(
        venda_id
    )

    venda["itens"] = itens

    return {
        "sucesso": True,
        "mensagem": (
            "Venda carregada para análise fiscal."
        ),
        "venda": venda
    }