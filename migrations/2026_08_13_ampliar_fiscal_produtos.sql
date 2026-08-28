-- ============================================================
-- AMPLIAÇÃO DO CADASTRO FISCAL DOS PRODUTOS
-- VERDE INFÂNCIA
--
-- IMPORTANTE:
-- Nenhum campo abaixo altera automaticamente tributação.
-- Os dados serão preenchidos posteriormente por análise
-- e confirmação.
-- ============================================================


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS origem_mercadoria VARCHAR(1);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS perfil_icms VARCHAR(30);

-- Valores previstos inicialmente:
--
-- NORMAL
-- ST_SUBSTITUIDO
-- ISENTO
-- NAO_TRIBUTADO
-- IMUNE
-- OUTROS


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS cfop_saida_interna VARCHAR(4);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS csosn_saida_interna VARCHAR(4);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS cfop_saida_interestadual VARCHAR(4);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS csosn_saida_interestadual VARCHAR(4);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS cst_ibs_cbs_saida VARCHAR(10);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS classificacao_tributaria_saida VARCHAR(20);


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS fiscal_revisado BOOLEAN DEFAULT FALSE;


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS fiscal_fonte VARCHAR(30);

-- Possíveis fontes:
--
-- XML_HISTORICO
-- XML_FORNECEDOR
-- CONTADOR
-- MANUAL
-- MOTOR_FISCAL


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS fiscal_confianca VARCHAR(20);

-- ALTA
-- MEDIA
-- BAIXA


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS fiscal_observacao TEXT;


ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS fiscal_atualizado_em TIMESTAMP;


CREATE INDEX IF NOT EXISTS
idx_produtos_perfil_icms
ON produtos(perfil_icms);


CREATE INDEX IF NOT EXISTS
idx_produtos_fiscal_revisado
ON produtos(fiscal_revisado);