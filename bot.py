import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from exchanges.btcc import BTCCExchange
from utils.logger import setup_logger

# Load env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BTCC_API_KEY = os.getenv("BTCC_API_KEY")
BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")

# Setup logger
logger = setup_logger("bot")

# Init BTCC
btcc = BTCCExchange(api_key=BTCC_API_KEY, api_secret=BTCC_API_SECRET)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📊 Balance", "🐝 Deposit"],
        ["📈 Trade", "🔔 Alerts"],
        ["🧠 AI Strategy", "⚙️ Settings"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🤖 Welcome to the Crypto Bot!", reply_markup=reply_markup)

# Buy BTC command
async def buybtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = 0.0005  # default amount
        result = btcc.place_market_order("BTC/USDT", "buy", amount)
        message = f"✅ Order placed:\nID: {result.get('data', {}).get('orderId', 'N/A')}"
    except Exception as e:
        message = f"❌ Error placing order: {str(e)}"
    await update.message.reply_text(message)

# MAIN
if __name__ == "__main__":
    if not BOT_TOKEN:
        logger.error("No bot token found.")
        exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buybtc", buybtc_command))
    
    async def run():
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted. Starting polling...")
        await app.run_polling()

    import asyncio
    logger.info("✅ Bot is starting...")
    asyncio.run(run())
