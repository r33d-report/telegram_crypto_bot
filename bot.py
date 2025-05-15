import os
import sys
import logging
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

from exchanges.btcc import BTCCExchange
from config import config
from utils.logger import setup_logger

# === Load .env ===
load_dotenv()
logger = setup_logger("bot")

BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
BTCC_API_KEY = os.getenv("BTCC_API_KEY")
BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")

btcc = BTCCExchange(BTCC_API_KEY, BTCC_API_SECRET)

# === Start Command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Buy BTC", callback_data="buy_btc")],
        [InlineKeyboardButton("📊 Portfolio", callback_data="balance")],
        [InlineKeyboardButton("⚙️ Trade Settings", callback_data="settings")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 Welcome to Crypto Bot! Choose an option below:", reply_markup=reply_markup)

# === Button Clicks ===
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_btc":
        await query.edit_message_text("🛒 Placing market buy order for 0.0005 BTC...")
        try:
            result = btcc.place_market_order("BTC/USDT", "buy", 0.0005)
            await query.message.reply_text(f"✅ Order placed: {result}")
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to buy BTC: {e}")

    elif query.data == "balance":
        await query.edit_message_text("📊 Fetching balance...")
        try:
            balance = btcc.get_balance()
            balance_str = "\n".join([f"{k}: {v}" for k, v in balance.items()])
            await query.message.reply_text(f"💰 Account Balance:\n{balance_str}")
        except Exception as e:
            await query.message.reply_text(f"❌ Failed to fetch balance: {e}")

    elif query.data == "settings":
        await query.edit_message_text("⚙️ Settings menu coming soon.")

# === Telegram Bot Init ===
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("Missing TELEGRAM_BOT_TOKEN")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))

    logger.info("✅ Bot is running with button UI...")
    app.run_polling()
