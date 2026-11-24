"""Endpoints de pedidos: /pedidos."""
import sqlite3

from fastapi import APIRouter, Depends, Query, Response, status

from app import repo_pedidos
from app.database import get_db
from app.schemas import (
    PedidoEntrada,
    PedidoResumo,
    PedidoSaida,
    StatusEntrada,
    StatusPedido,
)

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@router.post("", response_model=PedidoSaida, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    dados: PedidoEntrada, resposta: Response, conn: sqlite3.Connection = Depends(get_db)
):
    pedido = repo_pedidos.criar(conn, dados.cliente_id, dados.itens)
    resposta.headers["Location"] = f"/pedidos/{pedido['id']}"
    return pedido


@router.get("", response_model=list[PedidoResumo])
def listar_pedidos(
    cliente_id: int | None = None,
    status: StatusPedido | None = None,
    limite: int = Query(20, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    return repo_pedidos.listar(conn, cliente_id, status, limite, deslocamento)


@router.get("/{pedido_id}", response_model=PedidoSaida)
def obter_pedido(pedido_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return repo_pedidos.obter(conn, pedido_id)


@router.patch("/{pedido_id}/status", response_model=PedidoSaida)
def mudar_status_do_pedido(
    pedido_id: int, dados: StatusEntrada, conn: sqlite3.Connection = Depends(get_db)
):
    return repo_pedidos.mudar_status(conn, pedido_id, dados.status)
