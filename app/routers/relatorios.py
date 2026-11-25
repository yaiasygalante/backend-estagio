"""Endpoints de relatórios: /relatorios."""
import sqlite3

from fastapi import APIRouter, Depends, Query

from app import repo_relatorios
from app.database import get_db
from app.schemas import ClienteTop, VendaPorProduto

router = APIRouter(prefix="/relatorios", tags=["relatórios"])


@router.get("/vendas-por-produto", response_model=list[VendaPorProduto])
def vendas_por_produto(conn: sqlite3.Connection = Depends(get_db)):
    return repo_relatorios.vendas_por_produto(conn)


@router.get("/clientes-top", response_model=list[ClienteTop])
def clientes_top(limite: int = Query(5, ge=1, le=50), conn: sqlite3.Connection = Depends(get_db)):
    return repo_relatorios.clientes_top(conn, limite)
