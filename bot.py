import requests
import time
from datetime import datetime, timedelta

TOKEN_CHECK_INTERVAL = 60  # seconds
LIQUIDITY_SPIKE_THRESHOLD = 10000
VOLUME_SPIKE_MULTIPLIER = 3  # spike must exceed 3x average rate
MIN_BASE_VOLUME = 2000  # to trigger alerts for microcap tokens

tracked_tokens = {}

print("🚀 Advanced Momentum Bot Starting...")

def get_recent_tokens():
    # Replace with real API call
    return [{
        "address": "0x123",
        "volume": 7000,
        "liquidity": 22000,
        "tax": 5,
        "locked": True,
        "liquidity_added_tx": True
    }]

def send_alert(token, reason):
    print(f"🚨 ALERT for {token['address']}: {reason}")

def main():
    while True:
        tokens = get_recent_tokens()
        now = datetime.utcnow()

        for token in tokens:
            addr = token["address"]
            if token["tax"] > 10 or not token["locked"]:
                continue

            current_volume = token["volume"]
            current_liquidity = token["liquidity"]

            if addr not in tracked_tokens:
                tracked_tokens[addr] = {
                    "last_volume": current_volume,
                    "last_time": now,
                    "avg_rate": 0,
                    "history": [],
                    "last_liquidity": current_liquidity
                }
                continue

            data = tracked_tokens[addr]
            last_volume = data["last_volume"]
            last_time = data["last_time"]
            last_liquidity = data["last_liquidity"]
            minutes_elapsed = (now - last_time).total_seconds() / 60 or 1

            volume_delta = current_volume - last_volume
            rate_per_minute = volume_delta / minutes_elapsed

            # Update rolling rate history
            data["history"].append(rate_per_minute)
            if len(data["history"]) > 5:
                data["history"].pop(0)

            avg_rate = sum(data["history"]) / len(data["history"])
            data["avg_rate"] = avg_rate

            # 🔥 Adaptive spike logic
            if avg_rate > 0 and rate_per_minute > avg_rate * VOLUME_SPIKE_MULTIPLIER and current_volume > MIN_BASE_VOLUME:
                send_alert(token, f"🔥 Volume surged to {int(rate_per_minute)} $/min (> {VOLUME_SPIKE_MULTIPLIER}x avg)")

            # 🧊 Microcap trigger
            if current_volume < 15000 and volume_delta > 2000:
                send_alert(token, "📈 Microcap token surged over $2K in volume!")

            # 💧 Liquidity spike
            liquidity_delta = current_liquidity - last_liquidity
            if liquidity_delta >= LIQUIDITY_SPIKE_THRESHOLD and token.get("liquidity_added_tx"):
                send_alert(token, f"💧 Liquidity spike: +${liquidity_delta:,} added (locked)")

            # Update tracking data
            data["last_volume"] = current_volume
            data["last_time"] = now
            data["last_liquidity"] = current_liquidity

        time.sleep(TOKEN_CHECK_INTERVAL)

if __name__ == "__main__":
    main()