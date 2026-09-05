-- ============================================================
-- ERP VERDE INFÂNCIA
-- MÓDULO MARKETPLACES
-- Estrutura genérica para Magalu, Mercado Livre, Shopee e outros
-- ============================================================


-- ============================================================
-- 1. CANAIS / MARKETPLACES
-- ============================================================
CREATE TABLE IF NOT EXISTS marketplace_canais (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    integracao_api BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


INSERT INTO marketplace_canais (
    codigo,
    nome,
    ativo,
    integracao_api
)
VALUES
    ('MAGALU', 'Magazine Luiza', TRUE, FALSE),
    ('MERCADO_LIVRE', 'Mercado Livre', TRUE, FALSE),
    ('SHOPEE', 'Shopee', TRUE, FALSE)
ON CONFLICT (codigo) DO NOTHING;


-- ============================================================
-- 2. PEDIDOS
-- ============================================================
CREATE TABLE IF NOT EXISTS marketplace_pedidos (
    id SERIAL PRIMARY KEY,

    canal_id INTEGER NOT NULL
        REFERENCES marketplace_canais(id),

    pedido_externo VARCHAR(120) NOT NULL,

    cliente_id INTEGER
        REFERENCES clientes(id),

    venda_id INTEGER
        REFERENCES vendas(id),

    data_pedido TIMESTAMP,
    data_aprovacao TIMESTAMP,

    status_pedido VARCHAR(50) NOT NULL DEFAULT 'NOVO',
    status_fiscal VARCHAR(50) NOT NULL DEFAULT 'AGUARDANDO_NFE',
    status_envio VARCHAR(50) NOT NULL DEFAULT 'AGUARDANDO',
    status_repasse VARCHAR(50) NOT NULL DEFAULT 'AGUARDANDO',

    forma_pagamento VARCHAR(50),

    valor_produtos NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_frete_cliente NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_desconto NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_total_cliente NUMERIC(14,2) NOT NULL DEFAULT 0,

    valor_comissao NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_tarifa_fixa NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_taxas_outros NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_coparticipacao_frete NUMERIC(14,2),

    valor_repasse_previsto NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_repasse_recebido NUMERIC(14,2),

    numero_nfe INTEGER,
    serie_nfe INTEGER,
    chave_nfe VARCHAR(44),
    protocolo_nfe VARCHAR(30),

    data_despacho TIMESTAMP,
    codigo_rastreio VARCHAR(120),

    observacoes TEXT,

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_marketplace_pedido
        UNIQUE (canal_id, pedido_externo)
);


-- ============================================================
-- 3. ITENS DO PEDIDO
-- ============================================================
CREATE TABLE IF NOT EXISTS marketplace_pedido_itens (
    id SERIAL PRIMARY KEY,

    pedido_id INTEGER NOT NULL
        REFERENCES marketplace_pedidos(id)
        ON DELETE CASCADE,

    produto_id INTEGER
        REFERENCES produtos(id),

    sku_marketplace VARCHAR(120),
    codigo_anuncio VARCHAR(120),

    descricao VARCHAR(255) NOT NULL,

    quantidade NUMERIC(14,4) NOT NULL DEFAULT 1,

    valor_unitario NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_total NUMERIC(14,2) NOT NULL DEFAULT 0,

    custo_unitario NUMERIC(14,2) NOT NULL DEFAULT 0,
    custo_total NUMERIC(14,2) NOT NULL DEFAULT 0,

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. TAXAS / AJUSTES DO MARKETPLACE
-- ============================================================
CREATE TABLE IF NOT EXISTS marketplace_taxas (
    id SERIAL PRIMARY KEY,

    pedido_id INTEGER NOT NULL
        REFERENCES marketplace_pedidos(id)
        ON DELETE CASCADE,

    tipo VARCHAR(50) NOT NULL,
    descricao VARCHAR(255),

    percentual NUMERIC(10,4),
    valor NUMERIC(14,2) NOT NULL DEFAULT 0,

    responsabilidade VARCHAR(30),

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 5. REPASSES
-- ============================================================
CREATE TABLE IF NOT EXISTS marketplace_repasses (
    id SERIAL PRIMARY KEY,

    pedido_id INTEGER NOT NULL
        REFERENCES marketplace_pedidos(id),

    data_prevista DATE,
    data_recebimento DATE,

    valor_previsto NUMERIC(14,2) NOT NULL DEFAULT 0,
    valor_recebido NUMERIC(14,2),

    status VARCHAR(30) NOT NULL DEFAULT 'PENDENTE',

    conta_bancaria_id INTEGER,

    identificador_externo VARCHAR(120),

    observacoes TEXT,

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 6. EVENTOS / HISTÓRICO
-- ============================================================
CREATE TABLE IF NOT EXISTS marketplace_eventos (
    id SERIAL PRIMARY KEY,

    pedido_id INTEGER NOT NULL
        REFERENCES marketplace_pedidos(id)
        ON DELETE CASCADE,

    tipo VARCHAR(50) NOT NULL,
    status VARCHAR(50),

    descricao TEXT,

    origem VARCHAR(30) NOT NULL DEFAULT 'ERP',

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_marketplace_pedidos_canal
    ON marketplace_pedidos(canal_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_pedidos_cliente
    ON marketplace_pedidos(cliente_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_pedidos_venda
    ON marketplace_pedidos(venda_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_pedidos_status
    ON marketplace_pedidos(status_pedido);

CREATE INDEX IF NOT EXISTS idx_marketplace_pedidos_fiscal
    ON marketplace_pedidos(status_fiscal);

CREATE INDEX IF NOT EXISTS idx_marketplace_pedidos_repasse
    ON marketplace_pedidos(status_repasse);

CREATE INDEX IF NOT EXISTS idx_marketplace_itens_pedido
    ON marketplace_pedido_itens(pedido_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_eventos_pedido
    ON marketplace_eventos(pedido_id);
