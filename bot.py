from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Placeholder user database
user_data = {}

# Main menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📊 Balance", callback_data="balance"),
            InlineKeyboardButton("💸 Deposit", callback_data="deposit")
        ],
        [
            InlineKeyboardButton("📈 Trade", callback_data="trade"),
            InlineKeyboardButton("🔔 Alerts", callback_data="alerts")
        ],
        [
            InlineKeyboardButton("🧠 AI Strategy", callback_data="ai_strategy"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🤖 Welcome to the Crypto Bot!", reply_markup=reply_markup)

# Callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # You can expand this logic per platform/API integration
    if data == "balance":
        await query.edit_message_text(text="📊 Your balance is: $10,000 (Demo)")
    elif data == "deposit":
        await query.edit_message_text(text="💸 Send crypto to your deposit address: ...")
    elif data == "trade":
        await query.edit_message_text(text="📈 Trading module coming soon!")
    elif data == "alerts":
        await query.edit_message_text(text="🔔 Set price alerts in the next version.")
    elif data == "ai_strategy":
        await query.edit_message_text(text="🧠 AI Strategies not available yet.")
    elif data == "settings":
        await query.edit_message_text(text="⚙️ Customize your bot experience.")
    else:
        await query.edit_message_text(text="❓ Unknown option.")

# Run the bot
if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    print("✅ Bot is running with button UI...")
    app.run_polling()
