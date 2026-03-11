#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"
BYBIT_KLINE_URL = "https://api.bybit.com/v5/market/kline"
TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
INTERVAL_MINUTES = 5


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _fmt_decimal(raw: str) -> str:
    try:
        value = Decimal(raw)
    except (InvalidOperation, TypeError):
        return raw

    # Hide fractional "kopecks" and show whole USDT only.
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


def _fetch_binance_volume(symbol: str, market_name: str, url: str) -> tuple[str, str]:
    now_ms = int(time.time() * 1000)
    rows = _http_get(url, {"symbol": symbol, "interval": "5m", "limit": 3})
    closed = [row for row in rows if int(row[6]) <= now_ms]
    if not closed:
        raise RuntimeError(f"{market_name}: no closed candle returned")

    row = closed[-1]
    open_time = int(row[0])
    # Binance kline index 7 is quote asset volume (USDT for BTCUSDT).
    volume = row[7]
    candle_time = datetime.fromtimestamp(open_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return candle_time, volume


def _fetch_bybit_volume(symbol: str, category: str, market_name: str) -> tuple[str, str]:
    now_ms = int(time.time() * 1000)
    payload = _http_get(BYBIT_KLINE_URL, {"category": category, "symbol": symbol, "interval": "5", "limit": 5})
    candles = payload.get("result", {}).get("list", [])
    if not candles:
        raise RuntimeError(f"{market_name}: empty response from Bybit")

    interval_ms = INTERVAL_MINUTES * 60 * 1000
    closed = [c for c in candles if int(c[0]) + interval_ms <= now_ms]
    if not closed:
        raise RuntimeError(f"{market_name}: no closed candle returned")

    row = sorted(closed, key=lambda c: int(c[0]))[-1]
    start_time = int(row[0])
    # Bybit kline index 6 is turnover (quote volume, USDT for BTCUSDT).
    volume = row[6]
    candle_time = datetime.fromtimestamp(start_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return candle_time, volume


def _send_telegram_message(token: str, chat_id: str, text: str) -> None:
    result = _http_post_json(TELEGRAM_SEND_URL.format(token=token), {"chat_id": chat_id, "text": text})
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def build_report() -> str:
    b_fut_t, b_fut_v = _fetch_binance_volume("BTCUSDT", "Binance Futures", BINANCE_FUTURES_URL)
    _b_spot_t, b_spot_v = _fetch_binance_volume("BTCUSDT", "Binance Spot", BINANCE_SPOT_URL)
    _y_fut_t, y_fut_v = _fetch_bybit_volume("BTCUSDT", "linear", "Bybit Futures")
    _y_spot_t, y_spot_v = _fetch_bybit_volume("BTCUSDT", "spot", "Bybit Spot")

    return "\n".join(
        [
            "📊 BTCUSDT 5m candle quote volume (USDT)",
            f"Time: {b_fut_t}",
            "",
            f"Binance Futures BTCUSDT: {_fmt_decimal(b_fut_v)} USDT",
            f"Binance Spot BTCUSDT: {_fmt_decimal(b_spot_v)} USDT",
            "",
            f"Bybit Futures BTCUSDT: {_fmt_decimal(y_fut_v)} USDT",
            f"Bybit Spot BTCUSDT: {_fmt_decimal(y_spot_v)} USDT",
        ]
    )


def _sleep_until_next_5m_boundary() -> None:
    now = time.time()
    interval = INTERVAL_MINUTES * 60
    next_tick = ((int(now) // interval) + 1) * interval
    time.sleep(max(0, next_tick - now + 2))


def main() -> None:
    token = _require_env("TELEGRAM_BOT_TOKEN")
    chat_id = _require_env("TELEGRAM_CHAT_ID")
    send_on_start = os.getenv("SEND_ON_START", "true").lower() in {"1", "true", "yes"}

    if send_on_start:
        _send_telegram_message(token, chat_id, build_report())
        print("Initial report sent")

    while True:
        _sleep_until_next_5m_boundary()
        try:
            _send_telegram_message(token, chat_id, build_report())
            print(f"Report sent at {datetime.now(timezone.utc).isoformat()}")
        except Exception as exc:  # noqa: BLE001
            msg = f"❌ Failed to fetch/send BTCUSDT volume report: {exc}"
            print(msg)
            try:
                _send_telegram_message(token, chat_id, msg)
            except Exception:
                pass


if __name__ == "__main__":
    main()
