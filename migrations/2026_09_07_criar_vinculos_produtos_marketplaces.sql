-- ============================================================
-- MARKETPLACES - VINCULO DE PRODUTOS POR CANAL
-- Data: 2026-09-07
-- ============================================================

CREATE TABLE IF NOT EXISTS marketplace_produto_vinculos (
    id SERIAL PRIMARY KEY,

    canal_id INTEGER NOT NULL
        REFERENCES marketplace_canais(id)
        ON DELETE CASCADE,

    produto_id INTEGER NOT NULL
        REFERENCES produtos(id),

    sku_marketplace VARCHAR(120) NOT NULL,
    codigo_anuncio VARCHAR(120),

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_marketplace_produto_sku
        UNIQUE (canal_id, sku_marketplace)
);

CREATE INDEX IF NOT EXISTS idx_marketplace_produto_vinculos_canal
    ON marketplace_produto_vinculos(canal_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_produto_vinculos_produto
    ON marketplace_produto_vinculos(produto_id);

CREATE INDEX IF NOT EXISTS idx_marketplace_produto_vinculos_ativo
    ON marketplace_produto_vinculos(ativo);
