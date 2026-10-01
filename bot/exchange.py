"""Creates the ccxt exchange connection."""

import ccxt

from bot.config import Settings


def create_exchange(settings: Settings):
    """Return a ccxt exchange instance, on the testnet when sandbox is on."""
    if not hasattr(ccxt, settings.exchange_id):
        raise ValueError(f"Unknown exchange in config.yaml: {settings.exchange_id}")

    exchange_class = getattr(ccxt, settings.exchange_id)
    exchange = exchange_class(
        {
            "apiKey": settings.api_key,
            "secret": settings.api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot", "fetchCurrencies": False},
        }
    )
    if settings.sandbox:
        exchange.set_sandbox_mode(True)
    return exchange
