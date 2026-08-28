ALTER TABLE configuracoes_fiscais
ADD COLUMN IF NOT EXISTS certificado_pfx_caminho TEXT;

ALTER TABLE configuracoes_fiscais
ADD COLUMN IF NOT EXISTS certificado_atualizado_em TIMESTAMP;