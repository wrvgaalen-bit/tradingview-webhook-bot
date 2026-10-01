"""Send a fake TradingView alert to the running bot.

Usage:
    python scripts/send_test_alert.py buy
    python scripts/send_test_alert.py sell --symbol ETH/USDT --amount 0.01
"""

import argparse
import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

parser = argparse.ArgumentParser(description="Send a test alert to the webhook bot")
parser.add_argument("side", choices=["buy", "sell"])
parser.add_argument("--symbol", default="BTC/USDT")
parser.add_argument("--amount", type=float, default=None)
parser.add_argument("--url", default="http://127.0.0.1:8000/webhook")
parser.add_argument("--secret", default=None, help="override the secret (to test rejection)")
args = parser.parse_args()

payload = {
    "secret": args.secret or os.getenv("WEBHOOK_SECRET", ""),
    "symbol": args.symbol,
    "side": args.side,
}
if args.amount is not None:
    payload["amount"] = args.amount

request = urllib.request.Request(
    args.url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=10) as response:
        print(response.status, response.read().decode())
except urllib.error.HTTPError as error:
    print(error.code, error.read().decode())
except urllib.error.URLError as error:
    print("Could not reach the bot. Is `python main.py` running?", error.reason)
