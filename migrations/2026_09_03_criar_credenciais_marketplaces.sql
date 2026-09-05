-- Credenciais OAuth dos marketplaces
-- Criada em 03/09/2026
--
-- IMPORTANTE:
-- access_token e refresh_token devem ser gravados
-- exclusivamente em formato criptografado pelo ERP.

CREATE TABLE IF NOT EXISTS marketplace_credenciais (
    id SERIAL PRIMARY KEY,

    canal_id INTEGER NOT NULL
        REFERENCES marketplace_canais(id)
        ON DELETE CASCADE,

    access_token_criptografado TEXT,

    refresh_token_criptografado TEXT,

    token_type VARCHAR(30),

    access_token_expira_em TIMESTAMP,

    autorizado_em TIMESTAMP,

    ultima_renovacao_em TIMESTAMP,

    tenant_id VARCHAR(255),

    tenant_nome VARCHAR(255),

    scopes TEXT,

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_marketplace_credencial_canal
        UNIQUE (canal_id)
);

CREATE INDEX IF NOT EXISTS
    idx_marketplace_credenciais_canal
ON marketplace_credenciais(canal_id);

CREATE INDEX IF NOT EXISTS
    idx_marketplace_credenciais_ativo
ON marketplace_credenciais(ativo);
