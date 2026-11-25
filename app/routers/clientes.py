"""Endpoints de clientes: /clientes."""
import sqlite3

from fastapi import APIRouter, Depends, Query, Response, status

from app import repo_clientes
from app.database import get_db
from app.schemas import ClienteEntrada, ClienteSaida

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteSaida, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    dados: ClienteEntrada, resposta: Response, conn: sqlite3.Connection = Depends(get_db)
):
    cliente = repo_clientes.criar(conn, dados.nome, dados.email)
    resposta.headers["Location"] = f"/clientes/{cliente['id']}"
    return cliente


@router.get("", response_model=list[ClienteSaida])
def listar_clientes(
    limite: int = Query(20, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    return repo_clientes.listar(conn, limite, deslocamento)


@router.get("/{cliente_id}", response_model=ClienteSaida)
def obter_cliente(cliente_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return repo_clientes.obter(conn, cliente_id)


@router.put("/{cliente_id}", response_model=ClienteSaida)
def atualizar_cliente(
    cliente_id: int, dados: ClienteEntrada, conn: sqlite3.Connection = Depends(get_db)
):
    return repo_clientes.atualizar(conn, cliente_id, dados.nome, dados.email)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_cliente(cliente_id: int, conn: sqlite3.Connection = Depends(get_db)):
    repo_clientes.remover(conn, cliente_id)
