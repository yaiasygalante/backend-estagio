-- Dados de demonstração. Usa INSERT OR IGNORE com ids fixos, então pode rodar de novo sem duplicar.

INSERT OR IGNORE INTO clientes (id, nome, email) VALUES
    (1, 'Marina Costa',  'marina@exemplo.com'),
    (2, 'Rafael Lima',   'rafael@exemplo.com'),
    (3, 'Beatriz Souza', 'beatriz@exemplo.com');

INSERT OR IGNORE INTO produtos (id, nome, preco_centavos, estoque) VALUES
    (1, 'Teclado mecânico',  25990, 40),
    (2, 'Mouse sem fio',      8990, 120),
    (3, 'Monitor 24 polegadas', 79900, 15),
    (4, 'Webcam Full HD',    18900, 30),
    (5, 'Hub USB-C',          12900, 0);

INSERT OR IGNORE INTO pedidos (id, cliente_id, status) VALUES
    (1, 1, 'pago'),
    (2, 2, 'pendente'),
    (3, 1, 'enviado');

INSERT OR IGNORE INTO itens_pedido (id, pedido_id, produto_id, quantidade, preco_unitario_centavos) VALUES
    (1, 1, 1, 1, 25990),
    (2, 1, 2, 2,  8990),
    (3, 2, 3, 1, 79900),
    (4, 3, 4, 1, 18900);
