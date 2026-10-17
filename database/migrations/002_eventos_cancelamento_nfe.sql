CREATE TABLE IF NOT EXISTS erp_cancelamentos_nfe (
    chave_acesso VARCHAR(44) NOT NULL,
    ambiente SMALLINT NOT NULL CHECK (ambiente IN (1,2)),
    documento_id BIGINT NOT NULL,
    usuario_id BIGINT NOT NULL,
    usuario TEXT NOT NULL,
    justificativa TEXT NOT NULL,
    xml_assinado TEXT NOT NULL,
    resposta TEXT,
    resposta_inicial TEXT,
    protocolo_evento TEXT,
    estado TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chave_acesso, ambiente)
);
