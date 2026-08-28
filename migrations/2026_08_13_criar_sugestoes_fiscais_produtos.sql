CREATE TABLE IF NOT EXISTS sugestoes_fiscais_produtos (

    id SERIAL PRIMARY KEY,

    produto_id INTEGER
        REFERENCES produtos(id)
        ON DELETE SET NULL,

    documento_fiscal_id INTEGER
        REFERENCES documentos_fiscais(id)
        ON DELETE SET NULL,

    chave_acesso VARCHAR(44),

    numero_nota INTEGER,

    numero_item INTEGER,

    codigo_xml VARCHAR(60),

    codigo_barras_xml VARCHAR(30),

    descricao_xml TEXT,

    ncm_xml VARCHAR(10),

    cest_xml VARCHAR(10),

    cfop_historico VARCHAR(4),

    csosn_historico VARCHAR(4),

    perfil_icms_sugerido VARCHAR(30),

    cfop_saida_interna_sugerido VARCHAR(4),

    csosn_saida_interna_sugerido VARCHAR(4),

    confianca_historico VARCHAR(20),

    confianca_vinculo VARCHAR(20),

    encontrado_por VARCHAR(30),

    apto_para_aplicar BOOLEAN DEFAULT FALSE,

    motivo_bloqueio TEXT,

    status VARCHAR(20) DEFAULT 'PENDENTE',
    -- PENDENTE
    -- APROVADO
    -- REJEITADO
    -- APLICADO

    observacao_revisao TEXT,

    revisado_em TIMESTAMP,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS
idx_sugestoes_fiscais_produto
ON sugestoes_fiscais_produtos(produto_id);


CREATE INDEX IF NOT EXISTS
idx_sugestoes_fiscais_status
ON sugestoes_fiscais_produtos(status);


CREATE INDEX IF NOT EXISTS
idx_sugestoes_fiscais_chave
ON sugestoes_fiscais_produtos(chave_acesso);