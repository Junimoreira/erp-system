ALTER TABLE itens_compra
ADD COLUMN IF NOT EXISTS cfop_fornecedor VARCHAR(4);

ALTER TABLE itens_compra
ADD COLUMN IF NOT EXISTS cfop_entrada VARCHAR(4);

COMMENT ON COLUMN itens_compra.cfop_fornecedor IS
'CFOP original informado no XML da NF-e do fornecedor.';

COMMENT ON COLUMN itens_compra.cfop_entrada IS
'CFOP de entrada utilizado na escrituracao da compra, apos classificacao e conferencia fiscal.';
