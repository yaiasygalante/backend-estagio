"""Testes da API. Cada teste usa um banco novo e temporário, então nada fica salvo entre eles."""
import pytest
from fastapi.testclient import TestClient

from app.database import connect, get_db, init_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    arquivo = str(tmp_path / "teste.db")
    conn = connect(arquivo)
    init_db(conn)
    conn.close()

    def banco_de_teste():
        conn = connect(arquivo)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = banco_de_teste
    # Sem "with": não dispara o ciclo de vida, que criaria o banco padrão no disco.
    yield TestClient(app)
    app.dependency_overrides.clear()


def criar_cliente(client, nome="Ana", email="ana@exemplo.com"):
    resposta = client.post("/clientes", json={"nome": nome, "email": email})
    assert resposta.status_code == 201
    return resposta.json()


def criar_produto(client, nome="Teclado", preco=10000, estoque=10):
    resposta = client.post(
        "/produtos", json={"nome": nome, "preco_centavos": preco, "estoque": estoque}
    )
    assert resposta.status_code == 201
    return resposta.json()


def criar_pedido(client, cliente_id, itens):
    return client.post("/pedidos", json={"cliente_id": cliente_id, "itens": itens})


# ---------- Infra ----------
def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


# ---------- Clientes ----------
def test_criar_cliente_devolve_201_e_location(client):
    resposta = client.post("/clientes", json={"nome": "Ana", "email": "ana@exemplo.com"})
    assert resposta.status_code == 201
    assert resposta.headers["Location"] == f"/clientes/{resposta.json()['id']}"


def test_email_duplicado_devolve_409(client):
    criar_cliente(client)
    resposta = client.post("/clientes", json={"nome": "Outra", "email": "ana@exemplo.com"})
    assert resposta.status_code == 409


def test_email_invalido_devolve_422(client):
    resposta = client.post("/clientes", json={"nome": "Ana", "email": "isso-nao-e-email"})
    assert resposta.status_code == 422


def test_cliente_inexistente_devolve_404(client):
    assert client.get("/clientes/999").status_code == 404


def test_atualizar_e_remover_cliente(client):
    cliente = criar_cliente(client)
    resposta = client.put(
        f"/clientes/{cliente['id']}", json={"nome": "Ana Maria", "email": "ana@exemplo.com"}
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Ana Maria"
    assert client.delete(f"/clientes/{cliente['id']}").status_code == 204
    assert client.get(f"/clientes/{cliente['id']}").status_code == 404


def test_paginacao_de_clientes(client):
    for i in range(5):
        criar_cliente(client, nome=f"Cliente {i}", email=f"c{i}@exemplo.com")
    pagina = client.get("/clientes", params={"limite": 2, "deslocamento": 2}).json()
    assert [c["nome"] for c in pagina] == ["Cliente 2", "Cliente 3"]


def test_limite_acima_do_maximo_devolve_422(client):
    assert client.get("/clientes", params={"limite": 1000}).status_code == 422


# ---------- Produtos ----------
def test_preco_precisa_ser_positivo(client):
    resposta = client.post("/produtos", json={"nome": "X", "preco_centavos": 0, "estoque": 1})
    assert resposta.status_code == 422


def test_busca_e_filtro_de_estoque(client):
    criar_produto(client, nome="Teclado mecânico", estoque=5)
    criar_produto(client, nome="Teclado simples", estoque=0)
    criar_produto(client, nome="Mouse", estoque=3)
    por_nome = client.get("/produtos", params={"busca": "teclado"}).json()
    assert len(por_nome) == 2
    com_estoque = client.get(
        "/produtos", params={"busca": "teclado", "apenas_com_estoque": True}
    ).json()
    assert [p["nome"] for p in com_estoque] == ["Teclado mecânico"]


# ---------- Pedidos ----------
def test_criar_pedido_calcula_total_e_baixa_estoque(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client, preco=2500, estoque=10)
    resposta = criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 3}])
    assert resposta.status_code == 201
    pedido = resposta.json()
    assert pedido["status"] == "pendente"
    assert pedido["total_centavos"] == 7500
    assert pedido["itens"][0]["subtotal_centavos"] == 7500
    assert client.get(f"/produtos/{produto['id']}").json()["estoque"] == 7


def test_estoque_insuficiente_devolve_409_e_nao_deixa_rastro(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client, estoque=2)
    resposta = criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 5}])
    assert resposta.status_code == 409
    assert client.get(f"/produtos/{produto['id']}").json()["estoque"] == 2
    assert client.get("/pedidos").json() == []


def test_falha_no_segundo_item_desfaz_o_primeiro(client):
    cliente = criar_cliente(client)
    bom = criar_produto(client, nome="Bom", estoque=5)
    ruim = criar_produto(client, nome="Ruim", estoque=1)
    resposta = criar_pedido(
        client,
        cliente["id"],
        [{"produto_id": bom["id"], "quantidade": 2}, {"produto_id": ruim["id"], "quantidade": 9}],
    )
    assert resposta.status_code == 409
    assert client.get(f"/produtos/{bom['id']}").json()["estoque"] == 5  # a baixa foi revertida


def test_pedido_com_cliente_ou_produto_inexistente_devolve_404(client):
    produto = criar_produto(client)
    assert criar_pedido(client, 999, [{"produto_id": produto["id"], "quantidade": 1}]).status_code == 404
    cliente = criar_cliente(client)
    assert criar_pedido(client, cliente["id"], [{"produto_id": 999, "quantidade": 1}]).status_code == 404


def test_produto_repetido_no_pedido_devolve_422(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client)
    itens = [{"produto_id": produto["id"], "quantidade": 1}] * 2
    assert criar_pedido(client, cliente["id"], itens).status_code == 422


def test_preco_do_pedido_nao_muda_quando_o_produto_muda(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client, preco=1000, estoque=5)
    pedido = criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 1}]).json()
    client.put(
        f"/produtos/{produto['id']}",
        json={"nome": produto["nome"], "preco_centavos": 9999, "estoque": 4},
    )
    assert client.get(f"/pedidos/{pedido['id']}").json()["total_centavos"] == 1000


def test_fluxo_de_status_valido(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client)
    pedido = criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 1}]).json()
    for novo in ("pago", "enviado"):
        resposta = client.patch(f"/pedidos/{pedido['id']}/status", json={"status": novo})
        assert resposta.status_code == 200
        assert resposta.json()["status"] == novo


def test_transicao_invalida_devolve_409(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client)
    pedido = criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 1}]).json()
    resposta = client.patch(f"/pedidos/{pedido['id']}/status", json={"status": "enviado"})
    assert resposta.status_code == 409


def test_cancelar_devolve_o_estoque(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client, estoque=10)
    pedido = criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 4}]).json()
    assert client.get(f"/produtos/{produto['id']}").json()["estoque"] == 6
    resposta = client.patch(f"/pedidos/{pedido['id']}/status", json={"status": "cancelado"})
    assert resposta.status_code == 200
    assert client.get(f"/produtos/{produto['id']}").json()["estoque"] == 10


def test_filtrar_pedidos_por_status_e_cliente(client):
    ana = criar_cliente(client, "Ana", "ana@exemplo.com")
    bia = criar_cliente(client, "Bia", "bia@exemplo.com")
    produto = criar_produto(client, estoque=20)
    item = [{"produto_id": produto["id"], "quantidade": 1}]
    criar_pedido(client, ana["id"], item)
    segundo = criar_pedido(client, bia["id"], item).json()
    client.patch(f"/pedidos/{segundo['id']}/status", json={"status": "pago"})
    assert len(client.get("/pedidos", params={"status": "pago"}).json()) == 1
    assert len(client.get("/pedidos", params={"cliente_id": ana["id"]}).json()) == 1


def test_nao_remove_cliente_nem_produto_com_pedido(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client)
    criar_pedido(client, cliente["id"], [{"produto_id": produto["id"], "quantidade": 1}])
    assert client.delete(f"/clientes/{cliente['id']}").status_code == 409
    assert client.delete(f"/produtos/{produto['id']}").status_code == 409


# ---------- Relatórios ----------
def test_relatorio_de_vendas_ignora_pedido_cancelado(client):
    cliente = criar_cliente(client)
    produto = criar_produto(client, preco=1000, estoque=20)
    item = [{"produto_id": produto["id"], "quantidade": 2}]
    criar_pedido(client, cliente["id"], item)
    cancelado = criar_pedido(client, cliente["id"], item).json()
    client.patch(f"/pedidos/{cancelado['id']}/status", json={"status": "cancelado"})
    vendas = client.get("/relatorios/vendas-por-produto").json()
    assert vendas == [
        {"produto_id": produto["id"], "nome": "Teclado", "unidades_vendidas": 2, "receita_centavos": 2000}
    ]


def test_relatorio_de_clientes_top_ordena_por_gasto(client):
    ana = criar_cliente(client, "Ana", "ana@exemplo.com")
    bia = criar_cliente(client, "Bia", "bia@exemplo.com")
    produto = criar_produto(client, preco=1000, estoque=50)
    criar_pedido(client, ana["id"], [{"produto_id": produto["id"], "quantidade": 1}])
    criar_pedido(client, bia["id"], [{"produto_id": produto["id"], "quantidade": 5}])
    top = client.get("/relatorios/clientes-top", params={"limite": 1}).json()
    assert [c["nome"] for c in top] == ["Bia"]
    assert top[0]["total_gasto_centavos"] == 5000
