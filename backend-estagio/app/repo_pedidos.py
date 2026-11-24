"""Acesso aos dados de pedidos. Criar e cancelar mexem em várias tabelas, então usam transação."""
import sqlite3

from app.errors import Conflito, NaoEncontrado
from app.schemas import ItemEntrada

# De qual status se pode ir para qual. 'enviado' e 'cancelado' são finais.
TRANSICOES = {
    "pendente": {"pago", "cancelado"},
    "pago": {"enviado", "cancelado"},
    "enviado": set(),
    "cancelado": set(),
}

SELECT_RESUMO = """
    SELECT p.id, p.cliente_id, p.status, p.criado_em,
           COALESCE(SUM(i.quantidade * i.preco_unitario_centavos), 0) AS total_centavos
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
"""


def criar(conn: sqlite3.Connection, cliente_id: int, itens: list[ItemEntrada]) -> dict:
    cliente = conn.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if cliente is None:
        raise NaoEncontrado("Cliente não encontrado.")

    # Tudo dentro de um único bloco: se qualquer item falhar, o pedido inteiro é desfeito.
    with conn:
        pedido_id = conn.execute(
            "INSERT INTO pedidos (cliente_id) VALUES (?)", (cliente_id,)
        ).lastrowid
        for item in itens:
            produto = conn.execute(
                "SELECT id, preco_centavos FROM produtos WHERE id = ?", (item.produto_id,)
            ).fetchone()
            if produto is None:
                raise NaoEncontrado(f"Produto {item.produto_id} não encontrado.")
            # Baixa o estoque só se ainda houver quantidade suficiente (checagem e baixa numa só instrução).
            baixa = conn.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item.quantidade, item.produto_id, item.quantidade),
            )
            if baixa.rowcount == 0:
                raise Conflito(f"Estoque insuficiente para o produto {item.produto_id}.")
            conn.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario_centavos) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item.produto_id, item.quantidade, produto["preco_centavos"]),
            )
    return obter(conn, pedido_id)


def obter(conn: sqlite3.Connection, pedido_id: int) -> dict:
    linha = conn.execute(
        SELECT_RESUMO + " WHERE p.id = ? GROUP BY p.id", (pedido_id,)
    ).fetchone()
    if linha is None:
        raise NaoEncontrado("Pedido não encontrado.")
    itens = conn.execute(
        """
        SELECT i.produto_id,
               pr.nome AS produto_nome,
               i.quantidade,
               i.preco_unitario_centavos,
               i.quantidade * i.preco_unitario_centavos AS subtotal_centavos
        FROM itens_pedido i
        JOIN produtos pr ON pr.id = i.produto_id
        WHERE i.pedido_id = ?
        ORDER BY i.id
        """,
        (pedido_id,),
    ).fetchall()
    return {**dict(linha), "itens": [dict(item) for item in itens]}


def listar(
    conn: sqlite3.Connection,
    cliente_id: int | None,
    status: str | None,
    limite: int,
    deslocamento: int,
) -> list[dict]:
    condicoes, parametros = [], []
    if cliente_id is not None:
        condicoes.append("p.cliente_id = ?")
        parametros.append(cliente_id)
    if status is not None:
        condicoes.append("p.status = ?")
        parametros.append(status)
    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    linhas = conn.execute(
        f"{SELECT_RESUMO} {where} GROUP BY p.id ORDER BY p.id LIMIT ? OFFSET ?",
        (*parametros, limite, deslocamento),
    ).fetchall()
    return [dict(linha) for linha in linhas]


def mudar_status(conn: sqlite3.Connection, pedido_id: int, novo_status: str) -> dict:
    with conn:
        atual = conn.execute("SELECT status FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
        if atual is None:
            raise NaoEncontrado("Pedido não encontrado.")
        if novo_status not in TRANSICOES[atual["status"]]:
            raise Conflito(f"Não é possível ir de '{atual['status']}' para '{novo_status}'.")
        if novo_status == "cancelado":
            # Cancelar devolve ao estoque o que o pedido havia reservado.
            conn.execute(
                """
                UPDATE produtos
                SET estoque = estoque + (
                    SELECT i.quantidade FROM itens_pedido i
                    WHERE i.pedido_id = ? AND i.produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )
        conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    return obter(conn, pedido_id)
