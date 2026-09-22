ALTER TABLE compras
ADD COLUMN IF NOT EXISTS data_entrada DATE;

COMMENT ON COLUMN compras.data_entrada IS
'Data efetiva de entrada/recebimento da mercadoria na empresa. '
'Usada para competencia fiscal das operacoes de entrada.';
