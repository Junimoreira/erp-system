CREATE TABLE IF NOT EXISTS erp_cancelamentos_vendas (
    venda_id BIGINT PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    usuario TEXT NOT NULL,
    motivo TEXT NOT NULL,
    plano JSONB NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
