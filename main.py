"""Start the webhook server: python main.py"""

import uvicorn

from bot.app import create_app, setup_logging
from bot.config import load_settings
from bot.exchange import create_exchange

settings = load_settings()
setup_logging(settings.log_file)
app = create_app(settings, create_exchange(settings))

if __name__ == "__main__":
    print(
        f"Exchange: {settings.exchange_id} | testnet: {settings.sandbox} | "
        f"dry run: {settings.dry_run} | symbols: {', '.join(settings.allowed_symbols)}"
    )
    uvicorn.run(app, host=settings.host, port=settings.port)
