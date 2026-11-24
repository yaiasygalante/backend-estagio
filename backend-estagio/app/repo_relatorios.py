"""Consultas de relatório (JOIN, GROUP BY e agregações). Pedidos cancelados não contam."""
import sqlite3


def vendas_por_produto(conn: sqlite3.Connection) -> list[dict]:
    linhas = conn.execute(
        """
        SELECT pr.id AS produto_id,
               pr.nome,
               SUM(i.quantidade) AS unidades_vendidas,
               SUM(i.quantidade * i.preco_unitario_centavos) AS receita_centavos
        FROM itens_pedido i
        JOIN pedidos  p  ON p.id  = i.pedido_id
        JOIN produtos pr ON pr.id = i.produto_id
        WHERE p.status <> 'cancelado'
        GROUP BY pr.id, pr.nome
        ORDER BY receita_centavos DESC, pr.nome
        """
    ).fetchall()
    return [dict(linha) for linha in linhas]


def clientes_top(conn: sqlite3.Connection, limite: int) -> list[dict]:
    linhas = conn.execute(
        """
        SELECT c.id AS cliente_id,
               c.nome,
               COUNT(DISTINCT p.id) AS pedidos,
               SUM(i.quantidade * i.preco_unitario_centavos) AS total_gasto_centavos
        FROM clientes c
        JOIN pedidos      p ON p.cliente_id = c.id
        JOIN itens_pedido i ON i.pedido_id  = p.id
        WHERE p.status <> 'cancelado'
        GROUP BY c.id, c.nome
        ORDER BY total_gasto_centavos DESC, c.nome
        LIMIT ?
        """,
        (limite,),
    ).fetchall()
    return [dict(linha) for linha in linhas]
