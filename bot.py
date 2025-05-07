import time
import requests
import os
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_BOT_TOKEN)

print("📡 Combined volume + bundle bot running...")

tracked_tokens = {}
bundle_checked = {}

VOLUME_SPIKE_THRESHOLD = 15000  # $15K increase
CHECK_INTERVAL = 60  # seconds
BUNDLE_HOLDER_THRESHOLD = 15
BUNDLE_SUPPLY_PERCENT = 50

def get_token_data():
    try:
        res = requests.get("https://api.dexscreener.com/latest/dex/pairs/abstract")
        if res.status_code == 200:
            return res.json().get("pairs", [])
        return []
    except Exception as e:
        print(f"Error fetching token data: {e}")
        return []

def format_volume_alert(token, delta_volume, age_min):
    symbol = token.get("baseToken", {}).get("symbol", "???")
    address = token.get("pairAddress", "")
    price = token.get("priceUsd", "N/A")
    fdv = token.get("fdv", "N/A")
    liquidity = token.get("liquidity", {}).get("usd", "N/A")
    vol24 = token.get("volume", {}).get("h24", "0")
    ds_link = f"https://dexscreener.com/abstract/{address}"
    looter_link = f"https://t.me/looter_ai_bot?start={address}"
    age_str = f"{age_min}m" if age_min < 60 else f"{age_min//60}h{age_min%60}m"

    text = (
        f"🔥 Volume Spike Detected!\n"
        f"• Ticker: ${symbol}\n"
        f"• Spike: +${int(delta_volume):,} in last {CHECK_INTERVAL}s\n"
        f"• 24h Volume: ${int(float(vol24)):,}\n"
        f"• FDV: ${int(float(fdv)):,}\n"
        f"• Liquidity: ${int(float(liquidity)):,}\n"
        f"• ⏳ Age: {age_str}\n"
        f"• 💸 Price: ${price}\n"
        f"• 📊 Chart: {ds_link}"
    )
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("💰 Buy via Looter", url=looter_link)]])
    return text, markup

def format_bundle_alert(symbol, address, percent, wallet_count):
    ds_link = f"https://dexscreener.com/abstract/{address}"
    text = (
        f"⚠️ Bundle Watch Triggered!\n"
        f"• Ticker: ${symbol}\n"
        f"• {wallet_count} wallets hold {percent}% of supply\n"
        f"• 📊 Chart: {ds_link}"
    )
    markup = InlineKeyboardMarkup([[InlineKeyboardButton("💰 View Chart", url=ds_link)]])
    return text, markup

def check_bundle(token):
    address = token.get("pairAddress")
    symbol = token.get("baseToken", {}).get("symbol", "???")
    
    # Only check bundle if pair is under 84 hours old
    pair_age_hrs = (time.time() - token.get("pairCreatedAt", time.time())) / 3600
    if address in bundle_checked and bundle_checked[address]['last_checked'] + 60 > time.time():
        return
    if pair_age_hrs > 84:
        return
    

    try:
        response = requests.get(f"https://api.abscan.org/api/token/top-holders/{address}")
        data = response.json()

        total_percent = 0
        for i, holder in enumerate(data.get("holders", [])):
            if i >= BUNDLE_HOLDER_THRESHOLD:
                break
            total_percent += float(holder.get("percentage", "0"))

        if total_percent >= BUNDLE_SUPPLY_PERCENT:
            text, markup = format_bundle_alert(symbol, address, round(total_percent, 1), i+1)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, reply_markup=markup)
            print(f"⚠️ Bundle alert: {symbol} - {total_percent}% in {i+1} wallets")

        bundle_checked[address] = {'last_checked': time.time()}
    except Exception as e:
        print(f"Error checking bundle for {address}: {e}")

def monitor_tokens():
    global tracked_tokens
    tokens = get_token_data()
    now = int(time.time())

    for token in tokens:
        try:
            address = token.get("pairAddress")
            if not address:
                continue

            vol = float(token.get("volume", {}).get("h24", 0))
            created = token.get("pairCreatedAt", now)
            age_min = (now - created) // 60

            check_bundle(token)  # Run once per token

            if address in tracked_tokens:
                last_vol, _ = tracked_tokens[address]
                delta = vol - last_vol

                if delta >= VOLUME_SPIKE_THRESHOLD:
                    text, markup = format_volume_alert(token, delta, age_min)
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text, reply_markup=markup)
                    print(f"🚨 Volume alert: ${token.get('baseToken', {}).get('symbol')} +${int(delta)}")

                tracked_tokens[address] = (vol, now)
            else:
                tracked_tokens[address] = (vol, now)

        except Exception as e:
            print(f"Error processing token: {e}")

while True:
    monitor_tokens()
    time.sleep(CHECK_INTERVAL)