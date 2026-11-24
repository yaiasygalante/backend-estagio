"""Cria o banco pela linha de comando.

Uso:
    python -m app.init_db            # só as tabelas
    python -m app.init_db --demo     # tabelas e dados de demonstração
"""
import sys

from app.database import caminho_do_banco, connect, init_db

if __name__ == "__main__":
    conn = connect()
    init_db(conn, com_dados_demo="--demo" in sys.argv)
    conn.close()
    print(f"Banco pronto em {caminho_do_banco()}")
