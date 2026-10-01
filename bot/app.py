"""FastAPI app that turns TradingView alerts into exchange orders."""

import hmac
import logging
from typing import Literal

import ccxt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from bot.config import Settings

logger = logging.getLogger("webhook-bot")


class Alert(BaseModel):
    """The JSON body TradingView sends with each alert."""

    secret: str
    symbol: str
    side: Literal["buy", "sell"]
    amount: float | None = Field(default=None, gt=0)


def setup_logging(log_file: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def create_app(settings: Settings, exchange) -> FastAPI:
    app = FastAPI(title="TradingView Webhook Bot")

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "exchange": settings.exchange_id,
            "sandbox": settings.sandbox,
            "dry_run": settings.dry_run,
        }

    @app.post("/webhook")
    def webhook(alert: Alert):
        # 1. Only accept alerts that carry the shared secret
        if not hmac.compare_digest(alert.secret, settings.webhook_secret):
            logger.warning("Rejected alert: wrong secret")
            raise HTTPException(status_code=401, detail="Invalid secret")

        # 2. Only trade symbols that are explicitly allowed
        symbol = alert.symbol.upper()
        if symbol not in settings.allowed_symbols:
            logger.warning("Rejected alert: symbol %s not allowed", symbol)
            raise HTTPException(status_code=400, detail=f"Symbol {symbol} not allowed")

        # 3. Never exceed the maximum order size
        amount = alert.amount or settings.default_amount
        if amount > settings.max_amount:
            logger.warning("Rejected alert: amount %s above max %s", amount, settings.max_amount)
            raise HTTPException(status_code=400, detail="Amount above max_amount")

        logger.info("Alert received: %s %s %s", alert.side, amount, symbol)

        # 4. Dry run: log what would happen, place nothing
        if settings.dry_run:
            logger.info("DRY RUN: no order placed")
            return {"status": "dry_run", "symbol": symbol, "side": alert.side, "amount": amount}

        # 5. Place the market order
        try:
            order = exchange.create_order(symbol, "market", alert.side, amount)
        except ccxt.BaseError as error:
            logger.error("Order failed: %s", error)
            raise HTTPException(status_code=502, detail=f"Exchange error: {error}")

        logger.info("Order placed: id=%s status=%s", order.get("id"), order.get("status"))
        return {
            "status": "ok",
            "order_id": order.get("id"),
            "symbol": symbol,
            "side": alert.side,
            "amount": amount,
        }

    return app
