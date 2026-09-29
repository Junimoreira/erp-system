-- =========================================================
-- NORMALIZACAO DAS CATEGORIAS DOS PRODUTOS
-- =========================================================
-- Mapeamento validado previamente no erp_local.
-- Migration idempotente: somente produtos que necessitam
-- normalizacao sao incluidos na proposta.
--
-- Categorias ausentes ou fora do catalogo ativo sao normalizadas.
-- Casos individuais podem ser incluidos para corrigir uma
-- categoria especifica mesmo quando ela ja pertence ao catalogo.
-- A atualizacao ocorre somente quando o destino difere do valor atual.
-- =========================================================

BEGIN;

WITH proposta AS (

    SELECT
        p.id,

        CASE

            -- NORMALIZACAO POR DADOS DO PRODUTO
            -- Nao utilizar ID como regra de categorizacao.

            -- CATEGORIAS LEGADAS

            -- Normaliza capitalizacao legada:
            -- Papelaria -> PAPELARIA
            WHEN UPPER(BTRIM(p.categoria)) = 'PAPELARIA'
                THEN 'PAPELARIA'

            -- Erro legado de digitacao
            WHEN UPPER(BTRIM(p.categoria)) = 'ATERSANAL'
             AND UPPER(p.nome) LIKE '%SLIME%'
                THEN 'BRINQUEDO'

            -- Categoria composta antiga
            WHEN UPPER(BTRIM(p.categoria)) =
                 'QUEBRA-CABECA/ALFABETIZACAO'
                THEN 'QUEBRA-CABECA'

            -- Raciocinio
            WHEN UPPER(BTRIM(p.categoria)) = 'RACIOCINIO'
             AND UPPER(p.nome) LIKE '%JUNTE QUATRO%'
                THEN 'RACIOCINIO LOGICO'

            -- Equilibrio
            WHEN UPPER(BTRIM(p.categoria)) IN (
                    'EDUCATIVA',
                    'EDUCATIVO',
                    'RACIOCINIO',
                    'RACIOCINIO LOGICO'
                 )
             AND UPPER(p.nome) LIKE '%EQUILIBRIO%'
                THEN 'EQUILIBRIO'

            -- Produtos artesanais classificados como brinquedos
            WHEN UPPER(BTRIM(p.categoria)) = 'ARTESANAL'
             AND (
                    UPPER(p.nome) LIKE '%FANTOCHE%'
                    OR UPPER(p.nome) LIKE '%CASINHA DE NATAL%'
                    OR UPPER(p.nome) LIKE '%CESTINHA DE FRUTAS%'
                    OR UPPER(p.nome) LIKE '%BALDE DE PRAIA%'
                    OR UPPER(p.nome) LIKE '%PESCARIA%'
                 )
                THEN 'BRINQUEDO'

            -- Materiais de arte
            WHEN UPPER(BTRIM(p.categoria)) = 'ARTESANAL'
             AND (
                    UPPER(p.nome) LIKE '%LANTEJOULA%'
                    OR UPPER(p.nome) LIKE '%FITA DECORATIVA%'
                    OR UPPER(p.nome) LIKE '%AREIA MAGICA%'
                 )
                THEN 'ARTES E PINTURA'

            WHEN UPPER(BTRIM(p.categoria)) = 'ACESSORIO'
                THEN 'ACESSORIOS'

            WHEN UPPER(BTRIM(p.categoria)) = 'ELETRONICA'
                THEN 'ELETRONICOS'

            WHEN UPPER(BTRIM(p.categoria)) = 'UNNIFORMES'
                THEN 'UNIFORMES'

            WHEN UPPER(BTRIM(p.categoria)) = 'NUMERAL'
             AND (
                    UPPER(p.nome) LIKE '%CONTINHAS%'
                    OR UPPER(p.nome) LIKE '%MATEMATICA%'
                    OR UPPER(p.nome) LIKE '%DIVISAO%'
                    OR UPPER(p.nome) LIKE '%MULTIPLICACAO%'
                 )
                THEN 'MATEMATICA'

            WHEN UPPER(BTRIM(p.categoria)) = 'NUMERAL'
             AND UPPER(p.nome) LIKE '%QUEBRA%CABE%'
                THEN 'QUEBRA-CABECA'

            WHEN UPPER(BTRIM(p.categoria)) IN (
                    'RECIOCINIO/MEMORIA',
                    'MEMORIA/RACIOCINIO',
                    'MEMORIA/EDUCATIVO'
                 )
                THEN 'MEMORIA'

            WHEN UPPER(BTRIM(p.categoria)) IN (
                    'EDUCATIVA/ENCAIXE',
                    'ENCAIXE/EDUCATIVA'
                 )
                THEN 'EDUCATIVO'

            WHEN UPPER(BTRIM(p.categoria)) = 'EQUILIBRIO/RACIOCINIO'
                THEN 'EQUILIBRIO'

            WHEN UPPER(BTRIM(p.categoria)) = 'DESAFIO LOGICO'
                THEN 'DESAFIO'

            WHEN UPPER(BTRIM(p.categoria)) = 'SENSORIAL/MUSICAL'
                THEN 'SENSORIAL'

            WHEN UPPER(BTRIM(p.categoria)) = 'ENTRETERIMENTO/CARTAS'
                THEN 'BRINQUEDO'

            WHEN UPPER(BTRIM(p.categoria)) = 'ENTRETERIMENTO'
             AND UPPER(p.nome) LIKE '%ALBUM DA COPA%'
                THEN 'PAPELARIA'

            WHEN UPPER(BTRIM(p.categoria)) = 'ENTRETERIMENTO'
                THEN 'BRINQUEDO'

            WHEN UPPER(BTRIM(p.categoria)) = 'LUDICA'
                THEN 'BRINQUEDO'

            WHEN UPPER(BTRIM(p.categoria)) = 'ARTESANAL'
             AND UPPER(p.nome) LIKE '%PINCEL%'
                THEN 'ARTES E PINTURA'

            WHEN UPPER(BTRIM(p.categoria)) = 'ARTESANAL'
             AND UPPER(p.nome) LIKE '%KIT PINTURA%'
                THEN 'ARTES E PINTURA'

            WHEN LOWER(BTRIM(p.categoria)) = 'brinquedos'
            THEN CASE
                WHEN UPPER(p.nome) LIKE '%FORMANDO PALAVRAS%'
                    THEN 'ALFABETIZACAO'

                WHEN UPPER(p.nome) LIKE '%QUEBRA%CABE%'
                    THEN 'QUEBRA-CABECA'
                WHEN UPPER(p.nome) LIKE '%MEMORIA%'
                    THEN 'MEMORIA'
                WHEN UPPER(p.nome) LIKE '%DOMINO%'
                    THEN 'DOMINO'
                WHEN UPPER(p.nome) LIKE '%XILOFONE%'
                    THEN 'MUSICAL'
                WHEN UPPER(p.nome) LIKE '%ALFABETO%'
                    THEN 'ALFABETIZACAO'
                WHEN UPPER(p.nome) LIKE '%PEDAGOGIC%'
                    THEN 'PEDAGOGICO'
                ELSE 'BRINQUEDO'
            END

            WHEN UPPER(BTRIM(p.categoria)) = 'EDUCATIVA'
             AND UPPER(p.nome) LIKE '%LIVRO%'
                THEN 'LIVROS'

            WHEN UPPER(BTRIM(p.categoria)) IN (
                'EDUCATIVA',
                'ENDUCATIVO'
            )
                THEN 'EDUCATIVO'

            WHEN UPPER(BTRIM(p.categoria)) = 'LEITURA'
                THEN 'LIVROS'

            WHEN UPPER(BTRIM(p.categoria)) = 'PEDAGOGICA'
                THEN 'PEDAGOGICO'

            WHEN UPPER(BTRIM(p.categoria)) = 'QUEBRA -CABECA'
                THEN 'QUEBRA-CABECA'

            WHEN UPPER(BTRIM(p.categoria)) = 'UNIFORME'
                THEN 'UNIFORMES'

            WHEN UPPER(BTRIM(p.categoria)) =
                 'ITERATIVO/ALFABETIZACAO'
                THEN 'ALFABETIZACAO'

            WHEN UPPER(BTRIM(p.categoria)) =
                 'CONHECIMENTO E CORES'
                THEN 'CONHECIMENTO'

            WHEN UPPER(BTRIM(p.categoria)) = 'RACIOCINIO'
             AND UPPER(p.nome) LIKE '%DOMINO%'
                THEN 'DOMINO'

            WHEN UPPER(BTRIM(p.categoria)) = 'RACIOCINIO'
             AND UPPER(p.nome) LIKE '%EQUILIBRA%'
                THEN 'EQUILIBRIO'

            WHEN UPPER(BTRIM(p.categoria)) = 'ARTESANAL'
             AND (
                UPPER(p.nome) LIKE '%TINTA%'
                OR UPPER(p.nome) LIKE '%MASSINHA%'
                OR UPPER(p.nome) LIKE '%MASSA DE E.V.A%'
                OR UPPER(p.nome) LIKE '%MARCADOR%'
                OR UPPER(p.nome) LIKE '%GIZ%'
             )
                THEN 'ARTES E PINTURA'

            WHEN UPPER(BTRIM(p.categoria)) = 'ARTESANAL'
             AND UPPER(p.nome) LIKE '%COLA%'
                THEN 'COLAGEM'

            -- PRODUTOS SEM CATEGORIA
            WHEN p.categoria IS NULL
              OR BTRIM(p.categoria) = ''
              OR LOWER(BTRIM(p.categoria)) = 'nan'
            THEN CASE

                WHEN UPPER(p.nome) LIKE 'IMPRESS%'
                    THEN 'USO E CONSUMO'

                WHEN UPPER(p.nome) LIKE '%CAMISETA%'
                  OR UPPER(p.nome) LIKE '%AGASALHO%'
                  OR UPPER(p.nome) LIKE '%SHORT-SAIA%'
                  OR UPPER(p.nome) LIKE '%CALCA %'
                    THEN 'UNIFORMES'

                WHEN UPPER(p.nome) LIKE '%ETIQUETA%'
                    THEN 'ETIQUETAS'

                WHEN UPPER(p.nome) LIKE '%PASTA%'
                  OR UPPER(p.nome) LIKE '%ORGANIZADORA%'
                    THEN 'ORGANIZACAO'

                WHEN UPPER(p.nome) LIKE '%COLA %'
                  OR UPPER(p.nome) LIKE 'COLA %'
                  OR UPPER(p.nome) LIKE '%DUREX%'
                    THEN 'COLAGEM'

                WHEN UPPER(p.nome) LIKE '%LAPIS%'
                  OR UPPER(p.nome) LIKE '%CANETA%'
                  OR UPPER(p.nome) LIKE '%CANETINHA%'
                  OR UPPER(p.nome) LIKE '%CORRETIVO%'
                  OR UPPER(p.nome) LIKE '%BORRACHA%'
                    THEN 'ESCRITA'

                WHEN UPPER(p.nome) LIKE '%MASSINHA%'
                  OR UPPER(p.nome) LIKE '%MASSA DE E.V.A%'
                    THEN 'ARTES E PINTURA'

                WHEN UPPER(p.nome) LIKE '%LIVRO%'
                  OR UPPER(p.nome) LIKE '%ATIVIDADES PARA COLORIR%'
                    THEN 'LIVROS'

                WHEN UPPER(p.nome) LIKE '%QUEBRA%CABE%'
                    THEN 'QUEBRA-CABECA'

                WHEN UPPER(p.nome) LIKE '%MEMORIA%'
                    THEN 'MEMORIA'

                WHEN UPPER(p.nome) LIKE '%DOMINO%'
                    THEN 'DOMINO'

                WHEN UPPER(p.nome) LIKE '%XILOFONE%'
                  OR UPPER(p.nome) LIKE '%MUSICAL%'
                    THEN 'MUSICAL'

                WHEN UPPER(p.nome) LIKE '%ALFABETO%'
                  OR UPPER(p.nome) LIKE '%FORMANDO PALAVRAS%'
                  OR UPPER(p.nome) LIKE '%MONTANDO AS PALAVRAS%'
                  OR UPPER(p.nome) LIKE '%PALAVRAS CRUZADAS%'
                    THEN 'ALFABETIZACAO'

                WHEN UPPER(p.nome) LIKE '%CONTINHAS%'
                    THEN 'MATEMATICA'

                WHEN UPPER(p.nome) LIKE '%MATERIAL DOURADO%'
                    THEN 'MATEMATICA'

                WHEN UPPER(p.nome) LIKE '%DESAFIO DAS PALAVRAS%'
                    THEN 'DESAFIO'

                WHEN UPPER(p.nome) LIKE '%PACOTE FIGURINHAS%'
                    THEN 'PAPELARIA'

                WHEN UPPER(p.nome) LIKE '%COBRINHA INTELIGENTE%'
                    THEN 'RACIOCINIO LOGICO'

                WHEN (
                        UPPER(p.nome) LIKE '%SEQU%'
                        AND UPPER(p.nome) LIKE '%CORES%'
                     )
                    THEN 'EDUCATIVO'

                WHEN (
                        UPPER(p.nome) LIKE '%LOUSA%'
                        AND UPPER(p.nome) LIKE '%STITCH%'
                     )
                    THEN 'BRINQUEDO'

                WHEN UPPER(p.nome) LIKE '%BOX DE ATIVIDADES%'
                    THEN 'EDUCATIVO'

                WHEN UPPER(p.nome) LIKE '%BINGO DOS ANIMAIS%'
                    THEN 'BRINQUEDO'

                WHEN UPPER(p.nome) LIKE '%PEDAGOGIC%'
                    THEN 'PEDAGOGICO'

                WHEN UPPER(p.nome) LIKE '%UNO%'
                  OR UPPER(p.nome) LIKE '%ROUBA MONTE%'
                  OR UPPER(p.nome) LIKE '%JOGO DE CARTAS%'
                  OR UPPER(p.nome) LIKE '%MICO%'
                    THEN 'BRINQUEDO'

                ELSE NULL
            END

            ELSE NULL

        END AS categoria_nova

    FROM produtos p

    WHERE
        (
            UPPER(BTRIM(p.categoria)) = 'PAPELARIA'
            AND p.categoria IS DISTINCT FROM 'PAPELARIA'
        )
        OR p.categoria IS NULL
        OR BTRIM(p.categoria) = ''
        OR LOWER(BTRIM(p.categoria)) = 'nan'
        OR NOT EXISTS (
            SELECT 1
            FROM categorias_produtos c
            WHERE c.ativo = TRUE
              AND UPPER(BTRIM(c.nome)) =
                  UPPER(BTRIM(p.categoria))
        )
),

validacao AS (
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (
            WHERE categoria_nova IS NULL
        ) AS sem_destino,
        COUNT(*) FILTER (
            WHERE categoria_nova IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM categorias_produtos c
                  WHERE c.ativo = TRUE
                    AND c.nome = proposta.categoria_nova
              )
        ) AS destino_invalido
    FROM proposta
),

protege AS (
    SELECT
        1 AS ok
    FROM validacao
    WHERE sem_destino = 0
      AND destino_invalido = 0
),

atualizacao AS (
    UPDATE produtos p
       SET categoria = proposta.categoria_nova
      FROM proposta, protege
     WHERE p.id = proposta.id
       AND proposta.categoria_nova IS NOT NULL
       AND protege.ok = 1
       AND p.categoria IS DISTINCT FROM proposta.categoria_nova
    RETURNING p.id
)

SELECT
    COUNT(*) AS produtos_normalizados
FROM atualizacao;

COMMIT;
