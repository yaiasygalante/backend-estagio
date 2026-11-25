-- Esquema do banco (SQLite). Pode ser executado várias vezes sem erro.
-- Valores em dinheiro ficam em centavos (inteiro) para evitar erro de arredondamento.

CREATE TABLE IF NOT EXISTS clientes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT    NOT NULL CHECK (length(nome) BETWEEN 1 AND 120),
    email     TEXT    NOT NULL UNIQUE,
    criado_em TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS produtos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL CHECK (length(nome) BETWEEN 1 AND 120),
    preco_centavos INTEGER NOT NULL CHECK (preco_centavos > 0),
    estoque        INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pedidos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL REFERENCES clientes (id),
    status     TEXT    NOT NULL DEFAULT 'pendente'
               CHECK (status IN ('pendente', 'pago', 'enviado', 'cancelado')),
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Cada linha é um produto dentro de um pedido. O preço é copiado no momento
-- da compra, para que mudar o preço do produto depois não altere pedidos antigos.
CREATE TABLE IF NOT EXISTS itens_pedido (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id                INTEGER NOT NULL REFERENCES pedidos (id) ON DELETE CASCADE,
    produto_id               INTEGER NOT NULL REFERENCES produtos (id),
    quantidade               INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario_centavos  INTEGER NOT NULL CHECK (preco_unitario_centavos > 0),
    UNIQUE (pedido_id, produto_id)
);

CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos (cliente_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_status  ON pedidos (status);
CREATE INDEX IF NOT EXISTS idx_itens_produto   ON itens_pedido (produto_id);
