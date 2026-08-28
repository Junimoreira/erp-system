-- ============================================================
-- AMPLIAR SUGESTÕES FISCAIS
-- ORIGEM DA MERCADORIA
--
-- Objetivo:
-- Guardar a origem encontrada no XML histórico e a origem
-- sugerida para futura aplicação ao cadastro do produto.
--
-- IMPORTANTE:
-- Esta migration NÃO altera produtos.
-- Esta migration NÃO aprova sugestões.
-- Esta migration NÃO aplica configuração fiscal.
-- ============================================================


-- ============================================================
-- ORIGEM ENCONTRADA NO DOCUMENTO HISTÓRICO
-- ============================================================
ALTER TABLE sugestoes_fiscais_produtos
ADD COLUMN IF NOT EXISTS origem_mercadoria_historico
VARCHAR(1);


-- ============================================================
-- ORIGEM SUGERIDA PARA O PRODUTO
-- ============================================================
ALTER TABLE sugestoes_fiscais_produtos
ADD COLUMN IF NOT EXISTS origem_mercadoria_sugerida
VARCHAR(1);


-- ============================================================
-- VALIDAÇÃO DO CÓDIGO HISTÓRICO
--
-- Aceita:
-- NULL
-- 0 a 8
-- ============================================================
DO $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'ck_sugestoes_fiscais_origem_historico'
    )
    THEN

        ALTER TABLE sugestoes_fiscais_produtos
        ADD CONSTRAINT
            ck_sugestoes_fiscais_origem_historico

        CHECK (
            origem_mercadoria_historico IS NULL
            OR
            origem_mercadoria_historico IN (
                '0',
                '1',
                '2',
                '3',
                '4',
                '5',
                '6',
                '7',
                '8'
            )
        );

    END IF;

END
$$;


-- ============================================================
-- VALIDAÇÃO DO CÓDIGO SUGERIDO
--
-- Aceita:
-- NULL
-- 0 a 8
-- ============================================================
DO $$
BEGIN

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname =
            'ck_sugestoes_fiscais_origem_sugerida'
    )
    THEN

        ALTER TABLE sugestoes_fiscais_produtos
        ADD CONSTRAINT
            ck_sugestoes_fiscais_origem_sugerida

        CHECK (
            origem_mercadoria_sugerida IS NULL
            OR
            origem_mercadoria_sugerida IN (
                '0',
                '1',
                '2',
                '3',
                '4',
                '5',
                '6',
                '7',
                '8'
            )
        );

    END IF;

END
$$;