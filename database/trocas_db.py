# database/trocas_db.py

import pandas as pd

from database.connection import conectar

from database.finance_engine import (
    registrar_entrada_caixa,
    registrar_entrada_banco
)


# ============================================================
# NORMALIZAR FORMA DE PAGAMENTO
# ============================================================

def normalizar_forma_pagamento(forma_pagamento):

    forma = str(
        forma_pagamento or ""
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


# ============================================================
# BUSCAR VENDA PARA TROCA
# ============================================================

def buscar_venda_para_troca(venda_id):

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
                int(venda_id),
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar venda para troca:",
            erro
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ============================================================
# LISTAR ITENS DA VENDA DISPONÍVEIS PARA TROCA
# ============================================================

def listar_itens_disponiveis_troca(venda_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                i.id AS item_venda_id,

                i.produto_id,

                p.nome AS produto,

                i.quantidade
                    AS quantidade_vendida,

                i.preco_unitario,

                i.subtotal,

                COALESCE(
                    i.desconto,
                    0
                ) AS desconto,

                CASE
                    WHEN COALESCE(i.valor_final, 0) > 0
                        THEN i.valor_final
                    ELSE
                        GREATEST(
                            COALESCE(i.subtotal, 0)
                            -
                            COALESCE(i.desconto, 0),
                            0
                        )
                END AS valor_final,

                COALESCE(
                    (
                        SELECT SUM(it.quantidade)
                        FROM itens_troca it

                        INNER JOIN trocas t
                            ON t.id = it.troca_id

                        WHERE
                            it.item_venda_id = i.id

                            AND it.tipo = 'DEVOLVIDO'

                            AND UPPER(
                                COALESCE(
                                    t.status,
                                    ''
                                )
                            ) <> 'CANCELADA'
                    ),
                    0
                ) AS quantidade_ja_trocada

            FROM itens_venda i

            INNER JOIN produtos p
                ON p.id = i.produto_id

            WHERE i.venda_id = %s

            ORDER BY p.nome
        """

        df = pd.read_sql(
            query,
            conn,
            params=(
                int(venda_id),
            )
        )

        if df.empty:
            return df

        df["quantidade_disponivel"] = (
            df["quantidade_vendida"].astype(int)
            -
            df["quantidade_ja_trocada"].astype(int)
        )

        return df

    except Exception as erro:

        print(
            "Erro ao listar itens disponíveis para troca:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# LISTAR PRODUTOS PARA TROCA
# ============================================================

def listar_produtos_para_troca():

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
                codigo_barras,
                ativo
            FROM produtos
            WHERE COALESCE(
                ativo,
                TRUE
            ) = TRUE
            ORDER BY nome
            """,
            conn
        )

    except Exception as erro:

        print(
            "Erro ao listar produtos para troca:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# CALCULAR CRÉDITO UNITÁRIO
# ============================================================

def calcular_valor_unitario_credito(
    quantidade_vendida,
    valor_final_item
):

    quantidade_vendida = int(
        quantidade_vendida or 0
    )

    valor_final_item = float(
        valor_final_item or 0
    )

    if quantidade_vendida <= 0:
        return 0.0

    return round(
        valor_final_item / quantidade_vendida,
        2
    )


# ============================================================
# VALIDAR ITENS DEVOLVIDOS
# ============================================================

def validar_itens_devolvidos(
    cursor,
    venda_id,
    itens_devolvidos
):

    if not itens_devolvidos:

        raise Exception(
            "Informe pelo menos um produto devolvido."
        )

    itens_validados = []

    for item in itens_devolvidos:

        item_venda_id = int(
            item["item_venda_id"]
        )

        quantidade_devolver = int(
            item["quantidade"]
        )

        if quantidade_devolver <= 0:

            raise Exception(
                "A quantidade devolvida deve ser maior que zero."
            )

        cursor.execute(
            """
            SELECT
                i.id,
                i.produto_id,
                i.quantidade,
                i.preco_unitario,
                i.subtotal,

                COALESCE(
                    i.desconto,
                    0
                ),

                CASE
                    WHEN COALESCE(i.valor_final, 0) > 0
                        THEN i.valor_final
                    ELSE
                        GREATEST(
                            COALESCE(i.subtotal, 0)
                            -
                            COALESCE(i.desconto, 0),
                            0
                        )
                END

            FROM itens_venda i

            WHERE
                i.id = %s
                AND i.venda_id = %s

            LIMIT 1
            """,
            (
                item_venda_id,
                venda_id
            )
        )

        registro = cursor.fetchone()

        if registro is None:

            raise Exception(
                "Item da venda não encontrado."
            )

        (
            _,
            produto_id,
            quantidade_vendida,
            preco_unitario,
            subtotal,
            desconto,
            valor_final_item
        ) = registro

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(it.quantidade),
                    0
                )

            FROM itens_troca it

            INNER JOIN trocas t
                ON t.id = it.troca_id

            WHERE
                it.item_venda_id = %s

                AND it.tipo = 'DEVOLVIDO'

                AND UPPER(
                    COALESCE(
                        t.status,
                        ''
                    )
                ) <> 'CANCELADA'
            """,
            (
                item_venda_id,
            )
        )

        quantidade_ja_trocada = int(
            cursor.fetchone()[0] or 0
        )

        quantidade_disponivel = (
            int(quantidade_vendida)
            -
            quantidade_ja_trocada
        )

        if quantidade_devolver > quantidade_disponivel:

            raise Exception(
                "Quantidade devolvida maior que a quantidade disponível para troca."
            )

        valor_unitario_credito = (
            calcular_valor_unitario_credito(
                quantidade_vendida=quantidade_vendida,
                valor_final_item=valor_final_item
            )
        )

        valor_credito = round(
            valor_unitario_credito
            *
            quantidade_devolver,
            2
        )

        itens_validados.append(
            {
                "item_venda_id": item_venda_id,

                "produto_id": int(
                    produto_id
                ),

                "quantidade": quantidade_devolver,

                "preco_unitario": valor_unitario_credito,

                "valor_total": valor_credito
            }
        )

    return itens_validados


# ============================================================
# VALIDAR NOVOS PRODUTOS
# ============================================================

def validar_itens_novos(
    cursor,
    itens_novos
):

    if not itens_novos:

        raise Exception(
            "Informe pelo menos um novo produto para a troca."
        )

    itens_validados = []

    for item in itens_novos:

        produto_id = int(
            item["produto_id"]
        )

        quantidade = int(
            item["quantidade"]
        )

        if quantidade <= 0:

            raise Exception(
                "A quantidade do novo produto deve ser maior que zero."
            )

        cursor.execute(
            """
            SELECT
                id,
                nome,
                preco,
                estoque,
                ativo
            FROM produtos
            WHERE id = %s
            LIMIT 1
            """,
            (
                produto_id,
            )
        )

        produto = cursor.fetchone()

        if produto is None:

            raise Exception(
                f"Produto ID {produto_id} não encontrado."
            )

        (
            _,
            nome,
            preco,
            estoque,
            ativo
        ) = produto

        if ativo is False:

            raise Exception(
                f"O produto '{nome}' está inativo."
            )

        estoque = int(
            estoque or 0
        )

        if quantidade > estoque:

            raise Exception(
                f"Estoque insuficiente para '{nome}'. "
                f"Disponível: {estoque}."
            )

        preco = float(
            preco or 0
        )

        valor_total = round(
            preco * quantidade,
            2
        )

        itens_validados.append(
            {
                "produto_id": produto_id,

                "quantidade": quantidade,

                "preco_unitario": preco,

                "valor_total": valor_total
            }
        )

    return itens_validados


# ============================================================
# REGISTRAR DIFERENÇA FINANCEIRA
# ============================================================

def registrar_diferenca_financeira(
    conn,
    troca_id,
    diferenca,
    forma_pagamento,
    conta_bancaria_id=None,
    usuario=None
):

    diferenca = round(
        float(diferenca or 0),
        2
    )

    if diferenca <= 0:
        return True

    forma_normalizada = (
        normalizar_forma_pagamento(
            forma_pagamento
        )
    )

    descricao = (
        f"Troca #{troca_id} - "
        f"diferença da troca"
    )

    # --------------------------------------------------------
    # DINHEIRO
    # --------------------------------------------------------

    if forma_normalizada in [
        "DINHEIRO",
        "CAIXA"
    ]:

        sucesso = registrar_entrada_caixa(
            valor=diferenca,

            descricao=descricao,

            origem="TROCA",

            categoria="TROCA_DIFERENCA",

            referencia_id=troca_id,

            referencia_tipo="TROCA",

            usuario=usuario,

            conn_externa=conn
        )

        if not sucesso:

            raise Exception(
                "Não foi possível registrar a diferença da troca no caixa."
            )

        return True

    # --------------------------------------------------------
    # BANCO
    # --------------------------------------------------------

    elif forma_normalizada in [
        "PIX",
        "DEBITO",
        "CARTAO DEBITO",
        "TRANSFERENCIA",
        "BOLETO",
        "BANCO"
    ]:

        if conta_bancaria_id is None:

            raise Exception(
                "Selecione uma conta bancária para receber a diferença da troca."
            )

        sucesso = registrar_entrada_banco(
            conta_bancaria_id=int(
                conta_bancaria_id
            ),

            valor=diferenca,

            descricao=descricao,

            origem="TROCA",

            categoria="TROCA_DIFERENCA",

            referencia_id=troca_id,

            referencia_tipo="TROCA",

            usuario=usuario,

            conn_externa=conn
        )

        if not sucesso:

            raise Exception(
                "Não foi possível registrar a diferença da troca no banco."
            )

        return True

    # --------------------------------------------------------
    # OUTRAS FORMAS
    # --------------------------------------------------------

    else:

        raise Exception(
            "Forma de pagamento da diferença ainda não suportada: "
            f"{forma_pagamento}"
        )


# ============================================================
# REGISTRAR TROCA
# ============================================================

def registrar_troca(
    venda_original_id,
    itens_devolvidos,
    itens_novos,
    motivo=None,
    usuario=None,
    observacoes=None,
    forma_pagamento_diferenca=None,
    conta_bancaria_id=None
):

    conn = conectar()

    if conn is None:

        return {
            "sucesso": False,

            "erro": (
                "Não foi possível conectar ao banco de dados."
            )
        }

    cursor = conn.cursor()

    try:

        venda_original_id = int(
            venda_original_id
        )

        # ----------------------------------------------------
        # BUSCAR VENDA
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                cliente_id,
                status
            FROM vendas
            WHERE id = %s
            FOR UPDATE
            """,
            (
                venda_original_id,
            )
        )

        venda = cursor.fetchone()

        if venda is None:

            raise Exception(
                "Venda original não encontrada."
            )

        (
            _,
            cliente_id,
            status_venda
        ) = venda

        status_normalizado = str(
            status_venda or ""
        ).strip().upper()

        if status_normalizado == "CANCELADA":

            raise Exception(
                "Não é possível realizar troca de uma venda cancelada."
            )

        # ----------------------------------------------------
        # VALIDAR ITENS DEVOLVIDOS
        # ----------------------------------------------------

        devolvidos = validar_itens_devolvidos(
            cursor=cursor,
            venda_id=venda_original_id,
            itens_devolvidos=itens_devolvidos
        )

        # ----------------------------------------------------
        # VALIDAR ITENS NOVOS
        # ----------------------------------------------------

        novos = validar_itens_novos(
            cursor=cursor,
            itens_novos=itens_novos
        )

        # ----------------------------------------------------
        # CALCULAR VALORES
        # ----------------------------------------------------

        valor_credito = round(
            sum(
                float(
                    item["valor_total"]
                )
                for item in devolvidos
            ),
            2
        )

        valor_novos = round(
            sum(
                float(
                    item["valor_total"]
                )
                for item in novos
            ),
            2
        )

        diferenca = round(
            valor_novos - valor_credito,
            2
        )

        # ----------------------------------------------------
        # NOVO PRODUTO MAIS BARATO
        # ----------------------------------------------------

        if diferenca < 0:

            raise Exception(
                "O valor dos novos produtos é menor que o crédito da troca. "
                "Nesta primeira versão, use produtos de valor igual ou maior. "
                "O vale-crédito será implementado na próxima etapa."
            )

        if (
            diferenca > 0
            and
            not forma_pagamento_diferenca
        ):

            raise Exception(
                "Informe a forma de pagamento da diferença."
            )

        # ----------------------------------------------------
        # CRIAR TROCA
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO trocas (
                venda_original_id,
                cliente_id,
                motivo,
                valor_credito,
                valor_novos,
                diferenca,
                forma_pagamento_diferenca,
                conta_bancaria_id,
                usuario,
                observacoes,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'CONCLUIDA'
            )
            RETURNING id
            """,
            (
                venda_original_id,
                cliente_id,
                motivo,
                valor_credito,
                valor_novos,
                diferenca,
                forma_pagamento_diferenca,
                conta_bancaria_id,
                usuario,
                observacoes
            )
        )

        troca_id = int(
            cursor.fetchone()[0]
        )

        # ----------------------------------------------------
        # PRODUTOS DEVOLVIDOS
        # ----------------------------------------------------

        for item in devolvidos:

            cursor.execute(
                """
                INSERT INTO itens_troca (
                    troca_id,
                    item_venda_id,
                    produto_id,
                    tipo,
                    quantidade,
                    preco_unitario,
                    valor_total
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'DEVOLVIDO',
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    troca_id,
                    item["item_venda_id"],
                    item["produto_id"],
                    item["quantidade"],
                    item["preco_unitario"],
                    item["valor_total"]
                )
            )

            cursor.execute(
                """
                UPDATE produtos
                SET estoque =
                    COALESCE(
                        estoque,
                        0
                    ) + %s
                WHERE id = %s
                """,
                (
                    item["quantidade"],
                    item["produto_id"]
                )
            )

            if cursor.rowcount == 0:

                raise Exception(
                    "Erro ao devolver produto ao estoque."
                )

        # ----------------------------------------------------
        # NOVOS PRODUTOS
        # ----------------------------------------------------

        for item in novos:

            cursor.execute(
                """
                SELECT
                    estoque
                FROM produtos
                WHERE id = %s
                FOR UPDATE
                """,
                (
                    item["produto_id"],
                )
            )

            resultado_estoque = (
                cursor.fetchone()
            )

            if resultado_estoque is None:

                raise Exception(
                    "Produto novo não encontrado durante a baixa."
                )

            estoque_atual = int(
                resultado_estoque[0] or 0
            )

            if (
                item["quantidade"]
                >
                estoque_atual
            ):

                raise Exception(
                    "Estoque insuficiente durante a conclusão da troca."
                )

            cursor.execute(
                """
                INSERT INTO itens_troca (
                    troca_id,
                    item_venda_id,
                    produto_id,
                    tipo,
                    quantidade,
                    preco_unitario,
                    valor_total
                )
                VALUES (
                    %s,
                    NULL,
                    %s,
                    'NOVO',
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    troca_id,
                    item["produto_id"],
                    item["quantidade"],
                    item["preco_unitario"],
                    item["valor_total"]
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
                """,
                (
                    item["quantidade"],
                    item["produto_id"]
                )
            )

            if cursor.rowcount == 0:

                raise Exception(
                    "Erro ao baixar estoque do novo produto."
                )

        # ----------------------------------------------------
        # FINANCEIRO DA DIFERENÇA
        # ----------------------------------------------------

        if diferenca > 0:

            registrar_diferenca_financeira(
                conn=conn,

                troca_id=troca_id,

                diferenca=diferenca,

                forma_pagamento=(
                    forma_pagamento_diferenca
                ),

                conta_bancaria_id=(
                    conta_bancaria_id
                ),

                usuario=usuario
            )

        # ----------------------------------------------------
        # FINALIZAR
        # ----------------------------------------------------

        conn.commit()

        return {
            "sucesso": True,

            "troca_id": troca_id,

            "valor_credito": valor_credito,

            "valor_novos": valor_novos,

            "diferenca": diferenca
        }

    except Exception as erro:

        conn.rollback()

        print(
            "\n"
            +
            "=" * 80
        )

        print(
            "ERRO AO REGISTRAR TROCA"
        )

        print(
            erro
        )

        print(
            "=" * 80
        )

        return {
            "sucesso": False,

            "erro": str(
                erro
            )
        }

    finally:

        cursor.close()
        conn.close()


# ============================================================
# HISTÓRICO DE TROCAS
# ============================================================

def historico_trocas():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                t.id AS troca,

                t.venda_original_id
                    AS venda_original,

                c.nome AS cliente,

                t.data_troca,

                t.valor_credito,

                t.valor_novos,

                t.diferenca,

                t.forma_pagamento_diferenca,

                t.motivo,

                t.usuario,

                t.status

            FROM trocas t

            LEFT JOIN clientes c
                ON c.id = t.cliente_id

            ORDER BY
                t.id DESC
            """,
            conn
        )

    except Exception as erro:

        print(
            "Erro ao consultar histórico de trocas:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# LISTAR ITENS DE UMA TROCA
# ============================================================

def listar_itens_troca(troca_id):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                it.id,

                it.tipo,

                it.item_venda_id,

                it.produto_id,

                p.nome AS produto,

                it.quantidade,

                it.preco_unitario,

                it.valor_total

            FROM itens_troca it

            INNER JOIN produtos p
                ON p.id = it.produto_id

            WHERE it.troca_id = %s

            ORDER BY
                CASE
                    WHEN it.tipo = 'DEVOLVIDO'
                        THEN 1
                    ELSE 2
                END,
                p.nome
            """,
            conn,

            params=(
                int(troca_id),
            )
        )

    except Exception as erro:

        print(
            "Erro ao listar itens da troca:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# BUSCAR TROCA POR ID
# ============================================================

def buscar_troca_por_id(troca_id):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                t.id,

                t.venda_original_id,

                t.cliente_id,

                c.nome AS cliente,

                t.data_troca,

                t.motivo,

                t.valor_credito,

                t.valor_novos,

                t.diferenca,

                t.forma_pagamento_diferenca,

                t.conta_bancaria_id,

                t.usuario,

                t.observacoes,

                t.status

            FROM trocas t

            LEFT JOIN clientes c
                ON c.id = t.cliente_id

            WHERE t.id = %s

            LIMIT 1
            """,
            (
                int(troca_id),
            )
        )

        registro = cursor.fetchone()

        if registro is None:
            return None

        colunas = [
            descricao[0]
            for descricao in cursor.description
        ]

        return dict(
            zip(
                colunas,
                registro
            )
        )

    except Exception as erro:

        print(
            "Erro ao buscar troca:",
            erro
        )

        return None

    finally:

        cursor.close()
        conn.close()