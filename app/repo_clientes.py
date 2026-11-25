"""Acesso aos dados de clientes. Todo SQL usa parâmetros (?) para evitar SQL injection."""
import sqlite3

from app.errors import Conflito, NaoEncontrado


def criar(conn: sqlite3.Connection, nome: str, email: str) -> dict:
    try:
        with conn:  # confirma a transação no fim; desfaz se der erro
            cur = conn.execute("INSERT INTO clientes (nome, email) VALUES (?, ?)", (nome, email))
    except sqlite3.IntegrityError:
        raise Conflito("Já existe um cliente com este e-mail.")
    return obter(conn, cur.lastrowid)


def obter(conn: sqlite3.Connection, cliente_id: int) -> dict:
    linha = conn.execute(
        "SELECT id, nome, email, criado_em FROM clientes WHERE id = ?", (cliente_id,)
    ).fetchone()
    if linha is None:
        raise NaoEncontrado("Cliente não encontrado.")
    return dict(linha)


def listar(conn: sqlite3.Connection, limite: int, deslocamento: int) -> list[dict]:
    linhas = conn.execute(
        "SELECT id, nome, email, criado_em FROM clientes ORDER BY id LIMIT ? OFFSET ?",
        (limite, deslocamento),
    ).fetchall()
    return [dict(linha) for linha in linhas]


def atualizar(conn: sqlite3.Connection, cliente_id: int, nome: str, email: str) -> dict:
    obter(conn, cliente_id)  # garante o 404 antes de tentar alterar
    try:
        with conn:
            conn.execute(
                "UPDATE clientes SET nome = ?, email = ? WHERE id = ?", (nome, email, cliente_id)
            )
    except sqlite3.IntegrityError:
        raise Conflito("Já existe um cliente com este e-mail.")
    return obter(conn, cliente_id)


def remover(conn: sqlite3.Connection, cliente_id: int) -> None:
    obter(conn, cliente_id)
    total = conn.execute(
        "SELECT COUNT(*) FROM pedidos WHERE cliente_id = ?", (cliente_id,)
    ).fetchone()[0]
    if total:
        raise Conflito("Cliente tem pedidos e não pode ser removido.")
    with conn:
        conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
