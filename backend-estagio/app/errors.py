"""Erros de regra de negócio. A API converte cada um em um código HTTP."""


class NaoEncontrado(Exception):
    """O recurso pedido não existe (HTTP 404)."""


class Conflito(Exception):
    """A operação conflita com o estado atual (HTTP 409)."""
