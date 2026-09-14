-- Protecao contra duplicidade de numeracao fiscal
--
-- Garante que nao possam existir dois documentos com
-- o mesmo modelo, serie e numero.

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_documentos_fiscais_modelo_serie_numero
ON documentos_fiscais (
    modelo,
    serie,
    numero
);
