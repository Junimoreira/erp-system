-- =========================================================
-- CATEGORIAS DE PRODUTOS - AMPLIACAO PAPELARIA
-- =========================================================
-- Complementa o catalogo controlado de categorias para
-- melhorar a classificacao e os relatorios de papelaria.
--
-- Esta migration NAO altera produtos existentes.
-- =========================================================

INSERT INTO categorias_produtos (nome, grupo)
VALUES
    ('COLAGEM', 'PAPELARIA'),
    ('ESCRITA', 'PAPELARIA'),
    ('ETIQUETAS', 'PAPELARIA'),
    ('ORGANIZACAO', 'PAPELARIA'),

    -- MOCHILAS / BOLSAS
    ('MOCHILAS E BOLSAS', 'PAPELARIA'),

    -- UTILIDADES
    ('UTILIDADES', 'UTILIDADES')
ON CONFLICT (nome) DO NOTHING;
