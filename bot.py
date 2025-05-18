import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from exchanges.btcc import BTCCExchange
from utils.logger import setup_logger

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BTCC_API_KEY = os.getenv("BTCC_API_KEY")
BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")

# Setup logger
logger = setup_logger("bot")

# Initialize exchange
btcc = BTCCExchange(api_key=BTCC_API_KEY, api_secret=BTCC_API_SECRET)

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

# --- New command handlers ---

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        balances = btcc.get_balance()  # <- was get_balances()
        text = "💰 Your Balances:\n"
        for asset, amount in balances.items():
            text += f"{asset}: {amount}\n"
    except Exception as e:
        text = f"❌ Error getting balance: {str(e)}"
    await update.message.reply_text(text)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper() if context.args else "BTC"
        pair = f"{symbol}/USDT"
        price = btcc.get_current_price(pair)  # build this too
        msg = f"📈 {pair} price is: ${price}"
    except Exception as e:
        msg = f"❌ Error fetching price: {str(e)}"
    await update.message.reply_text(msg)

async def sellbtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = 0.0005
        result = btcc.place_market_order("BTC/USDT", "sell", amount)
        msg = f"✅ Sell order placed:\nID: {result.get('data', {}).get('orderId', 'N/A')}"
    except Exception as e:
        msg = f"❌ Error placing sell order: {str(e)}"
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧾 *Crypto Bot Commands:*\n\n"
        "/start - Launch the bot UI\n"
        "/buybtc - Buy 0.0005 BTC\n"
        "/sellbtc - Sell 0.0005 BTC\n"
        "/balance - Show account balances\n"
        "/price [COIN] - Show price of a coin (default BTC)\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
    
# Entrypoint
async def main():
    if not BOT_TOKEN:
        logger.error("❌ No bot token found.")
        return

    # ⚠️ Temporarily create a bot instance just to delete the webhook early
    from telegram import Bot
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook deleted (pre-run).")

    # Now build the actual application
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buybtc", buybtc_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("sellbtc", sellbtc_command))
    app.add_handler(CommandHandler("help", help_command))

    logger.info("✅ Starting polling...")
    await app.run_polling()

# Boot logic
if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    logger.info("✅ Bot is starting...")

    loop = asyncio.get_event_loop()
    nest_asyncio.apply(loop)

    try:
        loop.create_task(main())
        loop.run_forever()
    except Exception as e:
        logger.error(f"❌ Uncaught error in main: {e}")
