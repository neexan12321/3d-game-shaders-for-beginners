#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"
BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"
TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
INTERVAL_MINUTES = 5
ALERT_THRESHOLD_USDT = Decimal("25000000")


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _fmt_decimal(raw: str | Decimal) -> str:
    try:
        value = raw if isinstance(raw, Decimal) else Decimal(raw)
    except (InvalidOperation, TypeError):
        return str(raw)

    return f"{value.quantize(Decimal('1'), rounding=ROUND_HALF_UP):,}"


def _http_get(url: str, params: dict) -> dict | list:
    query = urlencode(params)
    with urlopen(f"{url}?{query}", timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_binance_futures_quote_volume() -> tuple[str, Decimal]:
    now_ms = int(time.time() * 1000)
    rows = _http_get(BINANCE_FUTURES_URL, {"symbol": "BTCUSDT", "interval": "5m", "limit": 3})
    closed = [row for row in rows if int(row[6]) <= now_ms]
    if not closed:
        raise RuntimeError("Binance Futures: no closed candle returned")

    row = closed[-1]
    open_time = int(row[0])
    quote_volume = Decimal(row[7])
    candle_time = datetime.fromtimestamp(open_time / 1000, tz=timezone.utc).strftime("%d-%m %H:%M")
    return candle_time, quote_volume


def _fetch_bybit_futures_quote_volume() -> tuple[str, Decimal]:
    now_ms = int(time.time() * 1000)
    payload = _http_get(BYBIT_KLINE_URL, {"category": "linear", "symbol": "BTCUSDT", "interval": "5", "limit": 5})
    candles = payload.get("result", {}).get("list", [])
    if not candles:
        raise RuntimeError("Bybit Futures: empty response")

    interval_ms = INTERVAL_MINUTES * 60 * 1000
    closed = [c for c in candles if int(c[0]) + interval_ms <= now_ms]
    if not closed:
        raise RuntimeError("Bybit Futures: no closed candle returned")

    row = sorted(closed, key=lambda c: int(c[0]))[-1]
    start_time = int(row[0])
    # turnover is quote volume in USDT.
    quote_volume = Decimal(row[6])
    candle_time = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc).strftime("%d-%m %H:%M")
    return candle_time, quote_volume


def _send_telegram_message(token: str, chat_id: str, text: str) -> None:
    result = _http_post_json(TELEGRAM_SEND_URL.format(token=token), {"chat_id": chat_id, "text": text})
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def _build_alert_if_needed() -> str | None:
    b_time, b_volume = _fetch_binance_futures_quote_volume()
    y_time, y_volume = _fetch_bybit_futures_quote_volume()

    if b_volume > ALERT_THRESHOLD_USDT and y_volume > ALERT_THRESHOLD_USDT:
        return None

    return "\n".join(
        [
            "🚨 BTCUSDT futures low-volume alert (5m)",
            f"Threshold: ≤ {_fmt_decimal(ALERT_THRESHOLD_USDT)} USDT",
            "",
            f"Binance Futures ({b_time}): {_fmt_decimal(b_volume)} USDT",
            f"Bybit Futures ({y_time}): {_fmt_decimal(y_volume)} USDT",
        ]
    )


def _sleep_until_next_5m_boundary() -> None:
    now = time.time()
    interval = INTERVAL_MINUTES * 60
    next_tick = ((int(now) // interval) + 1) * interval
    time.sleep(max(0, next_tick - now + 2))


def main() -> None:
    _load_dotenv()
    token = _require_env("TELEGRAM_BOT_TOKEN")
    chat_id = _require_env("TELEGRAM_CHAT_ID")

    while True:
        try:
            alert = _build_alert_if_needed()
            if alert:
                _send_telegram_message(token, chat_id, alert)
                print(f"Alert sent at {datetime.now(timezone.utc).isoformat()}")
            else:
                print(f"No alert at {datetime.now(timezone.utc).isoformat()}")
        except Exception as exc:  # noqa: BLE001
            msg = f"❌ Failed to evaluate/send futures volume alert: {exc}"
            print(msg)
            try:
                _send_telegram_message(token, chat_id, msg)
            except Exception:
                pass

        _sleep_until_next_5m_boundary()


if __name__ == "__main__":
    main()
