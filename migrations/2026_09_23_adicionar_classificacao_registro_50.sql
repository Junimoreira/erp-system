-- Classificacao fiscal do item da compra para o Registro 50 do SINTEGRA.
--
-- Valores previstos pela aplicacao:
-- TRIBUTADA
-- ISENTA_NAO_TRIBUTADA
-- OUTRAS
-- PENDENTE
--
-- NULL preserva compras historicas ou fluxos que ainda nao passaram
-- pela conferencia fiscal especifica do SINTEGRA.

ALTER TABLE itens_compra
ADD COLUMN IF NOT EXISTS classificacao_registro_50 VARCHAR(30);

COMMENT ON COLUMN itens_compra.classificacao_registro_50 IS
'Classificacao da escrituracao do item para o Registro 50 do SINTEGRA: TRIBUTADA, ISENTA_NAO_TRIBUTADA, OUTRAS ou PENDENTE.';
