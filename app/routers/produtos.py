"""Endpoints de produtos: /produtos."""
import sqlite3

from fastapi import APIRouter, Depends, Query, Response, status

from app import repo_produtos
from app.database import get_db
from app.schemas import ProdutoEntrada, ProdutoSaida

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.post("", response_model=ProdutoSaida, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoEntrada, resposta: Response, conn: sqlite3.Connection = Depends(get_db)
):
    produto = repo_produtos.criar(conn, dados.nome, dados.preco_centavos, dados.estoque)
    resposta.headers["Location"] = f"/produtos/{produto['id']}"
    return produto


@router.get("", response_model=list[ProdutoSaida])
def listar_produtos(
    busca: str | None = Query(None, max_length=60, description="Parte do nome do produto."),
    apenas_com_estoque: bool = False,
    limite: int = Query(20, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    return repo_produtos.listar(conn, busca, apenas_com_estoque, limite, deslocamento)


@router.get("/{produto_id}", response_model=ProdutoSaida)
def obter_produto(produto_id: int, conn: sqlite3.Connection = Depends(get_db)):
    return repo_produtos.obter(conn, produto_id)


@router.put("/{produto_id}", response_model=ProdutoSaida)
def atualizar_produto(
    produto_id: int, dados: ProdutoEntrada, conn: sqlite3.Connection = Depends(get_db)
):
    return repo_produtos.atualizar(
        conn, produto_id, dados.nome, dados.preco_centavos, dados.estoque
    )


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(produto_id: int, conn: sqlite3.Connection = Depends(get_db)):
    repo_produtos.remover(conn, produto_id)
