"""Aplicação FastAPI: monta as rotas e traduz erros de negócio em respostas HTTP.

Para rodar:  uvicorn app.main:app --reload
Documentação interativa (Swagger): http://127.0.0.1:8000/docs
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import connect, init_db
from app.errors import Conflito, NaoEncontrado
from app.routers import clientes, pedidos, produtos, relatorios


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Ao subir, garante que as tabelas existem. SEED_DEMO=1 também carrega os dados de exemplo.
    conn = connect()
    try:
        init_db(conn, com_dados_demo=os.getenv("SEED_DEMO") == "1")
    finally:
        conn.close()
    yield


app = FastAPI(
    title="API de Pedidos",
    description="API RESTful em Python com SQL (SQLite): clientes, produtos e pedidos.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.include_router(clientes.router)
app.include_router(produtos.router)
app.include_router(pedidos.router)
app.include_router(relatorios.router)


@app.exception_handler(NaoEncontrado)
async def tratar_nao_encontrado(request: Request, erro: NaoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(erro)})


@app.exception_handler(Conflito)
async def tratar_conflito(request: Request, erro: Conflito):
    return JSONResponse(status_code=409, content={"detail": str(erro)})


@app.get("/health", tags=["infra"])
def verificar_saude():
    """Usado para checar se a API está no ar."""
    return {"status": "ok"}
