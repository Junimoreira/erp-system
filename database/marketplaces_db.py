# database/marketplaces_db.py

import hashlib
from datetime import datetime, timedelta

import pandas as pd

from database.connection import conectar
from services.credenciais_seguras import (
    criptografar_texto,
    descriptografar_texto,
)


# ============================================================
# LISTAR CANAIS
# ============================================================

def listar_canais_marketplace(apenas_ativos=True):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                codigo,
                nome,
                ativo,
                integracao_api,
                criado_em,
                atualizado_em
            FROM marketplace_canais
        """

        if apenas_ativos:
            query += """
                WHERE ativo = TRUE
            """

        query += """
            ORDER BY nome
        """

        return pd.read_sql(
            query,
            conn
        )

    except Exception as erro:

        print(
            "Erro ao listar canais de marketplace:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# BUSCAR CANAL PELO CÓDIGO
# ============================================================

def buscar_canal_por_codigo(codigo):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        codigo = str(
            codigo or ""
        ).strip().upper()

        cursor.execute(
            """
            SELECT
                id,
                codigo,
                nome,
                ativo,
                integracao_api
            FROM marketplace_canais
            WHERE UPPER(codigo) = %s
            LIMIT 1
            """,
            (
                codigo,
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
            "Erro ao buscar canal de marketplace:",
            erro
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ============================================================
# LISTAR CLIENTES PARA PEDIDO
# ============================================================

def listar_clientes_marketplace():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                id,
                nome,
                cpf,
                cnpj,
                cidade,
                uf
            FROM clientes
            ORDER BY nome
            """,
            conn
        )

    except Exception as erro:

        print(
            "Erro ao listar clientes para marketplace:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# LISTAR PRODUTOS PARA PEDIDO
# ============================================================

def listar_produtos_marketplace():

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        return pd.read_sql(
            """
            SELECT
                id,
                nome,
                codigo_barras,
                preco,
                custo,
                estoque,
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
            "Erro ao listar produtos para marketplace:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# BUSCAR PEDIDO POR CANAL E NÚMERO EXTERNO
# ============================================================

def buscar_pedido_externo(
    canal_id,
    pedido_externo
):

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                mp.id,
                mp.canal_id,
                mc.codigo AS canal_codigo,
                mc.nome AS canal_nome,
                mp.pedido_externo,
                mp.cliente_id,
                c.nome AS cliente,
                mp.venda_id,
                mp.data_pedido,
                mp.data_aprovacao,
                mp.status_pedido,
                mp.status_fiscal,
                mp.status_envio,
                mp.status_repasse,
                mp.forma_pagamento,
                mp.valor_produtos,
                mp.valor_frete_cliente,
                mp.valor_desconto,
                mp.valor_total_cliente,
                mp.valor_comissao,
                mp.valor_tarifa_fixa,
                mp.valor_taxas_outros,
                mp.valor_coparticipacao_frete,
                mp.valor_repasse_previsto,
                mp.valor_repasse_recebido,
                mp.numero_nfe,
                mp.serie_nfe,
                mp.chave_nfe,
                mp.protocolo_nfe,
                mp.data_despacho,
                mp.codigo_rastreio,
                mp.observacoes,
                mp.criado_em,
                mp.atualizado_em
            FROM marketplace_pedidos mp

            INNER JOIN marketplace_canais mc
                ON mc.id = mp.canal_id

            LEFT JOIN clientes c
                ON c.id = mp.cliente_id

            WHERE
                mp.canal_id = %s
                AND mp.pedido_externo = %s

            LIMIT 1
            """,
            (
                int(canal_id),
                str(pedido_externo).strip()
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
            "Erro ao buscar pedido de marketplace:",
            erro
        )

        return None

    finally:

        cursor.close()
        conn.close()


# ============================================================
# REGISTRAR PEDIDO
# ============================================================

def registrar_pedido_marketplace(
    canal_id,
    pedido_externo,
    cliente_id,
    itens,
    data_pedido=None,
    data_aprovacao=None,
    forma_pagamento=None,
    valor_frete_cliente=0,
    valor_desconto=0,
    valor_comissao=0,
    valor_tarifa_fixa=0,
    valor_taxas_outros=0,
    valor_coparticipacao_frete=None,
    valor_repasse_previsto=0,
    taxas=None,
    observacoes=None
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

        canal_id = int(
            canal_id
        )

        pedido_externo = str(
            pedido_externo or ""
        ).strip()

        if not pedido_externo:

            raise Exception(
                "Informe o número do pedido do marketplace."
            )

        if not itens:

            raise Exception(
                "Informe pelo menos um produto no pedido."
            )

        # ----------------------------------------------------
        # VALIDAR CANAL
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                codigo,
                nome,
                ativo
            FROM marketplace_canais
            WHERE id = %s
            FOR UPDATE
            """,
            (
                canal_id,
            )
        )

        canal = cursor.fetchone()

        if canal is None:

            raise Exception(
                "Marketplace não encontrado."
            )

        if canal[3] is False:

            raise Exception(
                "O marketplace selecionado está inativo."
            )

        # ----------------------------------------------------
        # EVITAR PEDIDO DUPLICADO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT id
            FROM marketplace_pedidos
            WHERE
                canal_id = %s
                AND pedido_externo = %s
            LIMIT 1
            """,
            (
                canal_id,
                pedido_externo
            )
        )

        if cursor.fetchone() is not None:

            raise Exception(
                "Este pedido já está cadastrado para "
                "este marketplace."
            )

        # ----------------------------------------------------
        # VALIDAR CLIENTE
        # ----------------------------------------------------

        if cliente_id is not None:

            cliente_id = int(
                cliente_id
            )

            cursor.execute(
                """
                SELECT id
                FROM clientes
                WHERE id = %s
                LIMIT 1
                """,
                (
                    cliente_id,
                )
            )

            if cursor.fetchone() is None:

                raise Exception(
                    "Cliente não encontrado."
                )

        # ----------------------------------------------------
        # VALIDAR ITENS E CALCULAR VALORES
        # ----------------------------------------------------

        itens_validados = []
        valor_produtos = 0.0
        custo_total_pedido = 0.0

        for item in itens:

            produto_id = int(
                item["produto_id"]
            )

            quantidade = float(
                item.get(
                    "quantidade",
                    1
                ) or 1
            )

            valor_unitario = float(
                item.get(
                    "valor_unitario",
                    0
                ) or 0
            )

            if quantidade <= 0:

                raise Exception(
                    "A quantidade do produto deve ser "
                    "maior que zero."
                )

            if valor_unitario < 0:

                raise Exception(
                    "O valor unitário do produto não pode "
                    "ser negativo."
                )

            cursor.execute(
                """
                SELECT
                    id,
                    nome,
                    custo,
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
                nome_produto,
                custo_produto,
                produto_ativo
            ) = produto

            if produto_ativo is False:

                raise Exception(
                    f"O produto '{nome_produto}' está inativo."
                )

            custo_unitario = float(
                custo_produto or 0
            )

            valor_total_item = round(
                quantidade * valor_unitario,
                2
            )

            custo_total_item = round(
                quantidade * custo_unitario,
                2
            )

            valor_produtos += valor_total_item
            custo_total_pedido += custo_total_item

            itens_validados.append(
                {
                    "produto_id": produto_id,

                    "sku_marketplace": item.get(
                        "sku_marketplace"
                    ),

                    "codigo_anuncio": item.get(
                        "codigo_anuncio"
                    ),

                    "descricao": (
                        item.get("descricao")
                        or nome_produto
                    ),

                    "quantidade": quantidade,

                    "valor_unitario": valor_unitario,

                    "valor_total": valor_total_item,

                    "custo_unitario": custo_unitario,

                    "custo_total": custo_total_item
                }
            )

        valor_produtos = round(
            valor_produtos,
            2
        )

        custo_total_pedido = round(
            custo_total_pedido,
            2
        )

        valor_frete_cliente = round(
            float(
                valor_frete_cliente or 0
            ),
            2
        )

        valor_desconto = round(
            float(
                valor_desconto or 0
            ),
            2
        )

        valor_comissao = round(
            float(
                valor_comissao or 0
            ),
            2
        )

        valor_tarifa_fixa = round(
            float(
                valor_tarifa_fixa or 0
            ),
            2
        )

        valor_taxas_outros = round(
            float(
                valor_taxas_outros or 0
            ),
            2
        )

        valor_repasse_previsto = round(
            float(
                valor_repasse_previsto or 0
            ),
            2
        )

        if valor_coparticipacao_frete is not None:

            valor_coparticipacao_frete = round(
                float(
                    valor_coparticipacao_frete
                ),
                2
            )

        valor_total_cliente = round(
            valor_produtos
            +
            valor_frete_cliente
            -
            valor_desconto,
            2
        )

        # ----------------------------------------------------
        # CRIAR PEDIDO
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO marketplace_pedidos (
                canal_id,
                pedido_externo,
                cliente_id,
                data_pedido,
                data_aprovacao,
                status_pedido,
                status_fiscal,
                status_envio,
                status_repasse,
                forma_pagamento,
                valor_produtos,
                valor_frete_cliente,
                valor_desconto,
                valor_total_cliente,
                valor_comissao,
                valor_tarifa_fixa,
                valor_taxas_outros,
                valor_coparticipacao_frete,
                valor_repasse_previsto,
                observacoes
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                'NOVO',
                'AGUARDANDO_NFE',
                'AGUARDANDO',
                'AGUARDANDO',
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
                %s
            )
            RETURNING id
            """,
            (
                canal_id,
                pedido_externo,
                cliente_id,
                data_pedido,
                data_aprovacao,
                forma_pagamento,
                valor_produtos,
                valor_frete_cliente,
                valor_desconto,
                valor_total_cliente,
                valor_comissao,
                valor_tarifa_fixa,
                valor_taxas_outros,
                valor_coparticipacao_frete,
                valor_repasse_previsto,
                observacoes
            )
        )

        pedido_id = int(
            cursor.fetchone()[0]
        )

        # ----------------------------------------------------
        # ITENS
        # ----------------------------------------------------

        for item in itens_validados:

            cursor.execute(
                """
                INSERT INTO marketplace_pedido_itens (
                    pedido_id,
                    produto_id,
                    sku_marketplace,
                    codigo_anuncio,
                    descricao,
                    quantidade,
                    valor_unitario,
                    valor_total,
                    custo_unitario,
                    custo_total
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
                    %s
                )
                """,
                (
                    pedido_id,
                    item["produto_id"],
                    item["sku_marketplace"],
                    item["codigo_anuncio"],
                    item["descricao"],
                    item["quantidade"],
                    item["valor_unitario"],
                    item["valor_total"],
                    item["custo_unitario"],
                    item["custo_total"]
                )
            )

        # ----------------------------------------------------
        # TAXAS DETALHADAS
        # ----------------------------------------------------

        for taxa in (
            taxas or []
        ):

            cursor.execute(
                """
                INSERT INTO marketplace_taxas (
                    pedido_id,
                    tipo,
                    descricao,
                    percentual,
                    valor,
                    responsabilidade
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    pedido_id,
                    taxa.get(
                        "tipo",
                        "OUTRA"
                    ),

                    taxa.get(
                        "descricao"
                    ),

                    taxa.get(
                        "percentual"
                    ),

                    float(
                        taxa.get(
                            "valor",
                            0
                        ) or 0
                    ),

                    taxa.get(
                        "responsabilidade"
                    )
                )
            )

        # ----------------------------------------------------
        # REPASSE PREVISTO
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO marketplace_repasses (
                pedido_id,
                valor_previsto,
                status
            )
            VALUES (
                %s,
                %s,
                'PENDENTE'
            )
            """,
            (
                pedido_id,
                valor_repasse_previsto
            )
        )

        # ----------------------------------------------------
        # EVENTO INICIAL
        # ----------------------------------------------------

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
                'PEDIDO_CADASTRADO',
                'NOVO',
                %s,
                'ERP'
            )
            """,
            (
                pedido_id,
                (
                    f"Pedido {pedido_externo} "
                    "cadastrado manualmente no ERP."
                )
            )
        )

        # ----------------------------------------------------
        # RESULTADO ECONÔMICO PRELIMINAR
        # ----------------------------------------------------

        resultado_estimado = round(
            valor_repasse_previsto
            -
            custo_total_pedido,
            2
        )

        conn.commit()

        return {
            "sucesso": True,

            "pedido_id": pedido_id,

            "valor_produtos": valor_produtos,

            "valor_total_cliente": valor_total_cliente,

            "custo_total": custo_total_pedido,

            "valor_repasse_previsto": (
                valor_repasse_previsto
            ),

            "resultado_estimado": resultado_estimado
        }

    except Exception as erro:

        conn.rollback()

        print(
            "\n"
            +
            "=" * 80
        )

        print(
            "ERRO AO REGISTRAR PEDIDO DE MARKETPLACE"
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
# LISTAR PEDIDOS
# ============================================================

def listar_pedidos_marketplace(
    canal_id=None
):

    conn = conectar()

    if conn is None:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                mp.id,

                mc.codigo
                    AS marketplace_codigo,

                mc.nome
                    AS marketplace,

                mp.pedido_externo,

                c.nome
                    AS cliente,

                mp.data_pedido,

                mp.status_pedido,
                mp.status_fiscal,
                mp.status_envio,
                mp.status_repasse,

                mp.valor_produtos,
                mp.valor_frete_cliente,
                mp.valor_desconto,
                mp.valor_total_cliente,

                mp.valor_comissao,
                mp.valor_tarifa_fixa,
                mp.valor_taxas_outros,

                mp.valor_repasse_previsto,
                mp.valor_repasse_recebido,

                COALESCE(
                    (
                        SELECT SUM(
                            mpi.custo_total
                        )
                        FROM marketplace_pedido_itens mpi
                        WHERE mpi.pedido_id = mp.id
                    ),
                    0
                ) AS custo_produtos,

                mp.valor_repasse_previsto
                -
                COALESCE(
                    (
                        SELECT SUM(
                            mpi.custo_total
                        )
                        FROM marketplace_pedido_itens mpi
                        WHERE mpi.pedido_id = mp.id
                    ),
                    0
                ) AS resultado_estimado,

                mp.numero_nfe,
                mp.serie_nfe,
                mp.chave_nfe,

                mp.criado_em

            FROM marketplace_pedidos mp

            INNER JOIN marketplace_canais mc
                ON mc.id = mp.canal_id

            LEFT JOIN clientes c
                ON c.id = mp.cliente_id
        """

        params = []

        if canal_id is not None:

            query += """
                WHERE mp.canal_id = %s
            """

            params.append(
                int(canal_id)
            )

        query += """
            ORDER BY
                mp.data_pedido DESC NULLS LAST,
                mp.id DESC
        """

        return pd.read_sql(
            query,
            conn,
            params=(
                params
                if params
                else None
            )
        )

    except Exception as erro:

        print(
            "Erro ao listar pedidos de marketplace:",
            erro
        )

        return pd.DataFrame()

    finally:

        conn.close()


# ============================================================
# CREDENCIAIS OAUTH DOS MARKETPLACES
# ============================================================

def salvar_credenciais_marketplace(
    canal_id,
    access_token,
    refresh_token=None,
    token_type=None,
    access_token_expira_em=None,
    autorizado_em=None,
    ultima_renovacao_em=None,
    tenant_id=None,
    tenant_nome=None,
    scopes=None,
    ativo=True,
):
    """
    Salva ou atualiza credenciais OAuth de um marketplace.

    Access token e refresh token sao criptografados antes
    de serem enviados ao banco.

    Se refresh_token for None ou vazio durante uma atualizacao,
    o refresh token ja armazenado sera preservado.
    """

    access_token = str(
        access_token or ""
    ).strip()

    if not access_token:
        raise ValueError(
            "O access token e obrigatorio."
        )

    access_token_criptografado = (
        criptografar_texto(access_token)
    )

    refresh_token = str(
        refresh_token or ""
    ).strip()

    refresh_token_criptografado = None

    if refresh_token:
        refresh_token_criptografado = (
            criptografar_texto(refresh_token)
        )

    conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO marketplace_credenciais (
                canal_id,
                access_token_criptografado,
                refresh_token_criptografado,
                token_type,
                access_token_expira_em,
                autorizado_em,
                ultima_renovacao_em,
                tenant_id,
                tenant_nome,
                scopes,
                ativo,
                atualizado_em
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (canal_id)
            DO UPDATE SET
                access_token_criptografado =
                    EXCLUDED.access_token_criptografado,

                refresh_token_criptografado =
                    COALESCE(
                        EXCLUDED.refresh_token_criptografado,
                        marketplace_credenciais.refresh_token_criptografado
                    ),

                token_type =
                    EXCLUDED.token_type,

                access_token_expira_em =
                    EXCLUDED.access_token_expira_em,

                autorizado_em =
                    COALESCE(
                        EXCLUDED.autorizado_em,
                        marketplace_credenciais.autorizado_em
                    ),

                ultima_renovacao_em =
                    EXCLUDED.ultima_renovacao_em,

                tenant_id =
                    COALESCE(
                        EXCLUDED.tenant_id,
                        marketplace_credenciais.tenant_id
                    ),

                tenant_nome =
                    COALESCE(
                        EXCLUDED.tenant_nome,
                        marketplace_credenciais.tenant_nome
                    ),

                scopes =
                    COALESCE(
                        EXCLUDED.scopes,
                        marketplace_credenciais.scopes
                    ),

                ativo =
                    EXCLUDED.ativo,

                atualizado_em =
                    CURRENT_TIMESTAMP

            RETURNING id
            """,
            (
                int(canal_id),
                access_token_criptografado,
                refresh_token_criptografado,
                token_type,
                access_token_expira_em,
                autorizado_em,
                ultima_renovacao_em,
                tenant_id,
                tenant_nome,
                scopes,
                bool(ativo),
            )
        )

        credencial_id = cursor.fetchone()[0]

        conn.commit()

        return credencial_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


def buscar_credenciais_marketplace(canal_id):
    """
    Busca as credenciais de um marketplace e descriptografa
    os tokens somente no momento de uso pelo ERP.
    """

    conn = conectar()

    if conn is None:
        return None

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT
                id,
                canal_id,
                access_token_criptografado,
                refresh_token_criptografado,
                token_type,
                access_token_expira_em,
                autorizado_em,
                ultima_renovacao_em,
                tenant_id,
                tenant_nome,
                scopes,
                ativo,
                criado_em,
                atualizado_em
            FROM marketplace_credenciais
            WHERE canal_id = %s
            LIMIT 1
            """,
            (
                int(canal_id),
            )
        )

        linha = cursor.fetchone()

        if not linha:
            return None

        return {
            "id": linha[0],
            "canal_id": linha[1],

            "access_token": descriptografar_texto(
                linha[2]
            ),

            "refresh_token": descriptografar_texto(
                linha[3]
            ),

            "token_type": linha[4],
            "access_token_expira_em": linha[5],
            "autorizado_em": linha[6],
            "ultima_renovacao_em": linha[7],
            "tenant_id": linha[8],
            "tenant_nome": linha[9],
            "scopes": linha[10],
            "ativo": linha[11],
            "criado_em": linha[12],
            "atualizado_em": linha[13],
        }

    finally:
        cursor.close()
        conn.close()


def desativar_credenciais_marketplace(canal_id):
    """
    Desativa a autorizacao armazenada sem apagar o historico.
    """

    conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE marketplace_credenciais
            SET
                ativo = FALSE,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE canal_id = %s
            """,
            (
                int(canal_id),
            )
        )

        alterados = cursor.rowcount

        conn.commit()

        return alterados > 0

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


# ============================================================
# OAUTH STATE - SEGURANCA
# ============================================================

def _hash_oauth_state(state):

    state = str(
        state or ""
    ).strip()

    if not state:
        raise ValueError(
            "OAuth state nao pode ser vazio."
        )

    return hashlib.sha256(
        state.encode("utf-8")
    ).hexdigest()


def registrar_oauth_state(
    canal_id,
    state,
    validade_minutos=10,
):

    canal_id = int(canal_id)

    validade_minutos = int(
        validade_minutos
    )

    if validade_minutos <= 0:
        raise ValueError(
            "Validade do OAuth state deve "
            "ser maior que zero."
        )

    state_hash = _hash_oauth_state(
        state
    )

    expira_em = (
        datetime.utcnow()
        + timedelta(
            minutes=validade_minutos
        )
    )

    conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    cursor = conn.cursor()

    try:

        # Remove states antigos ja expirados.
        cursor.execute(
            """
            DELETE FROM marketplace_oauth_states
            WHERE expira_em < CURRENT_TIMESTAMP
            """
        )

        cursor.execute(
            """
            INSERT INTO marketplace_oauth_states (
                canal_id,
                state_hash,
                expira_em
            )
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                canal_id,
                state_hash,
                expira_em,
            )
        )

        registro_id = cursor.fetchone()[0]

        conn.commit()

        return registro_id

    except Exception:

        conn.rollback()
        raise

    finally:

        cursor.close()
        conn.close()


def consumir_oauth_state(
    canal_id,
    state,
):

    canal_id = int(canal_id)

    state_hash = _hash_oauth_state(
        state
    )

    conn = conectar()

    if conn is None:
        raise RuntimeError(
            "Nao foi possivel conectar ao banco."
        )

    cursor = conn.cursor()

    try:

        # UPDATE condicional torna o consumo atomico:
        # somente state correto, nao usado e nao expirado
        # pode ser marcado como utilizado.
        cursor.execute(
            """
            UPDATE marketplace_oauth_states
            SET usado_em = CURRENT_TIMESTAMP
            WHERE canal_id = %s
              AND state_hash = %s
              AND usado_em IS NULL
              AND expira_em >= CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                canal_id,
                state_hash,
            )
        )

        registro = cursor.fetchone()

        conn.commit()

        return bool(registro)

    except Exception:

        conn.rollback()
        raise

    finally:

        cursor.close()
        conn.close()
