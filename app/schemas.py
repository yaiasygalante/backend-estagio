"""Formatos de entrada e saída da API (validação feita pelo Pydantic)."""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# ---------- Clientes ----------
class ClienteEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=255, pattern=EMAIL_REGEX)


class ClienteSaida(BaseModel):
    id: int
    nome: str
    email: str
    criado_em: str


# ---------- Produtos ----------
class ProdutoEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    preco_centavos: int = Field(gt=0, description="Preço em centavos. R$ 25,90 vira 2590.")
    estoque: int = Field(default=0, ge=0)


class ProdutoSaida(BaseModel):
    id: int
    nome: str
    preco_centavos: int
    estoque: int
    criado_em: str


# ---------- Pedidos ----------
StatusPedido = Literal["pendente", "pago", "enviado", "cancelado"]


class ItemEntrada(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class PedidoEntrada(BaseModel):
    cliente_id: int
    itens: list[ItemEntrada] = Field(min_length=1)

    @field_validator("itens")
    @classmethod
    def sem_produto_repetido(cls, itens: list[ItemEntrada]) -> list[ItemEntrada]:
        ids = [item.produto_id for item in itens]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada produto só pode aparecer uma vez no pedido.")
        return itens


class StatusEntrada(BaseModel):
    status: StatusPedido


class ItemSaida(BaseModel):
    produto_id: int
    produto_nome: str
    quantidade: int
    preco_unitario_centavos: int
    subtotal_centavos: int


class PedidoSaida(BaseModel):
    id: int
    cliente_id: int
    status: StatusPedido
    criado_em: str
    total_centavos: int
    itens: list[ItemSaida]


class PedidoResumo(BaseModel):
    id: int
    cliente_id: int
    status: StatusPedido
    criado_em: str
    total_centavos: int


# ---------- Relatórios ----------
class VendaPorProduto(BaseModel):
    produto_id: int
    nome: str
    unidades_vendidas: int
    receita_centavos: int


class ClienteTop(BaseModel):
    cliente_id: int
    nome: str
    pedidos: int
    total_gasto_centavos: int
