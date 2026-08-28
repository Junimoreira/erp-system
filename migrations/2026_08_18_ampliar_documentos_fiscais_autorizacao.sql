-- ============================================================
-- AMPLIAR DOCUMENTOS FISCAIS PARA PÓS-AUTORIZAÇÃO
-- NF-e / NFC-e EMITIDAS PELO ERP
-- ============================================================

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS venda_id INTEGER;

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS cstat VARCHAR(10);

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS xmotivo TEXT;

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS digest_value TEXT;

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS data_autorizacao TIMESTAMP;

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS xml_assinado TEXT;

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS xml_processado TEXT;

ALTER TABLE documentos_fiscais
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP;


-- ============================================================
-- FK OPCIONAL PARA A VENDA
--
-- A venda pode ser NULL porque a tabela também guarda
-- documentos importados de terceiros.
-- ============================================================

DO $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_documentos_fiscais_venda'
    ) THEN

        ALTER TABLE documentos_fiscais
            ADD CONSTRAINT fk_documentos_fiscais_venda
            FOREIGN KEY (venda_id)
            REFERENCES vendas(id)
            ON DELETE SET NULL;

    END IF;

END
$$;


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_documentos_fiscais_venda
ON documentos_fiscais (
    venda_id
);

CREATE INDEX IF NOT EXISTS
    idx_documentos_fiscais_status
ON documentos_fiscais (
    status
);

CREATE INDEX IF NOT EXISTS
    idx_documentos_fiscais_modelo_serie_numero
ON documentos_fiscais (
    modelo,
    serie,
    numero
);