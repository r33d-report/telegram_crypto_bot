import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import asyncio

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

logger = setup_logger("bot")

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

    inline_buttons = [
        [InlineKeyboardButton("Buy BTC", callback_data="buy_btc"), InlineKeyboardButton("Sell BTC", callback_data="sell_btc")],
        [InlineKeyboardButton("Price BTC", callback_data="price_btc")],
        [InlineKeyboardButton("Balance BTCC", callback_data="balance_btcc"), InlineKeyboardButton("Balance Coinbase", callback_data="balance_coinbase")]
    ]
    inline_markup = InlineKeyboardMarkup(inline_buttons)
    await update.message.reply_text("Quick actions:", reply_markup=inline_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    try:
        if data == "buy_btc":
            result = btcc.place_market_order("BTC/USDT", "buy", 0.0005)
            msg = f"✅ Buy BTC ID: {result.get('data', {}).get('orderId', 'N/A')}"
        elif data == "sell_btc":
            result = btcc.place_market_order("BTC/USDT", "sell", 0.0005)
            msg = f"✅ Sell BTC ID: {result.get('data', {}).get('orderId', 'N/A')}"
        elif data == "price_btc":
            price = btcc.get_current_price("BTC/USDT")
            msg = f"📈 BTC/USDT: ${price}"
        elif data == "balance_btcc":
            balances = btcc.get_balance()
            msg = "\n".join(f"{k}: {v}" for k, v in balances.items()) if balances else "No BTCC balances."
        elif data == "balance_coinbase":
            balances = coinbase.get_balance()
            msg = "\n".join(f"{k}: {v}" for k, v in balances.items()) if balances else "No Coinbase balances."
        else:
            msg = "Unknown action."
    except Exception as e:
        msg = f"❌ Error: {str(e)}"

    await query.edit_message_text(msg)

async def buybtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = btcc.place_market_order("BTC/USDT", "buy", 0.0005)
        msg = f"✅ Order placed: {result.get('data', {}).get('orderId', 'N/A')}"
    except Exception as e:
        msg = f"❌ Error: {str(e)}"
    await update.message.reply_text(msg)

async def sellbtc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = btcc.place_market_order("BTC/USDT", "sell", 0.0005)
        msg = f"✅ Sell order placed: {result.get('data', {}).get('orderId', 'N/A')}"
    except Exception as e:
        msg = f"❌ Error: {str(e)}"
    await update.message.reply_text(msg)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exchange_name = context.args[0].lower() if context.args else "btcc"
    exchange = EXCHANGES.get(exchange_name)
    if not exchange:
        await update.message.reply_text(f"❌ Unknown exchange '{exchange_name}'")
        return
    try:
        balances = exchange.get_balance()
        msg = "💰 Balances:\n" + "\n".join(f"{k.upper()}: {v:.4f}" for k, v in balances.items()) if balances else "🤷 No balances."
    except Exception as e:
        msg = f"❌ Error: {str(e)}"
    await update.message.reply_text(msg)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper() if context.args else "BTC"
        price = btcc.get_current_price(f"{symbol}/USDT")
        msg = f"📈 {symbol}/USDT = ${price}"
    except Exception as e:
        msg = f"❌ Error: {str(e)}"
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧾 *Crypto Bot Commands:*\n"
        "/start - Show main menu\n"
        "/buybtc - Buy 0.0005 BTC\n"
        "/sellbtc - Sell 0.0005 BTC\n"
        "/balance [exchange] - Show balances (default: btcc)\n"
        "/price [symbol] - Get price (default: BTC)\n"
        "/help - Show this help menu"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ✅ Async launcher
def main():
    logger.info("✅ Bot is starting...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buybtc", buybtc_command))
    app.add_handler(CommandHandler("sellbtc", sellbtc_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("✅ Starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
