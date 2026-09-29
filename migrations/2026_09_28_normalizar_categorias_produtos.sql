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

            -- CASOS INDIVIDUAIS
            WHEN p.id = 23  THEN 'ARTES E PINTURA'
            WHEN p.id = 50  THEN 'USO E CONSUMO'
            WHEN p.id = 54  THEN 'LIVROS'
            WHEN p.id = 79  THEN 'MEMORIA'
            WHEN p.id = 223 THEN 'BRINQUEDO'

            -- SERVICOS DE PAPELARIA
            WHEN p.id = 264 THEN 'PAPELARIA'
            WHEN p.id = 265 THEN 'PAPELARIA'

            WHEN p.id = 8   THEN 'ARTES E PINTURA'
            WHEN p.id = 13  THEN 'PAPELARIA'
            WHEN p.id = 24  THEN 'BRINQUEDO'
            WHEN p.id = 25  THEN 'BRINQUEDO'
            WHEN p.id = 26  THEN 'BRINQUEDO'
            WHEN p.id = 27  THEN 'ALFABETIZACAO'
            WHEN p.id = 49  THEN 'BRINQUEDO'
            WHEN p.id = 56  THEN 'PAPELARIA'
            WHEN p.id = 57  THEN 'ACESSORIOS'
            WHEN p.id = 70  THEN 'PAPELARIA'
            WHEN p.id = 89  THEN 'EDUCATIVO'
            WHEN p.id = 101 THEN 'EDUCATIVO'
            WHEN p.id = 102 THEN 'RACIOCINIO LOGICO'
            WHEN p.id = 113 THEN 'EDUCATIVO'
            WHEN p.id = 114 THEN 'RACIOCINIO LOGICO'
            WHEN p.id = 119 THEN 'EDUCATIVO'
            WHEN p.id = 137 THEN 'PAPELARIA'
            WHEN p.id = 138 THEN 'PAPELARIA'
            WHEN p.id = 143 THEN 'PAPELARIA'
            WHEN p.id = 152 THEN 'BRINQUEDO'
            WHEN p.id = 155 THEN 'EDUCATIVO'
            WHEN p.id = 156 THEN 'BRINQUEDO'
            WHEN p.id = 339 THEN 'BRINQUEDO'

            -- CASOS INDIVIDUAIS - IMPORTACAO / USO INTERNO
            WHEN p.id = 340 THEN 'USO E CONSUMO'
            WHEN p.id = 343 THEN 'UTILIDADES'

            WHEN p.id IN (
                344,
                345,
                346,
                347,
                348,
                349,
                350
            )
                THEN 'MOCHILAS E BOLSAS'

            WHEN p.id = 351 THEN 'USO E CONSUMO'

            -- CATEGORIAS LEGADAS
            WHEN LOWER(BTRIM(p.categoria)) = 'brinquedos'
            THEN CASE
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
            THEN CASE

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
            p.id IN (264, 265)
            AND p.categoria IS DISTINCT FROM 'PAPELARIA'
        )
        OR (
            p.id = 340
            AND p.categoria IS DISTINCT FROM 'USO E CONSUMO'
        )
        OR p.categoria IS NULL
        OR BTRIM(p.categoria) = ''
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
