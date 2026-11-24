-- Consultas usadas pela API (e úteis para estudar SQL). Rode no sqlite3 ou em qualquer cliente SQLite.

-- 1) Total de cada pedido: JOIN + SUM + GROUP BY.
SELECT p.id,
       c.nome AS cliente,
       p.status,
       COALESCE(SUM(i.quantidade * i.preco_unitario_centavos), 0) AS total_centavos
FROM pedidos p
JOIN clientes c            ON c.id = p.cliente_id
LEFT JOIN itens_pedido i   ON i.pedido_id = p.id
GROUP BY p.id, c.nome, p.status
ORDER BY p.id;

-- 2) Vendas por produto, ignorando pedidos cancelados.
SELECT pr.id AS produto_id,
       pr.nome,
       SUM(i.quantidade)                                   AS unidades_vendidas,
       SUM(i.quantidade * i.preco_unitario_centavos)       AS receita_centavos
FROM itens_pedido i
JOIN pedidos  p  ON p.id  = i.pedido_id
JOIN produtos pr ON pr.id = i.produto_id
WHERE p.status <> 'cancelado'
GROUP BY pr.id, pr.nome
ORDER BY receita_centavos DESC, pr.nome;

-- 3) Clientes que mais gastaram.
SELECT c.id AS cliente_id,
       c.nome,
       COUNT(DISTINCT p.id)                                AS pedidos,
       SUM(i.quantidade * i.preco_unitario_centavos)       AS total_gasto_centavos
FROM clientes c
JOIN pedidos      p ON p.cliente_id = c.id
JOIN itens_pedido i ON i.pedido_id  = p.id
WHERE p.status <> 'cancelado'
GROUP BY c.id, c.nome
ORDER BY total_gasto_centavos DESC
LIMIT 5;

-- 4) Produtos sem estoque (candidatos a reposição).
SELECT id, nome FROM produtos WHERE estoque = 0 ORDER BY nome;
