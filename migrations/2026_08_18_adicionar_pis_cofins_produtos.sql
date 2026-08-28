-- ============================================================
-- PIS / COFINS - CONFIGURAÇÃO FISCAL DE SAÍDA DOS PRODUTOS
--
-- Não define CST automaticamente.
-- Não altera produtos existentes.
-- Não altera documentos fiscais.
-- ============================================================

ALTER TABLE produtos
    ADD COLUMN IF NOT EXISTS cst_pis_saida VARCHAR(2);

ALTER TABLE produtos
    ADD COLUMN IF NOT EXISTS aliquota_pis_saida NUMERIC(8,4);

ALTER TABLE produtos
    ADD COLUMN IF NOT EXISTS cst_cofins_saida VARCHAR(2);

ALTER TABLE produtos
    ADD COLUMN IF NOT EXISTS aliquota_cofins_saida NUMERIC(8,4);


COMMENT ON COLUMN produtos.cst_pis_saida IS
'CST do PIS utilizado na saída fiscal do produto.';

COMMENT ON COLUMN produtos.aliquota_pis_saida IS
'Alíquota percentual de PIS para saída, quando aplicável.';

COMMENT ON COLUMN produtos.cst_cofins_saida IS
'CST da COFINS utilizado na saída fiscal do produto.';

COMMENT ON COLUMN produtos.aliquota_cofins_saida IS
'Alíquota percentual de COFINS para saída, quando aplicável.';