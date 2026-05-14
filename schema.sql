-- ==================================================
-- CLIENTES
-- ==================================================

CREATE TABLE IF NOT EXISTS clientes (

    id SERIAL PRIMARY KEY,

    nome VARCHAR(150) NOT NULL,

    telefone VARCHAR(30),

    email VARCHAR(150),

    endereco TEXT,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==================================================
-- PRODUTOS
-- ==================================================

CREATE TABLE IF NOT EXISTS produtos (

    id SERIAL PRIMARY KEY,

    nome VARCHAR(150) NOT NULL,

    descricao TEXT,

    preco NUMERIC(10,2) NOT NULL CHECK (preco >= 0),

    custo NUMERIC(10,2) DEFAULT 0 CHECK (custo >= 0),

    estoque INTEGER DEFAULT 0 CHECK (estoque >= 0),

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==================================================
-- CONTAS BANCÁRIAS
-- ==================================================

CREATE TABLE IF NOT EXISTS contas_bancarias (

    id SERIAL PRIMARY KEY,

    banco VARCHAR(100) NOT NULL,

    agencia VARCHAR(20),

    conta VARCHAR(30),

    tipo_conta VARCHAR(30),

    saldo NUMERIC(10,2) DEFAULT 0,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==================================================
-- CATEGORIAS FINANCEIRAS
-- ==================================================

CREATE TABLE IF NOT EXISTS categorias_financeiras (

    id SERIAL PRIMARY KEY,

    nome VARCHAR(100) NOT NULL UNIQUE,

    tipo VARCHAR(20) NOT NULL,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==================================================
-- VENDAS
-- ==================================================

CREATE TABLE IF NOT EXISTS vendas (

    id SERIAL PRIMARY KEY,

    cliente_id INTEGER,

    valor_total NUMERIC(10,2) NOT NULL CHECK (valor_total >= 0),

    forma_pagamento VARCHAR(50),

    status VARCHAR(30) DEFAULT 'Concluída',

    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cliente_id)
        REFERENCES clientes(id)
        ON DELETE SET NULL
);


-- ==================================================
-- ITENS DA VENDA
-- ==================================================

CREATE TABLE IF NOT EXISTS itens_venda (

    id SERIAL PRIMARY KEY,

    venda_id INTEGER NOT NULL,

    produto_id INTEGER NOT NULL,

    quantidade INTEGER NOT NULL CHECK (quantidade > 0),

    preco_unitario NUMERIC(10,2) NOT NULL CHECK (preco_unitario >= 0),

    subtotal NUMERIC(10,2) NOT NULL CHECK (subtotal >= 0),

    FOREIGN KEY (venda_id)
        REFERENCES vendas(id)
        ON DELETE CASCADE,

    FOREIGN KEY (produto_id)
        REFERENCES produtos(id)
        ON DELETE CASCADE
);


-- ==================================================
-- CONTAS A PAGAR
-- ==================================================

CREATE TABLE IF NOT EXISTS contas_pagar (

    id SERIAL PRIMARY KEY,

    descricao VARCHAR(255) NOT NULL,

    categoria_id INTEGER,

    valor NUMERIC(10,2) NOT NULL CHECK (valor >= 0),

    vencimento DATE NOT NULL,

    status VARCHAR(20) DEFAULT 'Pendente',

    observacoes TEXT,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (categoria_id)
        REFERENCES categorias_financeiras(id)
        ON DELETE SET NULL
);


-- ==================================================
-- CONTAS A RECEBER
-- ==================================================

CREATE TABLE IF NOT EXISTS contas_receber (

    id SERIAL PRIMARY KEY,

    cliente_id INTEGER,

    descricao VARCHAR(255) NOT NULL,

    valor NUMERIC(10,2) NOT NULL CHECK (valor >= 0),

    vencimento DATE NOT NULL,

    status VARCHAR(20) DEFAULT 'Pendente',

    observacoes TEXT,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (cliente_id)
        REFERENCES clientes(id)
        ON DELETE SET NULL
);


-- ==================================================
-- FLUXO DE CAIXA
-- ==================================================

CREATE TABLE IF NOT EXISTS fluxo_caixa (

    id SERIAL PRIMARY KEY,

    tipo VARCHAR(20) NOT NULL,

    descricao TEXT,

    categoria_id INTEGER,

    valor NUMERIC(10,2) NOT NULL CHECK (valor >= 0),

    data_lancamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    origem VARCHAR(50),

    FOREIGN KEY (categoria_id)
        REFERENCES categorias_financeiras(id)
        ON DELETE SET NULL
);


-- ==================================================
-- MOVIMENTAÇÕES BANCÁRIAS
-- ==================================================

CREATE TABLE IF NOT EXISTS movimentacoes_bancarias (

    id SERIAL PRIMARY KEY,

    conta_id INTEGER NOT NULL,

    categoria_id INTEGER,

    tipo VARCHAR(20) NOT NULL,

    descricao TEXT,

    valor NUMERIC(10,2) NOT NULL CHECK (valor >= 0),

    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (conta_id)
        REFERENCES contas_bancarias(id)
        ON DELETE CASCADE,

    FOREIGN KEY (categoria_id)
        REFERENCES categorias_financeiras(id)
        ON DELETE SET NULL
);


-- ==================================================
-- INSERIR CATEGORIAS PADRÃO
-- ==================================================

INSERT INTO categorias_financeiras (nome, tipo)
VALUES
('Vendas', 'Entrada'),
('Serviços', 'Entrada'),
('Investimentos', 'Entrada'),
('Aluguel', 'Saída'),
('Energia', 'Saída'),
('Internet', 'Saída'),
('Funcionários', 'Saída'),
('Impostos', 'Saída'),
('Fornecedores', 'Saída')
ON CONFLICT (nome) DO NOTHING;