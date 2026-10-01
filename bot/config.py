"""Loads settings from config.yaml (non-secret) and .env (secrets)."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    exchange_id: str
    sandbox: bool
    dry_run: bool
    allowed_symbols: tuple[str, ...]
    default_amount: float
    max_amount: float
    host: str
    port: int
    log_file: str
    api_key: str
    api_secret: str
    webhook_secret: str


def load_settings(config_path: str | Path = "config.yaml") -> Settings:
    """Read config.yaml and .env and return one validated Settings object."""
    load_dotenv()

    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    exchange = cfg.get("exchange", {})
    trading = cfg.get("trading", {})
    server = cfg.get("server", {})

    webhook_secret = os.getenv("WEBHOOK_SECRET", "").strip()
    if len(webhook_secret) < 16:
        raise ValueError(
            "WEBHOOK_SECRET in .env is missing or shorter than 16 characters."
        )

    default_amount = float(trading.get("default_amount", 0.001))
    max_amount = float(trading.get("max_amount", 0.01))
    if default_amount > max_amount:
        raise ValueError("default_amount cannot be larger than max_amount.")

    return Settings(
        exchange_id=exchange.get("id", "binance"),
        sandbox=bool(exchange.get("sandbox", True)),
        dry_run=bool(trading.get("dry_run", True)),
        allowed_symbols=tuple(s.upper() for s in trading.get("allowed_symbols", [])),
        default_amount=default_amount,
        max_amount=max_amount,
        host=server.get("host", "127.0.0.1"),
        port=int(server.get("port", 8000)),
        log_file=server.get("log_file", "bot.log"),
        api_key=os.getenv("EXCHANGE_API_KEY", "").strip(),
        api_secret=os.getenv("EXCHANGE_API_SECRET", "").strip(),
        webhook_secret=webhook_secret,
    )
