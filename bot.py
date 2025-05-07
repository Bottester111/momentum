import requests
import time
from datetime import datetime, timedelta

TOKEN_CHECK_INTERVAL = 60  # seconds
SUSTAINED_ALERT_THRESHOLD = 5000  # $5K per minute
SUSTAINED_ALERT_DURATION = 15  # minutes
LIQUIDITY_SPIKE_THRESHOLD = 10000  # Trigger if liquidity increases over $10K in one jump

tracked_tokens = {}

print("🔧 Bot is starting...")

def get_recent_tokens():
    # Placeholder: replace with real API call
    return [{
        "address": "0x123",
        "volume": 50000,
        "liquidity": 25000,
        "tax": 5,
        "locked": True,
        "liquidity_added_tx": True  # Simulated field to indicate if liquidity was added in 1 tx
    }]

def get_token_volume(token):
    return token["volume"]

def get_token_liquidity(token):
    return token["liquidity"]

def is_token_safe(token):
    # Filter out tokens with high tax or not locked liquidity
    return token["tax"] <= 10 and token["locked"] is True

def send_alert(token, reason):
    print(f"🚨 ALERT for {token['address']}: {reason}")

def main():
    while True:
        tokens = get_recent_tokens()
        now = datetime.utcnow()

        for token in tokens:
            addr = token["address"]
            if not is_token_safe(token):
                continue

            current_volume = get_token_volume(token)
            current_liquidity = get_token_liquidity(token)

            if addr not in tracked_tokens:
                tracked_tokens[addr] = {
                    "last_volume": current_volume,
                    "last_time": now,
                    "sustained_start": None,
                    "last_liquidity": current_liquidity
                }
                continue

            last_volume = tracked_tokens[addr]["last_volume"]
            last_time = tracked_tokens[addr]["last_time"]
            last_liquidity = tracked_tokens[addr]["last_liquidity"]

            volume_delta = current_volume - last_volume
            minutes_elapsed = (now - last_time).total_seconds() / 60
            rate_per_minute = volume_delta / max(minutes_elapsed, 1)

            # 🔥 Sustained volume detection
            if rate_per_minute >= SUSTAINED_ALERT_THRESHOLD:
                if not tracked_tokens[addr]["sustained_start"]:
                    tracked_tokens[addr]["sustained_start"] = now
                else:
                    duration = (now - tracked_tokens[addr]["sustained_start"]).total_seconds() / 60
                    if duration >= SUSTAINED_ALERT_DURATION:
                        send_alert(token, f"🔥 Sustained Volume > ${SUSTAINED_ALERT_THRESHOLD}/min for {int(duration)} minutes")
                        tracked_tokens[addr]["sustained_start"] = None
            else:
                tracked_tokens[addr]["sustained_start"] = None

            # 💧 Liquidity spike detection (must be one large tx)
            liquidity_delta = current_liquidity - last_liquidity
            if liquidity_delta >= LIQUIDITY_SPIKE_THRESHOLD and token["locked"] and token.get("liquidity_added_tx"):
                send_alert(token, f"💧 Liquidity Spike: +${liquidity_delta:,} (Locked in 1 tx)")

            # Update tracking
            tracked_tokens[addr]["last_volume"] = current_volume
            tracked_tokens[addr]["last_time"] = now
            tracked_tokens[addr]["last_liquidity"] = current_liquidity

        time.sleep(TOKEN_CHECK_INTERVAL)

if __name__ == "__main__":
    main()