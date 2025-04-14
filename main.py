import logging
import asyncio
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import matplotlib.pyplot as plt
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7574687909:AAG8it1ndm-bYQ5MrZyXXOlBAehLPlGrlNA"
CHANNEL_ID = "-1002512649422"

selected_pair = "EURUSD=X"
running = False

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("✅ Start Signal", callback_data='start')],
        [InlineKeyboardButton("🛑 Stop Signal", callback_data='stop')],
        [InlineKeyboardButton("📊 Select Pair", callback_data='select_pair')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Bot Ready! নিচের অপশন থেকে বেছে নিন:", reply_markup=reply_markup)

async def button(update, context):
    global running, selected_pair
    query = update.callback_query
    await query.answer()

    if query.data == 'start':
        running = True
        await query.edit_message_text("✅ Signal Bot চালু হয়েছে!")
        asyncio.create_task(send_signals(context))

    elif query.data == 'stop':
        running = False
        await query.edit_message_text("🛑 Signal Bot বন্ধ হয়েছে!")

    elif query.data == 'select_pair':
        pairs = ["EURUSD=X", "USDCAD=X", "GBPUSD=X", "AUDJPY=X", "EURJPY=X", "EURGBP=X", "USDJPY=X", "AUDUSD=X"]
        buttons = [[InlineKeyboardButton(pair.replace("=X", ""), callback_data=pair)] for pair in pairs]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("📊 কোন পেয়ার সিলেক্ট করতে চান?", reply_markup=reply_markup)

    elif query.data in ["EURUSD=X", "USDCAD=X", "GBPUSD=X", "AUDJPY=X", "EURJPY=X", "EURGBP=X", "USDJPY=X", "AUDUSD=X"]:
        selected_pair = query.data
        await query.edit_message_text(f"✅ {selected_pair.replace('=X', '')} সিলেক্ট করা হয়েছে!")

async def send_signals(context):
    global running, selected_pair
    while running:
        df = yf.download(tickers=selected_pair, interval='1m', period='2d')
        if df.empty or 'Close' not in df.columns:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="❌ ডেটা লোড হয়নি")
            return

        df.ta.ema(length=10, append=True)
        df.ta.macd(append=True)
        df.ta.rsi(append=True)
        df.ta.stoch(append=True)
        df.ta.bbands(append=True)

        last = df.iloc[-1]
        signal = ""

        if (
            last['EMA_10'] < last['Close'] and
            last['MACDh_12_26_9'] > 0 and
            last['RSI_14'] < 70 and
            last['STOCHk_14_3_3'] > last['STOCHd_14_3_3']
        ):
            signal = "📈 VIP BUY Signal ✅"
        elif (
            last['EMA_10'] > last['Close'] and
            last['MACDh_12_26_9'] < 0 and
            last['RSI_14'] > 30 and
            last['STOCHk_14_3_3'] < last['STOCHd_14_3_3']
        ):
            signal = "📉 VIP SELL Signal ✅"
        else:
            signal = "⏸ No Signal"

        plt.figure(figsize=(8, 4))
        plt.plot(df['Close'], label='Price', color='blue')
        plt.title(f"{selected_pair.replace('=X','')} Price")
        plt.legend()
        chart_file = f"chart_{datetime.now().strftime('%H%M%S')}.png"
        plt.savefig(chart_file)
        plt.close()

        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=open(chart_file, 'rb'))
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"📍 {selected_pair.replace('=X','')} - {signal} ✅")
        await asyncio.sleep(60)

async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    await application.run_polling()

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
