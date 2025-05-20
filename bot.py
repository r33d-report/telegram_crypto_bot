import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from exchanges.btcc import BTCCExchange
from exchanges.coinbase import CoinbaseExchange
from utils.logger import setup_logger

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

BTCC_API_KEY = os.getenv("BTCC_API_KEY")
BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")

COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

# Setup logger
logger = setup_logger("bot")

# Initialize exchanges
btcc = BTCCExchange(api_key=BTCC_API_KEY, api_secret=BTCC_API_SECRET)
coinbase = CoinbaseExchange(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)

EXCHANGES = {
    "btcc": btcc,
    "coinbase": coinbase,
}

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["📊 Balance", "🐝 Deposit"], ["📈 Trade", "🔔 Alerts"], ["🧠 AI Strategy", "⚙️ Settings"]]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("🤖 Welcome to the Crypto Bot!", reply_markup=markup)

async def buybtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = 0.0005
        result = btcc.place_market_order("BTC/USDT", "buy", amount)
        msg = f"✅ Order placed:\nID: {result.get('data', {}).get('orderId', 'N/A')}"
    except Exception as e:
        msg = f"❌ Error placing order: {str(e)}"
    await update.message.reply_text(msg)

async def sellbtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = 0.0005
        result = btcc.place_market_order("BTC/USDT", "sell", amount)
        msg = f"✅ Sell order placed:\nID: {result.get('data', {}).get('orderId', 'N/A')}"
    except Exception as e:
        msg = f"❌ Error placing sell order: {str(e)}"
    await update.message.reply_text(msg)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exchange_name = context.args[0].lower() if context.args else "btcc"
    exchange = EXCHANGES.get(exchange_name)

    if not exchange:
        await update.message.reply_text(f"❌ Unknown exchange '{exchange_name}'")
        return

    try:
        balances = exchange.get_balance()
        if not balances:
            text = "🤷‍♂️ No balances found."
        else:
            text = "💰 Your Balances:\n" + "\n".join(f"{k.upper()}: {v:.4f}" for k, v in balances.items())
    except Exception as e:
        text = f"❌ Error getting balance: {str(e)}"
    await update.message.reply_text(text)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper() if context.args else "BTC"
        pair = f"{symbol}/USDT"
        price = btcc.get_current_price(pair)
        msg = f"📈 {pair} price is: ${price}"
    except Exception as e:
        msg = f"❌ Error fetching price: {str(e)}"
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧾 *Crypto Bot Commands:*\n\n"
        "/start - Launch the bot UI\n"
        "/buybtc - Buy 0.0005 BTC\n"
        "/sellbtc - Sell 0.0005 BTC\n"
        "/balance [exchange] - Show balances (default: btcc)\n"
        "/price [symbol] - Show coin price (default: BTC)\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# Entrypoint
async def main():
    if not BOT_TOKEN:
        logger.error("❌ No bot token found.")
        return

    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook deleted (pre-run).")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buybtc", buybtc_command))
    app.add_handler(CommandHandler("sellbtc", sellbtc_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("help", help_command))

    logger.info("✅ Starting polling...")
    await app.run_polling()

if __name
