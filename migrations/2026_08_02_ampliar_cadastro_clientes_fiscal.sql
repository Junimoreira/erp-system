-- ============================================================
-- ERP VERDE INFÂNCIA
-- AMPLIAÇÃO DO CADASTRO DE CLIENTES
--
-- Finalidade:
--   - Pessoa Física e Pessoa Jurídica
--   - Preparação para NF-e modelo 55
--   - Preparação para NFC-e modelo 65
--
-- Características:
--   - Não apaga dados existentes
--   - Pode ser executada novamente com segurança
--   - Novos campos fiscais permanecem opcionais
-- ============================================================

BEGIN;


-- ============================================================
-- 1. IDENTIFICAÇÃO DO CLIENTE
-- ============================================================

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS tipo_pessoa VARCHAR(2);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS cpf VARCHAR(14);

-- VARCHAR maior para suportar formatação e futura estrutura
-- alfanumérica do CNPJ.
ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS cnpj VARCHAR(20);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS razao_social VARCHAR(200);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS nome_fantasia VARCHAR(200);


-- ============================================================
-- 2. DADOS FISCAIS
-- ============================================================

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS inscricao_estadual VARCHAR(30);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS inscricao_municipal VARCHAR(30);

-- Indicador de Inscrição Estadual:
-- 1 = Contribuinte do ICMS
-- 2 = Contribuinte isento
-- 9 = Não contribuinte
ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS indicador_ie SMALLINT;

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS email_fiscal VARCHAR(150);


-- ============================================================
-- 3. ENDEREÇO
-- ============================================================

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS cep VARCHAR(9);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS logradouro VARCHAR(200);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS numero VARCHAR(20);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS complemento VARCHAR(100);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS bairro VARCHAR(100);

-- A coluna cidade já existe e será mantida.
ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS uf VARCHAR(2);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS codigo_municipio_ibge VARCHAR(7);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS codigo_pais VARCHAR(4);

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS pais VARCHAR(60);


-- ============================================================
-- 4. INFORMAÇÕES DE CONTROLE
-- ============================================================

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS observacoes TEXT;

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS ativo BOOLEAN;

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMP WITHOUT TIME ZONE;


-- ============================================================
-- 5. VALORES PADRÃO PARA REGISTROS ATUAIS
-- ============================================================

UPDATE clientes
SET tipo_pessoa = 'PF'
WHERE tipo_pessoa IS NULL
   OR TRIM(tipo_pessoa) = '';

UPDATE clientes
SET indicador_ie = 9
WHERE indicador_ie IS NULL;

UPDATE clientes
SET codigo_pais = '1058'
WHERE codigo_pais IS NULL
   OR TRIM(codigo_pais) = '';

UPDATE clientes
SET pais = 'Brasil'
WHERE pais IS NULL
   OR TRIM(pais) = '';

UPDATE clientes
SET ativo = TRUE
WHERE ativo IS NULL;

UPDATE clientes
SET atualizado_em = CURRENT_TIMESTAMP
WHERE atualizado_em IS NULL;


-- ============================================================
-- 6. VALORES PADRÃO PARA NOVOS CADASTROS
-- ============================================================

ALTER TABLE clientes
    ALTER COLUMN tipo_pessoa SET DEFAULT 'PF';

ALTER TABLE clientes
    ALTER COLUMN indicador_ie SET DEFAULT 9;

ALTER TABLE clientes
    ALTER COLUMN codigo_pais SET DEFAULT '1058';

ALTER TABLE clientes
    ALTER COLUMN pais SET DEFAULT 'Brasil';

ALTER TABLE clientes
    ALTER COLUMN ativo SET DEFAULT TRUE;

ALTER TABLE clientes
    ALTER COLUMN atualizado_em SET DEFAULT CURRENT_TIMESTAMP;


-- ============================================================
-- 7. RESTRIÇÕES DE INTEGRIDADE
-- ============================================================

-- Restringe o tipo de pessoa para PF ou PJ.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_clientes_tipo_pessoa'
          AND conrelid = 'clientes'::regclass
    ) THEN
        ALTER TABLE clientes
            ADD CONSTRAINT ck_clientes_tipo_pessoa
            CHECK (
                tipo_pessoa IS NULL
                OR UPPER(TRIM(tipo_pessoa)) IN ('PF', 'PJ')
            );
    END IF;
END
$$;


-- Restringe os códigos permitidos para o indicador de IE.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_clientes_indicador_ie'
          AND conrelid = 'clientes'::regclass
    ) THEN
        ALTER TABLE clientes
            ADD CONSTRAINT ck_clientes_indicador_ie
            CHECK (
                indicador_ie IS NULL
                OR indicador_ie IN (1, 2, 9)
            );
    END IF;
END
$$;


-- UF deve possuir duas letras quando informada.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_clientes_uf'
          AND conrelid = 'clientes'::regclass
    ) THEN
        ALTER TABLE clientes
            ADD CONSTRAINT ck_clientes_uf
            CHECK (
                uf IS NULL
                OR TRIM(uf) = ''
                OR TRIM(uf) ~ '^[A-Za-z]{2}$'
            );
    END IF;
END
$$;


-- CPF deve possuir 11 dígitos quando informado.
-- Esta restrição verifica o tamanho, mas não calcula
-- os dígitos verificadores. Essa validação ficará no Python.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_clientes_cpf_tamanho'
          AND conrelid = 'clientes'::regclass
    ) THEN
        ALTER TABLE clientes
            ADD CONSTRAINT ck_clientes_cpf_tamanho
            CHECK (
                cpf IS NULL
                OR TRIM(cpf) = ''
                OR LENGTH(
                    REGEXP_REPLACE(cpf, '[^0-9]', '', 'g')
                ) = 11
            );
    END IF;
END
$$;


-- Código IBGE municipal deve possuir sete dígitos.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_clientes_codigo_ibge'
          AND conrelid = 'clientes'::regclass
    ) THEN
        ALTER TABLE clientes
            ADD CONSTRAINT ck_clientes_codigo_ibge
            CHECK (
                codigo_municipio_ibge IS NULL
                OR TRIM(codigo_municipio_ibge) = ''
                OR codigo_municipio_ibge ~ '^[0-9]{7}$'
            );
    END IF;
END
$$;


-- ============================================================
-- 8. ÍNDICES PARA PESQUISA
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_clientes_nome_normalizado
    ON clientes (
        UPPER(TRIM(nome))
    );

CREATE INDEX IF NOT EXISTS idx_clientes_tipo_pessoa
    ON clientes (
        tipo_pessoa
    );

CREATE INDEX IF NOT EXISTS idx_clientes_cpf_pesquisa
    ON clientes (
        REGEXP_REPLACE(
            COALESCE(cpf, ''),
            '[^0-9]',
            '',
            'g'
        )
    );

-- O CNPJ é indexado como texto normalizado, permitindo
-- letras e números.
CREATE INDEX IF NOT EXISTS idx_clientes_cnpj_pesquisa
    ON clientes (
        UPPER(
            REGEXP_REPLACE(
                COALESCE(cnpj, ''),
                '[^A-Za-z0-9]',
                '',
                'g'
            )
        )
    );

CREATE INDEX IF NOT EXISTS idx_clientes_telefone_pesquisa
    ON clientes (
        REGEXP_REPLACE(
            COALESCE(telefone, ''),
            '[^0-9]',
            '',
            'g'
        )
    );

CREATE INDEX IF NOT EXISTS idx_clientes_email_normalizado
    ON clientes (
        LOWER(TRIM(email))
    );

CREATE INDEX IF NOT EXISTS idx_clientes_cep
    ON clientes (
        REGEXP_REPLACE(
            COALESCE(cep, ''),
            '[^0-9]',
            '',
            'g'
        )
    );

CREATE INDEX IF NOT EXISTS idx_clientes_codigo_municipio_ibge
    ON clientes (
        codigo_municipio_ibge
    );


-- ============================================================
-- 9. COMENTÁRIOS DE DOCUMENTAÇÃO
-- ============================================================

COMMENT ON COLUMN clientes.tipo_pessoa IS
    'Tipo de pessoa: PF ou PJ';

COMMENT ON COLUMN clientes.cpf IS
    'CPF da pessoa física, armazenado como texto';

COMMENT ON COLUMN clientes.cnpj IS
    'CNPJ da pessoa jurídica, armazenado como texto e preparado para estrutura alfanumérica';

COMMENT ON COLUMN clientes.razao_social IS
    'Razão social da pessoa jurídica';

COMMENT ON COLUMN clientes.nome_fantasia IS
    'Nome fantasia da pessoa jurídica';

COMMENT ON COLUMN clientes.inscricao_estadual IS
    'Inscrição Estadual do destinatário';

COMMENT ON COLUMN clientes.indicador_ie IS
    'Indicador de IE: 1 contribuinte, 2 isento, 9 não contribuinte';

COMMENT ON COLUMN clientes.codigo_municipio_ibge IS
    'Código IBGE de sete posições do município';

COMMENT ON COLUMN clientes.codigo_pais IS
    'Código do país; Brasil = 1058';

COMMENT ON COLUMN clientes.email_fiscal IS
    'E-mail utilizado para envio de documentos fiscais';


COMMIT;


-- ============================================================
-- FIM DA MIGRATION
-- ============================================================