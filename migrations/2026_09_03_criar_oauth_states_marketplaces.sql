-- Estados temporarios de seguranca OAuth
-- Marketplace / Magalu
--
-- O valor original do state nunca deve ser armazenado.
-- Apenas seu SHA-256 e persistido.

CREATE TABLE IF NOT EXISTS marketplace_oauth_states (
    id SERIAL PRIMARY KEY,

    canal_id INTEGER NOT NULL
        REFERENCES marketplace_canais(id)
        ON DELETE CASCADE,

    state_hash CHAR(64) NOT NULL UNIQUE,

    expira_em TIMESTAMP NOT NULL,

    usado_em TIMESTAMP,

    criado_em TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
    idx_marketplace_oauth_states_canal
ON marketplace_oauth_states(canal_id);

CREATE INDEX IF NOT EXISTS
    idx_marketplace_oauth_states_expira
ON marketplace_oauth_states(expira_em);
