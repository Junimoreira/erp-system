-- ============================================================
-- REGRAS FISCAIS
-- VERDE INFÂNCIA
-- ============================================================

CREATE TABLE IF NOT EXISTS regras_fiscais (

    id SERIAL PRIMARY KEY,

    nome VARCHAR(120) NOT NULL,

    tipo_operacao VARCHAR(20) NOT NULL,
    -- ENTRADA
    -- SAIDA

    finalidade VARCHAR(30),
    -- REVENDA
    -- USO_CONSUMO
    -- ATIVO
    -- etc.

    uf_origem CHAR(2),

    uf_destino CHAR(2),

    interestadual BOOLEAN,

    cfop_origem VARCHAR(4),

    cfop_destino VARCHAR(4),

    ncm_prefixo VARCHAR(10),

    cest VARCHAR(10),

    cst_origem VARCHAR(3),

    csosn_destino VARCHAR(4),

    cst_destino VARCHAR(3),

    cst_ibs_cbs VARCHAR(10),

    classificacao_tributaria VARCHAR(20),

    prioridade INTEGER DEFAULT 100,

    confianca VARCHAR(20) DEFAULT 'MEDIA',

    requer_revisao BOOLEAN DEFAULT TRUE,

    observacao TEXT,

    ativo BOOLEAN DEFAULT TRUE,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS
idx_regras_fiscais_operacao
ON regras_fiscais(tipo_operacao);


CREATE INDEX IF NOT EXISTS
idx_regras_fiscais_cfop
ON regras_fiscais(cfop_origem);


CREATE INDEX IF NOT EXISTS
idx_regras_fiscais_ncm
ON regras_fiscais(ncm_prefixo);