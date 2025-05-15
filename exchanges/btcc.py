import os
import sys
import json
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Load .env file
load_dotenv()

telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")

print("Bot token loaded:", telegram_token[:10], "...")

# Set up logging
from utils.logger import setup_logger
logger = setup_logger("bot")

# Import exchanges
from exchanges.btcc import BTCCExchange, quick_buy_btc

btcc = BTCCExchange(
    api_key=os.getenv("BTCC_API_KEY"),
    api_secret=os.getenv("BTCC_API_SECRET"),
    logger=setup_logger("btcc")
)

# === Bot Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Buy BTC", callback_data="buy_btc")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose an action:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy_btc":
        result = quick_buy_btc(btcc)
        if "error" in result:
            await query.edit_message_text(f"❌ Error placing order: {result['error']}")
        else:
            await query.edit_message_text(f"✅ Order placed!\n\n{json.dumps(result, indent=2)}")

# === Main Execution ===
if __name__ == "__main__":
    application = Application.builder().token(telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("✅ Bot is running with button UI...")
    application.run_polling()
