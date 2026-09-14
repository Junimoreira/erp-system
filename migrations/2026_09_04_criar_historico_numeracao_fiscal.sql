-- Historico de ajustes/sincronizacoes da numeracao fiscal
-- Criado em 04/09/2026

CREATE TABLE IF NOT EXISTS historico_numeracao_fiscal (
    id SERIAL PRIMARY KEY,

    configuracao_fiscal_id INTEGER NOT NULL
        REFERENCES configuracoes_fiscais(id),

    ambiente INTEGER NOT NULL,

    modelo INTEGER NOT NULL,

    serie INTEGER NOT NULL,

    numero_anterior INTEGER NOT NULL,

    numero_novo INTEGER NOT NULL,

    motivo TEXT NOT NULL,

    chave_referencia VARCHAR(44),

    protocolo_referencia VARCHAR(100),

    origem VARCHAR(50) NOT NULL
        DEFAULT 'ERP',

    criado_em TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS
    idx_historico_numeracao_fiscal_data
ON historico_numeracao_fiscal(criado_em);

CREATE INDEX IF NOT EXISTS
    idx_historico_numeracao_fiscal_modelo_serie
ON historico_numeracao_fiscal(
    modelo,
    serie
);
