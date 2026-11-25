"""Acesso aos dados de produtos."""
import sqlite3

from app.errors import Conflito, NaoEncontrado

COLUNAS = "id, nome, preco_centavos, estoque, criado_em"


def criar(conn: sqlite3.Connection, nome: str, preco_centavos: int, estoque: int) -> dict:
    with conn:
        cur = conn.execute(
            "INSERT INTO produtos (nome, preco_centavos, estoque) VALUES (?, ?, ?)",
            (nome, preco_centavos, estoque),
        )
    return obter(conn, cur.lastrowid)


def obter(conn: sqlite3.Connection, produto_id: int) -> dict:
    linha = conn.execute(f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    if linha is None:
        raise NaoEncontrado("Produto não encontrado.")
    return dict(linha)


def listar(
    conn: sqlite3.Connection,
    busca: str | None,
    apenas_com_estoque: bool,
    limite: int,
    deslocamento: int,
) -> list[dict]:
    # O SQL é montado só com trechos fixos; os valores sempre vão como parâmetros.
    condicoes, parametros = [], []
    if busca:
        condicoes.append("nome LIKE ?")
        parametros.append(f"%{busca}%")
    if apenas_com_estoque:
        condicoes.append("estoque > 0")
    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    linhas = conn.execute(
        f"SELECT {COLUNAS} FROM produtos {where} ORDER BY id LIMIT ? OFFSET ?",
        (*parametros, limite, deslocamento),
    ).fetchall()
    return [dict(linha) for linha in linhas]


def atualizar(
    conn: sqlite3.Connection, produto_id: int, nome: str, preco_centavos: int, estoque: int
) -> dict:
    obter(conn, produto_id)
    with conn:
        conn.execute(
            "UPDATE produtos SET nome = ?, preco_centavos = ?, estoque = ? WHERE id = ?",
            (nome, preco_centavos, estoque, produto_id),
        )
    return obter(conn, produto_id)


def remover(conn: sqlite3.Connection, produto_id: int) -> None:
    obter(conn, produto_id)
    total = conn.execute(
        "SELECT COUNT(*) FROM itens_pedido WHERE produto_id = ?", (produto_id,)
    ).fetchone()[0]
    if total:
        raise Conflito("Produto aparece em pedidos e não pode ser removido.")
    with conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
