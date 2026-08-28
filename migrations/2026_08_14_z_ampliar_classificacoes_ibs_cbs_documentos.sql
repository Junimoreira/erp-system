-- ============================================================
-- AMPLIAR CLASSIFICAÇÕES IBS / CBS
--
-- Adiciona indicadores oficiais de utilização em:
-- - NF-e  modelo 55
-- - NFC-e modelo 65
--
-- NÃO altera produtos.
-- NÃO altera vendas.
-- NÃO transmite documentos.
-- ============================================================


ALTER TABLE classificacoes_ibs_cbs
    ADD COLUMN IF NOT EXISTS ind_nfe BOOLEAN;


ALTER TABLE classificacoes_ibs_cbs
    ADD COLUMN IF NOT EXISTS ind_nfce BOOLEAN;


CREATE INDEX IF NOT EXISTS
    idx_classificacoes_ibs_cbs_ind_nfe
ON classificacoes_ibs_cbs (
    ind_nfe
);


CREATE INDEX IF NOT EXISTS
    idx_classificacoes_ibs_cbs_ind_nfce
ON classificacoes_ibs_cbs (
    ind_nfce
);