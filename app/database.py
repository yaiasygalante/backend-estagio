"""Conexão com o banco SQLite e criação das tabelas."""
import os
import sqlite3
from pathlib import Path

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def caminho_do_banco() -> str:
    """Caminho do arquivo do banco. Pode ser trocado pela variável DATABASE_PATH."""
    return os.getenv("DATABASE_PATH", "estagio.db")


def connect(caminho: str | None = None) -> sqlite3.Connection:
    # check_same_thread=False porque o FastAPI pode abrir a conexão numa thread
    # e usá-la em outra durante a mesma requisição.
    conn = sqlite3.connect(caminho or caminho_do_banco(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # o SQLite não confere chaves estrangeiras por padrão
    return conn


def init_db(conn: sqlite3.Connection, com_dados_demo: bool = False) -> None:
    """Cria as tabelas (se não existirem) e, opcionalmente, carrega os dados de demonstração."""
    conn.executescript((SQL_DIR / "schema.sql").read_text(encoding="utf-8"))
    if com_dados_demo:
        conn.executescript((SQL_DIR / "seed.sql").read_text(encoding="utf-8"))
    conn.commit()


def get_db():
    """Dependência do FastAPI: uma conexão por requisição, sempre fechada no fim."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
