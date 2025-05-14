from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = "3AzjTLSPwmf3sTVYg7BU36VmspKtHEJUYd7CKY5Hix9j"
    balance_text = (
        f"Solana -\n`{wallet_address}`\n(Tap to copy)\n"
        f"Balance: 0 SOL ($0.00)\n"
        f"\u2014\nClick on the Refresh button to update your current balance.\n\n"
        f"Join our Telegram group @trojan and follow us on [Twitter](https://twitter.com)!\n\n"
        f"💡 If you aren't already, we advise that you *use any of the following bots to trade with*. \
You will have the same wallets and settings across all bots, but it will be significantly faster due to lighter user load.\n"
        f"[Agamemnon](https://t.me/AgamemnonBot) | [Achilles](https://t.me/AchillesBot) | [Nestor](https://t.me/NestorBot) | [Odysseus](https://t.me/OdysseusBot)\n"
        f"[Menelaus](https://t.me/MenelausBot) | [Diomedes](https://t.me/DiomedesBot) | [Paris](https://t.me/ParisBot) | [Helenus](https://t.me/HelenusBot) | [Hector](https://t.me/HectorBot)\n\n"
        f"⚠️ We have no control over ads shown by Telegram in this bot. Do not be scammed by fake airdrops or login pages."
    )

    buttons = [
        [InlineKeyboardButton("Buy", callback_data="buy"), InlineKeyboardButton("Sell", callback_data="sell")],
        [InlineKeyboardButton("Positions", callback_data="positions"), InlineKeyboardButton("Limit Orders", callback_data="limit_orders")],
        [InlineKeyboardButton("Copy Trade", callback_data="copy_trade"), InlineKeyboardButton("Sniper 🆒", callback_data="sniper")],
        [InlineKeyboardButton("Trenches", callback_data="trenches"), InlineKeyboardButton("💰 Referrals", callback_data="referrals"), InlineKeyboardButton("⭐ Watchlist", callback_data="watchlist")],
        [InlineKeyboardButton("Withdraw", callback_data="withdraw"), InlineKeyboardButton("Settings", callback_data="settings")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="refresh")],
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        balance_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data
    if action == "refresh":
        await query.edit_message_text("🔄 Refreshing balance...")
    else:
        await query.edit_message_text(f"You selected: {action}")

if __name__ == "__main__":
    from config import config

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("Bot is polling...")
    app.run_polling()
