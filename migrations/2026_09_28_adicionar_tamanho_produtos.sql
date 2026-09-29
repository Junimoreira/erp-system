-- =========================================================
-- PRODUTOS - CAMPO TAMANHO
-- =========================================================
-- Adiciona o campo tamanho utilizado no cadastro, edicao,
-- busca e identificacao de produtos.
--
-- Campo opcional para manter compatibilidade com produtos
-- existentes que nao possuem tamanho.
-- =========================================================

ALTER TABLE produtos
ADD COLUMN IF NOT EXISTS tamanho VARCHAR(50);

COMMENT ON COLUMN produtos.tamanho IS
'Tamanho ou variacao do produto, quando aplicavel.';
