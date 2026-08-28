-- ============================================================
-- CLASSIFICAÇÕES IBS / CBS
--
-- Objetivo:
-- Manter no banco uma tabela versionada para CST IBS/CBS
-- e cClassTrib.
--
-- IMPORTANTE:
-- - NÃO altera produtos
-- - NÃO define tributação automaticamente
-- - NÃO transmite documentos
-- - A origem dos dados deve ser tabela oficial versionada
-- ============================================================


CREATE TABLE IF NOT EXISTS classificacoes_ibs_cbs (

    id SERIAL PRIMARY KEY,

    cst VARCHAR(3) NOT NULL,

    cclass_trib VARCHAR(6) NOT NULL,

    descricao TEXT,

    versao_fonte VARCHAR(50),

    fonte VARCHAR(100),

    data_inicio_vigencia DATE,

    data_fim_vigencia DATE,

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMP WITHOUT TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    atualizado_em TIMESTAMP WITHOUT TIME ZONE
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_classificacoes_ibs_cbs
        UNIQUE (
            cst,
            cclass_trib,
            versao_fonte
        ),

    CONSTRAINT ck_classificacoes_ibs_cbs_cst
        CHECK (
            cst ~ '^[0-9]{3}$'
        ),

    CONSTRAINT ck_classificacoes_ibs_cbs_cclass
        CHECK (
            cclass_trib ~ '^[0-9]{6}$'
        )
);


CREATE INDEX IF NOT EXISTS
    idx_classificacoes_ibs_cbs_cclass
ON classificacoes_ibs_cbs (
    cclass_trib
);


CREATE INDEX IF NOT EXISTS
    idx_classificacoes_ibs_cbs_cst
ON classificacoes_ibs_cbs (
    cst
);


CREATE INDEX IF NOT EXISTS
    idx_classificacoes_ibs_cbs_ativo
ON classificacoes_ibs_cbs (
    ativo
);