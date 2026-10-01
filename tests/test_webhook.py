"""Tests run without an exchange or internet: a fake exchange records orders."""

from dataclasses import replace

import ccxt
import pytest
from fastapi.testclient import TestClient

from bot.app import create_app
from bot.config import Settings

SECRET = "test-secret-1234567890"

BASE_SETTINGS = Settings(
    exchange_id="binance",
    sandbox=True,
    dry_run=False,
    allowed_symbols=("BTC/USDT",),
    default_amount=0.001,
    max_amount=0.01,
    host="127.0.0.1",
    port=8000,
    log_file="test.log",
    api_key="",
    api_secret="",
    webhook_secret=SECRET,
)


class FakeExchange:
    def __init__(self, fail=False):
        self.orders = []
        self.fail = fail

    def create_order(self, symbol, order_type, side, amount):
        if self.fail:
            raise ccxt.InsufficientFunds("not enough balance")
        self.orders.append((symbol, order_type, side, amount))
        return {"id": "123", "status": "closed"}


def client_for(settings=BASE_SETTINGS, exchange=None):
    exchange = exchange or FakeExchange()
    return TestClient(create_app(settings, exchange)), exchange


def test_valid_alert_places_order():
    client, exchange = client_for()
    r = client.post("/webhook", json={"secret": SECRET, "symbol": "btc/usdt", "side": "buy"})
    assert r.status_code == 200
    assert exchange.orders == [("BTC/USDT", "market", "buy", 0.001)]


def test_wrong_secret_is_rejected():
    client, exchange = client_for()
    r = client.post("/webhook", json={"secret": "wrong", "symbol": "BTC/USDT", "side": "buy"})
    assert r.status_code == 401
    assert exchange.orders == []


def test_unknown_symbol_is_rejected():
    client, exchange = client_for()
    r = client.post("/webhook", json={"secret": SECRET, "symbol": "DOGE/USDT", "side": "buy"})
    assert r.status_code == 400
    assert exchange.orders == []


def test_amount_above_max_is_rejected():
    client, exchange = client_for()
    r = client.post(
        "/webhook", json={"secret": SECRET, "symbol": "BTC/USDT", "side": "buy", "amount": 5}
    )
    assert r.status_code == 400
    assert exchange.orders == []


@pytest.mark.parametrize("side", ["hold", "BUY!", ""])
def test_invalid_side_is_rejected(side):
    client, exchange = client_for()
    r = client.post("/webhook", json={"secret": SECRET, "symbol": "BTC/USDT", "side": side})
    assert r.status_code == 422
    assert exchange.orders == []


def test_dry_run_places_no_order():
    client, exchange = client_for(replace(BASE_SETTINGS, dry_run=True))
    r = client.post("/webhook", json={"secret": SECRET, "symbol": "BTC/USDT", "side": "sell"})
    assert r.json()["status"] == "dry_run"
    assert exchange.orders == []


def test_exchange_error_returns_502():
    client, _ = client_for(exchange=FakeExchange(fail=True))
    r = client.post("/webhook", json={"secret": SECRET, "symbol": "BTC/USDT", "side": "buy"})
    assert r.status_code == 502


def test_health():
    client, _ = client_for()
    assert client.get("/health").json()["sandbox"] is True
