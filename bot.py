import pandas as pd
import requests
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import ConversationHandler, MessageHandler, filters

#Now starts importing of additional new features/updates!
from signal_engine import generate_signal
from bitnode_signal import get_bitnode_signal
from entry_time_calculator import get_next_candle_time
from datetime import datetime
from helpers import support_resistance_volume
from adx_indicator import calculate_adx
from fib_retracement import calculate_fibonacci_levels
from supertrend_indicator import calculate_supertrend
from trading_view_old import calculate_pine_signal

feedback_results = []

def timeframe_to_minutes(tf: str) -> int:
    tf = tf.lower().strip()
    if tf.endswith("m"):
        return int(tf[:-1])  # e.g., "5m" -> 5
    elif tf.endswith("h"):
        return int(tf[:-1]) * 60  # e.g., "1h" -> 60
    elif tf.endswith("d"):
        return int(tf[:-1]) * 60 * 24  # e.g., "1d" -> 1440
    else:
        # Agar user sirf number de de, wo bhi handle karlo
        return int(tf)

# Random reply list for "Thanks" or "Thank you"
thanks_replies = [
    "Ayy, anytime for you, Wasif Sir 😎",
    "Always got your back, Wasif 🤠",
    "No need to thank me, Wasif we are a team! 🤝",
    "You are welcome, sir anytime! 😇",
    "Of course, Wasif! Mein kisliye hun? 🤗",
    "Wasif, my man! You know I got you. 🥱",
    "All in a days work for Wasif squad! 🔥",
    "No worries, Wasif just another heroic moment 😄",
    "Chill karen, genius Wasif 👑",
    "No worries, Wasif! Got you covered like WiFi 😄"
]

# === Profit & Loss Replies ===
profit_replies = [
    "Congratulations, Sir! Thats a smart and well timed entry 💪",
    "Great job, Wasif your analysis paid off perfectly 👍",
    "Impressive work, Sir. You are mastering this game 😏",
    "Ayee haaye, Wasif Sir! Profit ka to toofaan le aaye ho 🤑",
    "Boom! Profit in bag Sir, aap genius ho 😎",
    "Yeh hui na baat! Ab to market bhi dar rahi hogi aap se 😄"
]

loss_replies = [
    "Im sorry, Sir every loss is a lesson. We will recover stronger 💪",
    "Tough luck, Wasif Lets learn from this and move forward 😇",
    "Losses happen to the best. Next time, we will nail it together 😊",
    "Sir, market ne wicket leli! Par koi nahi, agli baar chhakka lagayen gen 😎",
    "Loss hua? Market se badla lenge, in our style 🔥",
    "Sir, market ne thoda attitude dikhaya, ab hum dikhayenge 😎"
]

# Function to respond to "thanks" messages
async def handle_thanks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.lower()
    if "thank you" in message_text or "thanks" in message_text:
        reply = random.choice(thanks_replies)
        await update.message.reply_text(reply)


BOT_TOKEN = "7392528355:AAEM3coa4LPdxi-peofiGKYMoVjGpsl2s9k"  # Replace with your actual bot token


# === Step 1: Ask for Pair ===
async def start_custom_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sir, please enter the coin")
    return ASK_PAIR

# === Step 2: Ask for Timeframe ===
async def received_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["pair"] = update.message.text.strip().upper()
    await update.message.reply_text("Now enter the timeframe")
    return ASK_TIMEFRAME

# Conversation states
ASK_PAIR, ASK_TIMEFRAME = range(2)

# === Fetch Binance Data ===
def fetch_binance_data(symbol: str, timeframe: str):
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={symbol}&interval={timeframe}&limit=1"
    mexc_url = f"https://api.mexc.com/api/v3/klines?symbol={symbol}&interval={timeframe}&limit=1"

    for url_name, url in [("Binance", url), ("MEXC", mexc_url)]:
        try:
            res = requests.get(url, timeout=5)
            res.raise_for_status()
            candle = res.json()[0]

            open_price = float(candle[1])
            high = float(candle[2])
            low = float(candle[3])
            close = float(candle[4])

            direction = "LONG ⬆️" if close > open_price else "SHORT ⬇️"
            entry = close
            stop = low if direction.startswith("LONG") else high
            take = close * 1.015 if direction.startswith("LONG") else close * 0.985

            return {
                "pair": symbol,
                "timeframe": timeframe,
                "direction": direction,
                "entry": round(entry, 9),
                "stop_loss": round(stop, 9),
                "take_profit": round(take, 9),
                # "confidence": "75%"
        }
        except Exception as e:
            print(f'{url_name} failed: {e}')
            continue  # Try the next URL if this one fails

    return {"error": 'Data not available from both Binance and MEXC.'}

# === Step 3: Generate Signal ===

async def received_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = context.user_data.get("pair")
    timeframe = update.message.text.strip()

    binance_url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval={timeframe}&limit=150"
    mexc_url = f"https://api.mexc.com/api/v3/klines?symbol={pair}&interval={timeframe}&limit=150"

    candles = None
    for url_name, url in [("Binance", binance_url), ("MEXC", mexc_url)]:
        try:
            res = requests.get(url, timeout=5)
            res.raise_for_status()
            candles = res.json()
            if candles:
                break
        except Exception as e:
            print(f"{url_name} fetch failed: {e}")
            continue

    if not candles:
        await update.message.reply_text("☹️ Data not available from both Binance and MEXC.")
        return ConversationHandler.END

    if len(candles[0]) == 12:
        df = pd.DataFrame(candles, columns=[
            "open_time", "open", "high", "low", "close", "volume", "close_time",
            "quote_asset_volume", "number_of_trades", "taker_buy_base", 
            "taker_buy_quote", "ignore"
        ])
    elif len(candles[0]) == 8:
        df = pd.DataFrame(candles, columns=[
            "open_time", "open", "high", "low", "close", "volume", "close_time", "ignore"
        ])
    else:
        await update.message.reply_text("😦 Unexpected candle format from exchange.")
        return ConversationHandler.END


    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col])

    # # Generate signal
    # direction_map = {
    #     "LONG": "LONG ⬆️",
    #     "SHORT": "SHORT ⬇️",
    #     "NO SIGNAL": "NO CLEAR SIGNAL ⚠️"
    # }

    #Call section!
    signal_info = generate_signal(df)
    signal_type = signal_info.get("signal", "NO SIGNAL")
    rsi_value = signal_info.get("rsi", 0)
    ema_value = signal_info.get("ema9", 0)  # ✅ New
    bb_upper = signal_info.get("bb_upper", 0) # ✅ New
    bb_lower = signal_info.get("bb_lower", 0) # ✅ New
    extra = support_resistance_volume(df, timeframe) # ✅ New
    adx_data = calculate_adx(df) # ✅ New
    adx_value = adx_data["adx"] # ✅ New
    plus_di = adx_data["plus_di"] # ✅ New
    minus_di = adx_data["minus_di"] # ✅ New
    fib_data = calculate_fibonacci_levels(df) # ✅ New
    supertrend = calculate_supertrend(df, period=10, multiplier=3.0)
    supertrend_signal = supertrend.get("supertrend_signal", 'NO SIGNAL')
    trading_view = calculate_pine_signal(df)

    # signals = {
    # "Supertrend": supertrend.get("supertrend_signal", "NO SIGNAL")
    # }

    # supertrend_signal = supertrend.get("supertrend_signal", "NO SIGNAL")

    # Combine signals with confidence-based approach
    signals = {
        "RSI": signal_info["rsi_signal"],
        "EMA": signal_info["ema_signal"],
        "BB": signal_info["bb_signal"],
        "ADX": adx_data["signal"],
        "Fibonacci": fib_data["signal"],
        "Support/Resistance": extra["signal"],
        # "Supertrend": supertrend_signal["supertrend_signal"]
        "supertrend_signal": supertrend_signal,
        "trading_view": trading_view
    }

    # ✅ Step 1: Define indicator signals
    indicator_signals = {
        "RSI": signal_info["rsi_signal"],
        "EMA": signal_info["ema_signal"],
        "BB": signal_info["bb_signal"],
        "Support/Resistance": extra["signal"],
        "ADX": adx_data["signal"],
        "Fibonacci": fib_data["signal"],
        "supertrend_signal": supertrend_signal,
        "trading_view": trading_view
    }

    # ✅ Step 2: Filter only LONG/SHORT signals
    valid_signals = {
        k: v.strip().upper()
        for k, v in indicator_signals.items()
        if v.strip().upper() in ["LONG", "SHORT"]
    }

    # ✅ Step 3: Apply voting logic

    long_score = 0  # ✅ initialize before use
    short_score = 0

    if not valid_signals:
        long_confidence = 0
        short_confidence = 0
    else:
        indicator_weight = 90 / len(valid_signals)
        long_score = 0
        short_score = 0

        for name, signal in valid_signals.items():
            if signal == "LONG":
                long_score += indicator_weight
            elif signal == "SHORT":
                short_score += indicator_weight

        long_confidence = round(long_score, 2)
        short_confidence = round(short_score, 2)

    # Default final signal
    final_signal = "NO SIGNAL"

    # Decide based on weighted voting
    if long_score == 0 and short_score == 0:
        final_signal = "NO SIGNAL"
    elif abs(long_score - short_score) < 1e-3:
        if adx_value > 25:
            final_signal = adx_data["signal"]
        else:
            final_signal = "NO SIGNAL"
    elif long_score > short_score:
        final_signal = "LONG"
    else:
        final_signal = "SHORT"

    # Also assign to display
    long_confidence = long_score
    short_confidence = short_score

    # Generate signal details
    direction_map = {
        "LONG": "LONG ⬆️",
        "SHORT": "SHORT ⬇️",
        "NO SIGNAL": "NO CLEAR SIGNAL ⚠️"
    }

    # ⭐ Add star emoji to higher confidence signal
    star_long = " ⭐" if long_confidence > short_confidence else ""
    star_short = " ⭐" if short_confidence > long_confidence else ""

    current_time = datetime.now()
    timeframe_minutes = timeframe_to_minutes(timeframe)
    entry_time = get_next_candle_time(current_time, timeframe_minutes)

    direction_text = direction_map.get(final_signal, 'NO CLEAR SIGNAL ⚠️')

    if final_signal == "LONG":
        entry = df["close"].iloc[-1]
        stop_loss = df["low"].iloc[-1]
        take_profit = entry * 1.015
    elif final_signal == "SHORT":
        entry = df["close"].iloc[-1]
        stop_loss = df["high"].iloc[-1]
        take_profit = entry * 0.985
    else:
        entry = stop_loss = take_profit = None

    msg = (
        f"📢 *Your Trade Signal!*\n\n"
        f"Pair: {pair}\n"
        f"Timeframe: {timeframe}\n\n"
        f"Direction: {direction_text}\n"
        f"Entry Time: {entry_time} 🕔\n\n"
    )

    if entry:
        msg += (
            f"Entry Price: ${entry:.9f}\n"
            f"Stop Loss: ${stop_loss:.9f}\n"
            f"Take Profit: ${take_profit:.9f}\n\n"
            f"RSI Value: {signals['RSI']}\n"
            f"EMA Value: {signals['EMA']}\n"
            # f"Bollinger Bands Upper: ${bb_upper:.5f}\n"
            # f"Bollinger Bands Lower: ${bb_lower:.5f}\n"
            f"Bollinger Bands: {signals['BB']}\n"
            # f"Support: ${extra['support']}\n"
            # f"Resistance: ${extra['resistance']}\n"
            F"Support & Resistance: {signals['Support/Resistance']}\n"
            # f"ADX: {adx_value} | +DI: {plus_di} | -DI: {minus_di}\n"
            f"ADX: {signals['ADX']}\n"
            f"Fibonacci: {signals['Fibonacci']}\n"
            # f"Swing High: ${fib_data['swing_high']}\n"
            # f"Swing Low: ${fib_data['swing_low']}\n"
            f"Supertrend: {supertrend_signal}\n"
            f"Trading View: {trading_view}\n\n"
            f"Volume: {extra['volume']} ({'OK' if extra['volume_ok'] else 'LOW'})\n"
            f"LONG Confidence: {long_confidence:.2f}%{star_long}\n"
            f"SHORT Confidence: {short_confidence:.2f}%{star_short}\n"
            
        )
    else:
        msg += "Stop-Loss and Take-Profit levels not available due to unclear signal."

    await update.message.reply_markdown(msg)
    await update.message.reply_text("Sir, please give a feedback of this trade.")
    return ConversationHandler.END   #Its important to END here otherwise 'Thanks' will not works!


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END  #Two END'S important here otherwise 'Thanks' will not works!

        # Add feedback request at the end

bitnode_signal = get_bitnode_signal()

if bitnode_signal == "LONG":
    # place long trade
    pass
elif bitnode_signal == "SHORT":
    # place short trade
    pass
elif bitnode_signal == "WAIT":
    # do nothing
    pass

# Initialize result tracking list if not present
async def handle_profit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data.get("results", [])
    results.append("Profit")
    context.user_data["results"] = results
    await update.message.reply_text("🤩 Trade marked as Profit.")

    reply = random.choice(profit_replies)
    await update.message.reply_text(reply)

async def handle_loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data.get("results", [])
    results.append("Loss")
    context.user_data["results"] = results
    await update.message.reply_text("🥱 Trade marked as Loss.")

    reply = random.choice(loss_replies)
    await update.message.reply_text(reply)

async def handle_accuracy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = context.user_data.get("results", [])
    total = len(results)
    wins = results.count("Profit")

    if total == 0:
        await update.message.reply_text("No trade feedback given yet.")
        return

    accuracy = (wins / total) * 100
    await update.message.reply_text(
        f"Guider Accuracy Rate: {accuracy:.2f}% ({wins} wins / {total} total)"
    )

async def reset_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "results" in context.user_data:
        context.user_data["results"] = []
        await update.message.reply_text("Feedback data has been reset.")
    else:
        await update.message.reply_text("No feedback data to reset.")

# Function to respond to Profit or Loss messages
async def handle_trade_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if "profit" in text:
        reply = random.choice(profit_replies)
        await update.message.reply_text(reply)

    elif "loss" in text:
        reply = random.choice(loss_replies)
        await update.message.reply_text(reply)

# === Run the Bot ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
    entry_points=[CommandHandler("customsignal", start_custom_signal)],
    states={
        ASK_PAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_pair)],
        ASK_TIMEFRAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_timeframe)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
    
    app.add_handler(conv_handler)

    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^profit$"), handle_profit))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^loss$"), handle_loss))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^Accuracy Rate\\?$"), handle_accuracy))

    app.add_handler(CommandHandler("resetfeedback", reset_feedback))

    # Handles general messages that contain "profit" or "loss" (not exact match)
    # app.add_handler(MessageHandler(
    #     filters.TEXT & (~filters.COMMAND) & (
    #         filters.Regex(r'(?i).*profit.*') | filters.Regex(r'(?i).*loss.*')
    #     ),
    # handle_trade_result
    # ))

    # Then, add your thank you handler — after the conversation one
    app.add_handler(MessageHandler(
        filters.TEXT & (~filters.COMMAND) & (
            filters.Regex(r'(?i)^thanks$') | filters.Regex(r'(?i)^thank you$')
        ),
        handle_thanks
    ))

    print("🤖 Bot is running...")
    app.run_polling()
