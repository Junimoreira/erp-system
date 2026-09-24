-- Adiciona CSOSN de origem ao motor de regras fiscais.
-- Permite distinguir CST e CSOSN recebidos do fornecedor.
--
-- Esta migration e idempotente e preserva regras historicas.

ALTER TABLE regras_fiscais
ADD COLUMN IF NOT EXISTS csosn_origem VARCHAR(4);
