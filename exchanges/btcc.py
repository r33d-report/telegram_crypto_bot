import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from exchanges.btcc import BTCCExchange, quick_buy_btc
from utils.logger import setup_logger
from config import config

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger("bot")

# API Keys
BTCC_API_KEY = os.getenv("BTCC_API_KEY")
BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN

# Initialize BTCC Client
btcc_client = BTCCExchange(BTCC_API_KEY, BTCC_API_SECRET)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Crypto Bot!\nUse /buybtc to quickly buy 0.0005 BTC on BTCC."
    )

# Buy BTC command
async def buybtc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(f"🚀 Placing market buy order for 0.0005 BTC...")

    result = quick_buy_btc(btcc_client, amount=0.0005)

    if "error" in result:
        await update.message.reply_text(f"❌ Failed: {result['error']}")
    else:
        order_id = result.get("data", {}).get("orderId", "N/A")
        await update.message.reply_text(f"✅ Order placed! ID: {order_id}")

# Run the bot
if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buybtc", buybtc))

    logger.info("✅ Bot is running with real trading support...")
    application.run_polling()
