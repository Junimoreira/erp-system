-- ============================================================
-- AMPLIAR CONFIGURAÇÃO FISCAL - ENDEREÇO DO EMITENTE
--
-- Necessário para geração do grupo <enderEmit> da NF-e/NFC-e.
--
-- NÃO altera vendas.
-- NÃO altera produtos.
-- NÃO transmite documentos fiscais.
-- ============================================================


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS logradouro VARCHAR(255);


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS numero VARCHAR(60);


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS complemento VARCHAR(255);


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS bairro VARCHAR(120);


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS cidade VARCHAR(120);


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS cep VARCHAR(20);


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS codigo_pais VARCHAR(10)
        DEFAULT '1058';


ALTER TABLE configuracoes_fiscais
    ADD COLUMN IF NOT EXISTS pais VARCHAR(60)
        DEFAULT 'BRASIL';