-- Cadastro controlado de categorias de produtos.
--
-- Objetivos:
-- 1. impedir variacoes de digitacao no cadastro;
-- 2. organizar os produtos por GRUPO e CATEGORIA;
-- 3. preservar produtos.categoria durante a transicao;
-- 4. permitir que Novo Produto e Editar Produto utilizem listas.
--
-- Nenhum produto existente e alterado por esta migration.

CREATE TABLE IF NOT EXISTS categorias_produtos (

    id SERIAL PRIMARY KEY,

    nome VARCHAR(100) NOT NULL,

    grupo VARCHAR(100) NOT NULL,

    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_categorias_produtos_nome
        UNIQUE (nome)
);

CREATE INDEX IF NOT EXISTS
idx_categorias_produtos_grupo
ON categorias_produtos (grupo);

CREATE INDEX IF NOT EXISTS
idx_categorias_produtos_ativo
ON categorias_produtos (ativo);

COMMENT ON TABLE categorias_produtos IS
'Cadastro controlado de categorias disponiveis para os produtos do ERP.';

COMMENT ON COLUMN categorias_produtos.nome IS
'Nome padronizado da categoria apresentada no cadastro de produtos.';

COMMENT ON COLUMN categorias_produtos.grupo IS
'Grupo principal ao qual a categoria pertence.';

COMMENT ON COLUMN categorias_produtos.ativo IS
'Define se a categoria pode ser utilizada em novos cadastros e edicoes.';


-- ============================================================
-- CATALOGO INICIAL
-- ============================================================
--
-- ON CONFLICT torna a carga idempotente.
-- Executar novamente nao duplica categorias.
--
-- Produtos antigos NAO sao atualizados nesta etapa.
-- ============================================================

INSERT INTO categorias_produtos (
    nome,
    grupo
)
VALUES

    -- BRINQUEDOS
    ('ALFABETIZACAO', 'BRINQUEDOS'),
    ('ALINHAVO', 'BRINQUEDOS'),
    ('BRINQUEDO', 'BRINQUEDOS'),
    ('CONHECIMENTO', 'BRINQUEDOS'),
    ('COORDENACAO MOTORA', 'BRINQUEDOS'),
    ('DESAFIO', 'BRINQUEDOS'),
    ('DOMINO', 'BRINQUEDOS'),
    ('EDUCATIVO', 'BRINQUEDOS'),
    ('ENCAIXE', 'BRINQUEDOS'),
    ('EQUILIBRIO', 'BRINQUEDOS'),
    ('INTERATIVO', 'BRINQUEDOS'),
    ('MATEMATICA', 'BRINQUEDOS'),
    ('MEMORIA', 'BRINQUEDOS'),
    ('MONTESSORI', 'BRINQUEDOS'),
    ('MUSICAL', 'BRINQUEDOS'),
    ('NUMERAIS', 'BRINQUEDOS'),
    ('PEDAGOGICO', 'BRINQUEDOS'),
    ('QUEBRA-CABECA', 'BRINQUEDOS'),
    ('RACIOCINIO LOGICO', 'BRINQUEDOS'),
    ('SENSORIAL', 'BRINQUEDOS'),
    ('TABULEIRO', 'BRINQUEDOS'),

    -- PAPELARIA
    ('PAPELARIA', 'PAPELARIA'),
    ('ARTES E PINTURA', 'PAPELARIA'),

    -- UNIFORMES
    ('UNIFORMES', 'UNIFORMES'),

    -- ACESSORIOS
    ('ACESSORIOS', 'ACESSORIOS'),

    -- ELETRONICOS
    ('ELETRONICOS', 'ELETRONICOS'),

    -- LIVROS
    ('LIVROS', 'LIVROS'),

    -- UTILIDADES
    ('UTENSILIOS', 'UTILIDADES'),

    -- USO INTERNO
    ('USO E CONSUMO', 'USO INTERNO')

ON CONFLICT (nome)
DO NOTHING;
