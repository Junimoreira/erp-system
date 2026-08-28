-- ============================================================
-- MÓDULO FISCAL - VERDE INFÂNCIA
-- Estrutura inicial para NF-e / NFC-e
-- ============================================================


-- ============================================================
-- CONFIGURAÇÃO FISCAL DA EMPRESA
-- ============================================================
CREATE TABLE IF NOT EXISTS configuracoes_fiscais (

    id SERIAL PRIMARY KEY,

    cnpj VARCHAR(14) NOT NULL,
    razao_social VARCHAR(150) NOT NULL,
    nome_fantasia VARCHAR(150),

    inscricao_estadual VARCHAR(30),

    crt INTEGER,

    uf CHAR(2),
    codigo_municipio_ibge VARCHAR(7),

    ambiente INTEGER DEFAULT 2,
    -- 1 = produção
    -- 2 = homologação

    serie_nfe INTEGER DEFAULT 1,
    proximo_numero_nfe INTEGER DEFAULT 1,

    serie_nfce INTEGER DEFAULT 1,
    proximo_numero_nfce INTEGER DEFAULT 1,

    csc_nfce TEXT,
    csc_id_nfce VARCHAR(20),

    ativo BOOLEAN DEFAULT TRUE,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- DOCUMENTOS FISCAIS
-- NF-e modelo 55
-- NFC-e modelo 65
-- Entrada e saída
-- ============================================================
CREATE TABLE IF NOT EXISTS documentos_fiscais (

    id SERIAL PRIMARY KEY,

    chave_acesso VARCHAR(44) UNIQUE,

    modelo INTEGER NOT NULL,

    serie INTEGER,
    numero INTEGER,

    tipo_movimento VARCHAR(10),
    -- ENTRADA
    -- SAIDA

    finalidade INTEGER,

    ambiente INTEGER,

    natureza_operacao VARCHAR(150),

    data_emissao TIMESTAMP,

    emitente_cnpj VARCHAR(14),
    emitente_nome VARCHAR(200),
    emitente_uf CHAR(2),

    destinatario_documento VARCHAR(14),
    destinatario_nome VARCHAR(200),
    destinatario_uf CHAR(2),

    valor_produtos NUMERIC(14,2) DEFAULT 0,
    valor_frete NUMERIC(14,2) DEFAULT 0,
    valor_desconto NUMERIC(14,2) DEFAULT 0,
    valor_total NUMERIC(14,2) DEFAULT 0,

    protocolo VARCHAR(30),

    status VARCHAR(30) DEFAULT 'IMPORTADO',

    xml_original TEXT,

    origem_documento VARCHAR(30),
    -- FORNECEDOR
    -- ERP
    -- IMPORTACAO

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- ITENS DOS DOCUMENTOS FISCAIS
-- ============================================================
CREATE TABLE IF NOT EXISTS documentos_fiscais_itens (

    id SERIAL PRIMARY KEY,

    documento_fiscal_id INTEGER NOT NULL
        REFERENCES documentos_fiscais(id)
        ON DELETE CASCADE,

    numero_item INTEGER,

    codigo_produto VARCHAR(60),

    codigo_barras VARCHAR(30),

    descricao TEXT,

    ncm VARCHAR(10),
    cest VARCHAR(10),

    cfop VARCHAR(4),

    unidade VARCHAR(10),

    quantidade NUMERIC(15,4),

    valor_unitario NUMERIC(15,6),

    valor_produto NUMERIC(15,2),

    valor_desconto NUMERIC(15,2) DEFAULT 0,

    origem_icms VARCHAR(2),

    cst_icms VARCHAR(3),
    csosn VARCHAR(4),

    cst_pis VARCHAR(3),
    cst_cofins VARCHAR(3),

    cst_ibs_cbs VARCHAR(10),
    classificacao_tributaria VARCHAR(20),

    valor_ibs NUMERIC(15,2),
    valor_cbs NUMERIC(15,2),

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS
idx_documentos_fiscais_chave
ON documentos_fiscais(chave_acesso);


CREATE INDEX IF NOT EXISTS
idx_documentos_fiscais_emissao
ON documentos_fiscais(data_emissao);


CREATE INDEX IF NOT EXISTS
idx_documentos_fiscais_emitente
ON documentos_fiscais(emitente_cnpj);


CREATE INDEX IF NOT EXISTS
idx_documentos_fiscais_itens_documento
ON documentos_fiscais_itens(documento_fiscal_id);