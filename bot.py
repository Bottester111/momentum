
import requests
import time
from datetime import datetime
from telegram import Bot

# --- Telegram Setup ---
TELEGRAM_BOT_TOKEN = "7959789156:AAGKNNOSKr5mC-6oelrx6HypmTw4CO5dXSk"
TELEGRAM_CHAT_ID = "-1002500685386"

bot = Bot(token=TELEGRAM_BOT_TOKEN)

try:
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="✅ Expert Momentum Bot started!")
except Exception as e:
    print(f"❌ Failed to send Telegram startup message: {e}")

# --- Configurable Parameters ---
TOKEN_CHECK_INTERVAL = 5  # seconds
VOLUME_SPIKE_MULTIPLIER = 2.5
LIQUIDITY_SPIKE_PERCENT = 50
LIQUIDITY_SPIKE_ABSOLUTE = 5000
VOLUME_HISTORY_WINDOW = 5  # recent checks stored

# --- Storage ---
tracked_tokens = {}

def get_recent_tokens():
    url = "https://api.dexscreener.com/latest/dex/search/?q=abstract"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        tokens = []
        for pair in data.get("pairs", []):
            if "moonshot" in pair.get("url", "").lower():
                token_info = {
                    "address": pair.get("pairAddress"),
                    "name": pair.get("baseToken", {}).get("name", "Unknown"),
                    "symbol": pair.get("baseToken", {}).get("symbol", "???"),
                    "volume": pair.get("volume", {}).get("h1", 0),
                "volume24h": pair.get("volume", {}).get("h24", 0),
                "fdv": pair.get("fdv", 0),
                "priceChange1h": pair.get("priceChange", {}).get("h1", 0),
                "priceChange24h": pair.get("priceChange", {}).get("h24", 0),
                    "liquidity": pair.get("liquidity", {}).get("usd", 0),
                    "url": pair.get("url", ""),
                }
                if token_info["volume24h"] >= 5000:
                tokens.append(token_info)
        return tokens
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

def send_alert(token, reason):
    message = (
        f"🚨 *{token['name']}* (`{token['symbol']}`)
"
        f"{reason}

"
        f"*FDV:* ${int(token['fdv']):,}
"
        f"*24h Volume:* ${int(token['volume24h']):,}
"
        f"*1h Volume:* ${int(token['volume']):,}
"
        f"*Liquidity:* ${int(token['liquidity']):,}
"
        f"*1h Change:* {token['priceChange1h']}%
"
        f"*24h Change:* {token['priceChange24h']}%
"
        f"[📊 View Chart]({token['url']})"
    )
    print(message)
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Failed to send alert: {e}")

def main():
    print("🚀 Expert Momentum Bot Running...")
    while True:
        tokens = get_recent_tokens()
        now = datetime.utcnow()

        for token in tokens:
            addr = token["address"]
            vol = token["volume"]
            liq = token["liquidity"]

            if addr not in tracked_tokens:
                tracked_tokens[addr] = {
                    "volume_history": [],
                    "last_liquidity": liq,
                    "last_alert": None,
                }

            history = tracked_tokens[addr]["volume_history"]
            history.append(vol)
            if len(history) > VOLUME_HISTORY_WINDOW:
                history.pop(0)

            avg_volume = sum(history[:-1]) / max(len(history[:-1]), 1)

            # Volume Spike
            if avg_volume > 0 and vol > avg_volume * VOLUME_SPIKE_MULTIPLIER:
                send_alert(token, f"📈 *Volume spike detected!* (+${int(vol - avg_volume):,})")

            # Liquidity Spike
            prev_liq = tracked_tokens[addr]["last_liquidity"]
            if prev_liq > 0:
                liq_change = liq - prev_liq
                liq_change_pct = (liq_change / prev_liq) * 100
                if liq_change > LIQUIDITY_SPIKE_ABSOLUTE or liq_change_pct > LIQUIDITY_SPIKE_PERCENT:
                    send_alert(token, f"💧 *Liquidity spike detected!* (+${int(liq_change):,}, {liq_change_pct:.1f}%)")

            tracked_tokens[addr]["last_liquidity"] = liq

        time.sleep(TOKEN_CHECK_INTERVAL)

if __name__ == "__main__":
    main()
