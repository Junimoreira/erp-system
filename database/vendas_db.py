# database/vendas_db.py

import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta

from database.connection import conectar

from database.finance_engine import (
    registrar_entrada_caixa,
    registrar_entrada_banco
)

from database.contas_receber_db import cadastrar_conta_receber


# ==================================================
# CLIENTES
# ==================================================

def listar_clientes():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                id,
                nome
            FROM clientes
            ORDER BY nome
            """,
            conn
        )

    except Exception as erro:

        print("Erro ao listar clientes:", erro)
        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# PRODUTOS
# ==================================================

def listar_produtos():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                id,
                nome,
                preco,
                estoque,
                codigo_barras
            FROM produtos
            ORDER BY nome
            """,
            conn
        )

    except Exception as erro:

        print("Erro ao listar produtos:", erro)
        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# NORMALIZAR FORMA DE PAGAMENTO
# ==================================================

def normalizar_forma_pagamento(forma_pagamento):

    forma = str(
        forma_pagamento
    ).upper().strip()

    substituicoes = {
        "Á": "A",
        "Ã": "A",
        "Â": "A",
        "À": "A",
        "É": "E",
        "Ê": "E",
        "Í": "I",
        "Ó": "O",
        "Õ": "O",
        "Ô": "O",
        "Ú": "U",
        "Ç": "C"
    }

    for antigo, novo in substituicoes.items():
        forma = forma.replace(
            antigo,
            novo
        )

    return forma


# ==================================================
# GERAR PARCELAS
# ==================================================

def gerar_parcelas(
    valor_total,
    numero_parcelas
):

    numero_parcelas = int(
        numero_parcelas
    )

    if numero_parcelas <= 0:
        numero_parcelas = 1

    valor_total = round(
        float(valor_total),
        2
    )

    valor_base = round(
        valor_total / numero_parcelas,
        2
    )

    parcelas = []
    acumulado = 0.0

    for parcela in range(
        1,
        numero_parcelas + 1
    ):

        if parcela < numero_parcelas:

            valor_parcela = valor_base
            acumulado += valor_parcela

        else:

            valor_parcela = round(
                valor_total - acumulado,
                2
            )

        parcelas.append(
            valor_parcela
        )

    return parcelas


# ==================================================
# SALVAR VENDA
# ==================================================

def salvar_venda(
    cliente_id,
    valor_total,
    desconto,
    valor_final,
    forma_pagamento,
    data_venda,
    itens,
    conta_bancaria_id=None,
    numero_parcelas=1
):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        forma_normalizada = (
            normalizar_forma_pagamento(
                forma_pagamento
            )
        )

        valor_total = float(
            valor_total
        )

        desconto = float(
            desconto
        )

        valor_final = float(
            valor_final
        )

        # ==========================================
        # INSERIR VENDA
        # ==========================================

        cursor.execute(
            """
            INSERT INTO vendas (
                cliente_id,
                valor_total,
                desconto,
                valor_final,
                forma_pagamento,
                data_venda,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                cliente_id,
                valor_total,
                desconto,
                valor_final,
                forma_pagamento,
                data_venda,
                "Concluída"
            )
        )

        venda_id = int(
            cursor.fetchone()[0]
        )

        # ==========================================
        # ITENS DA VENDA + BAIXA DE ESTOQUE
        # ==========================================

        for item in itens:

            produto_id = int(
                item["produto_id"]
            )

            quantidade = int(
                item["quantidade"]
            )

            preco = float(
                item["preco"]
            )

            subtotal = float(
                item["subtotal"]
            )

            desconto_item = float(
                item.get(
                    "desconto",
                    0
                ) or 0
            )

            valor_final_item = float(
                item.get(
                    "valor_final",
                    subtotal - desconto_item
                ) or 0
            )

            # Segurança contra valor negativo
            if valor_final_item < 0:
                valor_final_item = 0.0

            # ======================================
            # GRAVAR ITEM
            # ======================================

            cursor.execute(
                """
                INSERT INTO itens_venda (
                    venda_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    subtotal,
                    desconto,
                    valor_final
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    venda_id,
                    produto_id,
                    quantidade,
                    preco,
                    subtotal,
                    desconto_item,
                    valor_final_item
                )
            )

            # ======================================
            # BAIXAR ESTOQUE
            # ======================================

            cursor.execute(
                """
                UPDATE produtos
                SET estoque =
                    COALESCE(estoque, 0) - %s
                WHERE id = %s
                """,
                (
                    quantidade,
                    produto_id
                )
            )

            if cursor.rowcount == 0:

                raise Exception(
                    f"Produto ID {produto_id} "
                    "não encontrado para baixa de estoque."
                )

        # ==========================================
        # DINHEIRO / CAIXA
        # ==========================================

        if forma_normalizada in [
            "DINHEIRO",
            "CAIXA"
        ]:

            sucesso_caixa = (
                registrar_entrada_caixa(
                    valor=valor_final,
                    descricao=(
                        f"Venda #{venda_id} "
                        f"({forma_pagamento})"
                    ),
                    origem=forma_pagamento,
                    categoria="VENDA",
                    referencia_id=venda_id,
                    referencia_tipo="VENDA",
                    conn_externa=conn
                )
            )

            if not sucesso_caixa:

                raise Exception(
                    "Falha ao registrar "
                    "entrada no caixa."
                )

        # ==========================================
        # BANCO / PIX / DÉBITO / TRANSFERÊNCIA
        # ==========================================

        elif forma_normalizada in [
            "PIX",
            "DEBITO",
            "CARTAO DEBITO",
            "TRANSFERENCIA",
            "BOLETO",
            "BANCO"
        ]:

            if conta_bancaria_id is None:

                cursor.execute(
                    """
                    SELECT id
                    FROM contas_bancarias
                    ORDER BY id
                    LIMIT 1
                    """
                )

                conta = cursor.fetchone()

                if not conta:

                    raise Exception(
                        "Nenhuma conta bancária "
                        "cadastrada."
                    )

                conta_bancaria_id = int(
                    conta[0]
                )

            sucesso_banco = (
                registrar_entrada_banco(
                    conta_bancaria_id=(
                        conta_bancaria_id
                    ),
                    valor=valor_final,
                    descricao=(
                        f"Venda #{venda_id} "
                        f"({forma_pagamento})"
                    ),
                    origem=forma_pagamento,
                    categoria="VENDA",
                    referencia_id=venda_id,
                    referencia_tipo="VENDA",
                    conn_externa=conn
                )
            )

            if not sucesso_banco:

                raise Exception(
                    "Falha ao registrar "
                    "entrada bancária."
                )

        # ==========================================
        # CRÉDITO / PRAZO / FIADO
        # ==========================================

        elif forma_normalizada in [
            "CREDITO",
            "CARTAO CREDITO",
            "PRAZO",
            "FIADO"
        ]:

            numero_parcelas = int(
                numero_parcelas
            )

            if numero_parcelas < 1:
                numero_parcelas = 1

            parcelas = gerar_parcelas(
                valor_total=valor_final,
                numero_parcelas=numero_parcelas
            )

            data_base = data_venda

            if isinstance(
                data_base,
                datetime
            ):

                data_base = data_base.date()

            for indice, valor_parcela in enumerate(
                parcelas,
                start=1
            ):

                vencimento = (
                    data_base
                    +
                    relativedelta(
                        months=indice
                    )
                )

                sucesso_receber = (
                    cadastrar_conta_receber(
                        cliente_id=cliente_id,
                        descricao=(
                            f"Venda #{venda_id} - "
                            f"Parcela {indice}/"
                            f"{numero_parcelas}"
                        ),
                        valor=valor_parcela,
                        vencimento=vencimento,
                        observacoes=(
                            "Gerado automaticamente "
                            f"pela venda #{venda_id}"
                        ),
                        forma_pagamento=(
                            forma_pagamento
                        )
                    )
                )

                if not sucesso_receber:

                    raise Exception(
                        "Falha ao gerar parcela "
                        f"{indice}/"
                        f"{numero_parcelas} "
                        "em contas a receber."
                    )

        # ==========================================
        # FORMA NÃO RECONHECIDA
        # ==========================================

        else:

            raise Exception(
                "Forma de pagamento "
                "não reconhecida: "
                f"{forma_pagamento}"
            )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "\n"
            +
            "=" * 80
        )

        print(
            "ERRO AO SALVAR VENDA"
        )

        print(
            erro
        )

        print(
            "=" * 80
        )

        return False

    finally:

        cursor.close()
        conn.close()


# ==================================================
# HISTÓRICO DE VENDAS
# ==================================================

def historico_vendas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                v.id AS pedido,
                c.nome AS cliente,
                p.nome AS produto,
                i.quantidade,
                i.preco_unitario
                    AS valor_unitario,
                i.subtotal,
                COALESCE(
                    i.desconto,
                    0
                ) AS desconto_item,
                COALESCE(
                    i.valor_final,
                    i.subtotal
                ) AS valor_final_item,
                v.desconto,
                v.valor_final,
                v.forma_pagamento,
                v.data_venda,
                v.status
            FROM vendas v
            LEFT JOIN clientes c
                ON c.id = v.cliente_id
            LEFT JOIN itens_venda i
                ON i.venda_id = v.id
            LEFT JOIN produtos p
                ON p.id = i.produto_id
            ORDER BY
                v.id DESC,
                p.nome
            """,
            conn
        )

    except Exception as erro:

        print(
            "ERRO AO CONSULTAR "
            "HISTÓRICO DE VENDAS"
        )

        print(
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# BUSCAR VENDA POR ID
# ==================================================

def buscar_venda_por_id(venda_id):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                v.id,
                v.cliente_id,
                c.nome AS cliente,
                v.valor_total,
                v.desconto,
                v.valor_final,
                v.forma_pagamento,
                v.data_venda,
                v.status
            FROM vendas v
            LEFT JOIN clientes c
                ON c.id = v.cliente_id
            WHERE v.id = %s
            LIMIT 1
            """,
            (
                venda_id,
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            descricao[0]
            for descricao
            in cursor.description
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar venda:",
            erro
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ==================================================
# LISTAR ITENS DA VENDA
# ==================================================

def listar_itens_venda(venda_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                i.id AS item_venda_id,
                i.produto_id,
                p.nome,
                i.quantidade,
                i.preco_unitario,
                i.subtotal,
                COALESCE(
                    i.desconto,
                    0
                ) AS desconto,
                COALESCE(
                    i.valor_final,
                    i.subtotal
                ) AS valor_final
            FROM itens_venda i
            INNER JOIN produtos p
                ON p.id = i.produto_id
            WHERE i.venda_id = %s
            ORDER BY p.nome
            """,
            conn,
            params=(
                venda_id,
            )
        )

    except Exception as erro:

        print(
            "Erro ao listar itens da venda:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ==================================================
# RESUMO DE VENDAS DO DIA
# ==================================================

def resumo_vendas():

    conn = conectar()

    if conn is None:

        return {
            "quantidade": 0,
            "total": 0,
            "ticket_medio": 0
        }

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(
                    SUM(valor_final),
                    0
                ),
                COALESCE(
                    AVG(valor_final),
                    0
                )
            FROM vendas
            WHERE DATE(data_venda) = CURRENT_DATE
              AND COALESCE(
                    status,
                    ''
                  ) <> 'Cancelada'
            """
        )

        qtd, total, ticket = (
            cursor.fetchone()
        )

        return {
            "quantidade": int(
                qtd
            ),
            "total": float(
                total
            ),
            "ticket_medio": float(
                ticket
            )
        }

    except Exception as erro:

        print(
            "Erro resumo vendas:",
            erro
        )

        return {
            "quantidade": 0,
            "total": 0,
            "ticket_medio": 0
        }

    finally:

        cursor.close()
        conn.close()


# ==================================================
# CANCELAR VENDA
# ==================================================

def cancelar_venda(venda_id):

    conn = conectar()

    if conn is None:
        return False

    cursor = conn.cursor()

    try:

        # Verifica se a venda existe
        cursor.execute(
            """
            SELECT status
            FROM vendas
            WHERE id = %s
            LIMIT 1
            """,
            (
                venda_id,
            )
        )

        venda = cursor.fetchone()

        if venda is None:

            print(
                "Venda não encontrada."
            )

            return False

        status_atual = str(
            venda[0] or ""
        ).strip().lower()

        if status_atual == "cancelada":

            print(
                "Venda já está cancelada."
            )

            return False

        # Busca os produtos
        cursor.execute(
            """
            SELECT
                produto_id,
                quantidade
            FROM itens_venda
            WHERE venda_id = %s
            """,
            (
                venda_id,
            )
        )

        itens = cursor.fetchall()

        # Devolve ao estoque
        for produto_id, quantidade in itens:

            cursor.execute(
                """
                UPDATE produtos
                SET estoque =
                    COALESCE(estoque, 0) + %s
                WHERE id = %s
                """,
                (
                    quantidade,
                    produto_id
                )
            )

        # Marca como cancelada
        cursor.execute(
            """
            UPDATE vendas
            SET status = 'Cancelada'
            WHERE id = %s
            """,
            (
                venda_id,
            )
        )

        conn.commit()

        return True

    except Exception as erro:

        conn.rollback()

        print(
            "Erro ao cancelar venda:",
            erro
        )

        return False

    finally:

        cursor.close()
        conn.close()

# ==================================================
# SALVAR VENDA ORIGINADA DE MARKETPLACE
#
# IMPORTANTE:
# - grava venda ERP
# - grava itens_venda
# - baixa estoque uma unica vez
# - vincula marketplace_pedidos.venda_id
# - NAO movimenta caixa
# - NAO movimenta banco
# - NAO cria contas a receber convencionais
# ==================================================

def salvar_venda_marketplace(
    pedido_id,
    conn_externa=None
):

    conexao_propria = (
        conn_externa is None
    )

    conn = (
        conectar()
        if conexao_propria
        else conn_externa
    )

    if conn is None:
        return {
            "sucesso": False,
            "venda_id": None,
            "ja_existia": False,
            "mensagem": (
                "Nao foi possivel conectar "
                "ao banco de dados."
            ),
        }

    cursor = conn.cursor()

    try:

        # ==========================================
        # TRAVAR E CARREGAR PEDIDO
        # ==========================================

        cursor.execute(
            """
            SELECT
                p.id,
                p.cliente_id,
                p.venda_id,
                p.data_pedido,
                p.forma_pagamento,
                p.valor_produtos,
                p.status_fiscal,
                p.pedido_externo,
                c.codigo AS canal_codigo
            FROM marketplace_pedidos p
            JOIN marketplace_canais c
                ON c.id = p.canal_id
            WHERE p.id = %s
            LIMIT 1
            FOR UPDATE OF p
            """,
            (
                int(pedido_id),
            )
        )

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError(
                f"Pedido marketplace {pedido_id} "
                "nao encontrado."
            )

        (
            pedido_id_db,
            cliente_id,
            venda_id_existente,
            data_pedido,
            forma_pagamento,
            valor_produtos_pedido,
            status_fiscal,
            pedido_externo,
            canal_codigo,
        ) = pedido

        # ==========================================
        # IDEMPOTENCIA
        # ==========================================

        if venda_id_existente is not None:

            if conexao_propria:
                conn.commit()

            return {
                "sucesso": True,
                "venda_id": int(
                    venda_id_existente
                ),
                "ja_existia": True,
                "pedido_id": int(
                    pedido_id_db
                ),
                "pedido_externo":
                    pedido_externo,
                "mensagem": (
                    "Pedido marketplace ja possui "
                    "venda ERP vinculada."
                ),
            }

        if cliente_id is None:
            raise ValueError(
                "Pedido marketplace sem cliente "
                "vinculado."
            )

        # ==========================================
        # CARREGAR ITENS DO PEDIDO
        # ==========================================

        cursor.execute(
            """
            SELECT
                i.id,
                i.produto_id,
                i.descricao,
                i.quantidade,
                i.valor_unitario,
                i.valor_total,
                p.estoque
            FROM marketplace_pedido_itens i
            JOIN produtos p
                ON p.id = i.produto_id
            WHERE i.pedido_id = %s
            ORDER BY i.id
            FOR UPDATE OF p
            """,
            (
                pedido_id_db,
            )
        )

        itens = cursor.fetchall()

        if not itens:
            raise ValueError(
                "Pedido marketplace sem itens."
            )

        # ==========================================
        # VALIDAR E SOMAR ITENS
        # ==========================================

        valor_total_venda = 0.0

        itens_preparados = []

        for item in itens:

            (
                item_marketplace_id,
                produto_id,
                descricao,
                quantidade_raw,
                valor_unitario_raw,
                valor_total_raw,
                estoque_atual_raw,
            ) = item

            quantidade_float = float(
                quantidade_raw
            )

            quantidade = int(
                quantidade_float
            )

            # A tabela itens_venda atual trabalha
            # com quantidade inteira.
            if (
                quantidade <= 0
                or
                quantidade_float != quantidade
            ):
                raise ValueError(
                    (
                        "Quantidade invalida para "
                        f"o produto {produto_id}: "
                        f"{quantidade_raw}."
                    )
                )

            valor_unitario = round(
                float(
                    valor_unitario_raw
                    or 0
                ),
                2
            )

            valor_total_item = round(
                float(
                    valor_total_raw
                    or 0
                ),
                2
            )

            if valor_unitario <= 0:
                raise ValueError(
                    (
                        "Valor unitario invalido "
                        f"para o produto {produto_id}."
                    )
                )

            valor_calculado = round(
                valor_unitario
                *
                quantidade,
                2
            )

            if (
                valor_calculado
                !=
                valor_total_item
            ):
                raise ValueError(
                    (
                        "Valor do item marketplace "
                        "nao confere. "
                        f"Produto={produto_id}; "
                        f"calculado={valor_calculado:.2f}; "
                        f"pedido={valor_total_item:.2f}."
                    )
                )

            estoque_atual = float(
                estoque_atual_raw
                or 0
            )

            if estoque_atual < quantidade:
                raise ValueError(
                    (
                        "Estoque insuficiente para "
                        f"produto {produto_id}. "
                        f"Estoque={estoque_atual}; "
                        f"necessario={quantidade}."
                    )
                )

            valor_total_venda = round(
                valor_total_venda
                +
                valor_total_item,
                2
            )

            itens_preparados.append(
                {
                    "item_marketplace_id":
                        item_marketplace_id,
                    "produto_id":
                        int(produto_id),
                    "descricao":
                        descricao,
                    "quantidade":
                        quantidade,
                    "preco_unitario":
                        valor_unitario,
                    "subtotal":
                        valor_total_item,
                }
            )

        # ==========================================
        # CONFERIR TOTAL DA MERCADORIA
        # ==========================================

        valor_produtos_pedido = round(
            float(
                valor_produtos_pedido
                or 0
            ),
            2
        )

        if (
            valor_total_venda
            !=
            valor_produtos_pedido
        ):
            raise ValueError(
                (
                    "Soma dos itens difere do "
                    "valor de produtos do pedido. "
                    f"Itens={valor_total_venda:.2f}; "
                    f"pedido={valor_produtos_pedido:.2f}."
                )
            )

        # ==========================================
        # FORMA DE PAGAMENTO
        #
        # Mantemos a forma informada pelo marketplace
        # apenas para o motor fiscal.
        # Nenhuma movimentacao financeira e criada.
        # ==========================================

        forma_pagamento = str(
            forma_pagamento
            or ""
        ).strip()

        if not forma_pagamento:
            raise ValueError(
                "Pedido marketplace sem forma "
                "de pagamento."
            )

        # ==========================================
        # CRIAR VENDA ERP
        #
        # Para marketplace:
        # - valor_total = mercadoria
        # - desconto = 0
        # - valor_final = mercadoria
        #
        # Frete/desconto/taxas da plataforma
        # permanecem em marketplace_pedidos.
        # ==========================================

        cursor.execute(
            """
            INSERT INTO vendas (
                cliente_id,
                valor_total,
                desconto,
                valor_final,
                forma_pagamento,
                data_venda,
                status
            )
            VALUES (
                %s,
                %s,
                0,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING id
            """,
            (
                int(cliente_id),
                valor_total_venda,
                valor_total_venda,
                forma_pagamento,
                data_pedido,
                "Concluida",
            )
        )

        venda_id = int(
            cursor.fetchone()[0]
        )

        # ==========================================
        # ITENS + BAIXA DE ESTOQUE
        # ==========================================

        for item in itens_preparados:

            cursor.execute(
                """
                INSERT INTO itens_venda (
                    venda_id,
                    produto_id,
                    quantidade,
                    preco_unitario,
                    subtotal,
                    desconto,
                    valor_final
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    0,
                    %s
                )
                """,
                (
                    venda_id,
                    item["produto_id"],
                    item["quantidade"],
                    item["preco_unitario"],
                    item["subtotal"],
                    item["subtotal"],
                )
            )

            cursor.execute(
                """
                UPDATE produtos
                SET estoque =
                    COALESCE(
                        estoque,
                        0
                    ) - %s
                WHERE id = %s
                  AND COALESCE(
                        estoque,
                        0
                      ) >= %s
                """,
                (
                    item["quantidade"],
                    item["produto_id"],
                    item["quantidade"],
                )
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    (
                        "Falha na baixa segura "
                        "de estoque do produto "
                        f"{item['produto_id']}."
                    )
                )

        # ==========================================
        # VINCULAR PEDIDO A VENDA
        # ==========================================

        cursor.execute(
            """
            UPDATE marketplace_pedidos
            SET
                venda_id = %s,
                atualizado_em =
                    CURRENT_TIMESTAMP
            WHERE id = %s
              AND venda_id IS NULL
            """,
            (
                venda_id,
                pedido_id_db,
            )
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "Pedido marketplace mudou durante "
                "a criacao da venda."
            )

        # ==========================================
        # EVENTO
        # ==========================================

        cursor.execute(
            """
            INSERT INTO marketplace_eventos (
                pedido_id,
                tipo,
                status,
                descricao,
                origem
            )
            VALUES (
                %s,
                'VENDA_ERP_CRIADA',
                'OK',
                %s,
                'ERP'
            )
            """,
            (
                pedido_id_db,
                (
                    f"Venda ERP #{venda_id} criada "
                    f"a partir do pedido {canal_codigo} "
                    f"{pedido_externo}. "
                    "Sem movimentacao financeira "
                    "automatica."
                ),
            )
        )

        if conexao_propria:
            conn.commit()

        return {
            "sucesso": True,
            "venda_id": venda_id,
            "ja_existia": False,
            "pedido_id": int(
                pedido_id_db
            ),
            "pedido_externo":
                pedido_externo,
            "valor_venda":
                valor_total_venda,
            "quantidade_itens":
                len(
                    itens_preparados
                ),
            "mensagem": (
                "Venda marketplace criada "
                "com sucesso."
            ),
        }

    except Exception as erro:

        if conexao_propria:
            conn.rollback()

        return {
            "sucesso": False,
            "venda_id": None,
            "ja_existia": False,
            "mensagem": str(
                erro
            ),
        }

    finally:

        cursor.close()

        if conexao_propria:
            conn.close()
