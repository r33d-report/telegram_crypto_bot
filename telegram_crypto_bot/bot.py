
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Crypto Trading Telegram Bot
A bot for cryptocurrency trading and meme coin sniping that integrates with BTCC and Coinbase.
"""

import os
import sys
import logging
import json
from typing import Dict, Optional, List, Any, Union, Tuple
from datetime import datetime
import threading
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

# Import utility modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger
from utils.price_alerts import PriceAlert, PriceAlertManager
from utils.strategies import Strategy, StrategyManager, TradingSignal, StrategyType
from utils.strategies import SMAStrategy, EMAStrategy, RSIStrategy, BollingerBandsStrategy
from utils.scheduler import TaskScheduler
from utils.keyboards import KeyboardFactory
from utils.meme_sniper import MemeToken, MemeSniperAlert, MemeSniper
from config import config
from exchanges.btcc import BTCCExchange
from exchanges.coinbase import CoinbaseExchange
from exchanges.futures_btcc import BTCCFuturesExchange
from exchanges.photon_sol import PhotonSOLExchange

# Set up logging
logger = setup_logger("bot")

# Get the bot token from environment variables
BOT_TOKEN = config.TELEGRAM_BOT_TOKEN
if not BOT_TOKEN:
    logger.error("No bot token found. Please set the TELEGRAM_BOT_TOKEN environment variable.")
    sys.exit(1)

# Exchange instances
exchange_instances = {}

# Create data directories if they don't exist
os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)

# File paths for persistent data
ALERTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'price_alerts.json')
STRATEGIES_FILE = os.path.join(os.path.dirname(__file__), 'data', 'strategies.json')
MEME_TOKENS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'meme_tokens.json')
MEME_ALERTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'meme_alerts.json')

# Conversation states
SETTING_ALERT = range(1)
SETTING_STRATEGY = range(1)
SETTING_MEME_SNIPER = range(1)

def get_exchange(exchange_name: str) -> Any:
    """
    Get or create an exchange instance.
    
    Args:
        exchange_name (str): Name of the exchange ('btcc', 'btcc_futures', 'coinbase', or 'photon_sol')
        
    Returns:
        Exchange instance
        
    Raises:
        ValueError: If exchange is not supported or credentials are missing
    """
    exchange_name = exchange_name.lower()
    
    if exchange_name in exchange_instances:
        return exchange_instances[exchange_name]
    
    try:
        credentials = config.get_exchange_credentials(exchange_name.split('_')[0])
        
        if exchange_name == 'btcc':
            exchange = BTCCExchange(
                api_key=credentials['api_key'],
                api_secret=credentials['api_secret'],
                logger=logger
            )
        elif exchange_name == 'btcc_futures':
            exchange = BTCCFuturesExchange(
                api_key=credentials['api_key'],
                api_secret=credentials['api_secret'],
                logger=logger
            )
        elif exchange_name == 'coinbase':
            exchange = CoinbaseExchange(
                api_key=credentials['api_key'],
                api_secret=credentials['api_secret'],
                logger=logger
            )
        elif exchange_name == 'photon_sol':
            exchange = PhotonSOLExchange(
                api_key=credentials['api_key'],
                api_secret=credentials['api_secret'],
                logger=logger
            )
        else:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        
        exchange_instances[exchange_name] = exchange
        return exchange
        
    except ValueError as e:
        logger.error(f"Failed to initialize exchange {exchange_name}: {str(e)}")
        raise

# Initialize managers
async def alert_notification_callback(alert: PriceAlert, current_price: float) -> None:
    """
    Callback function for price alert notifications.
    
    Args:
        alert (PriceAlert): The triggered alert
        current_price (float): Current price that triggered the alert
    """
    condition_text = "above" if alert.condition == "above" else "below"
    
    message = (
        f"🔔 *Price Alert Triggered!*\n\n"
        f"Symbol: {alert.symbol}\n"
        f"Condition: Price {condition_text} {alert.target_price}\n"
        f"Current Price: {current_price}\n"
        f"Exchange: {alert.exchange.upper()}\n\n"
        f"_Alert ID: {alert.alert_id}_"
    )
    
    try:
        await application.bot.send_message(
            chat_id=alert.user_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Sent price alert notification to user {alert.user_id}")
    except Exception as e:
        logger.error(f"Failed to send price alert notification: {str(e)}")

async def strategy_order_callback(strategy: Strategy, signal: TradingSignal) -> None:
    """
    Callback function for strategy trading signals.
    
    Args:
        strategy (Strategy): The strategy that generated the signal
        signal (TradingSignal): The trading signal (BUY or SELL)
    """
    # This would typically place an order based on the strategy's signal
    # For now, we'll just send a notification to the user
    
    # Extract user_id from strategy name (assuming format "strategy_name_user_id")
    try:
        user_id = int(strategy.name.split('_')[-1])
    except (ValueError, IndexError):
        logger.error(f"Could not extract user_id from strategy name: {strategy.name}")
        return
    
    message = (
        f"📊 *Trading Strategy Signal*\n\n"
        f"Strategy: {strategy.name}\n"
        f"Symbol: {strategy.symbol}\n"
        f"Signal: {signal.value.upper()}\n"
        f"Exchange: {strategy.exchange.upper()}\n\n"
        f"_Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_"
    )
    
    try:
        await application.bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Sent strategy signal notification to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send strategy signal notification: {str(e)}")

async def meme_notification_callback(alert: MemeSniperAlert, token: MemeToken) -> None:
    """
    Callback function for meme coin sniper alerts.
    
    Args:
        alert (MemeSniperAlert): The triggered alert
        token (MemeToken): The token that triggered the alert
    """
    price_change_5m = token.calculate_price_change(minutes=5) or 0
    price_change_1h = token.calculate_price_change(minutes=60) or 0
    volume_change = token.calculate_volume_change(minutes=60) or 0
    
    message = (
        f"🚀 *Meme Coin Alert!*\n\n"
        f"Token: {token.name} ({token.symbol})\n"
        f"Price: ${token.price:.8f}\n"
        f"Market Cap: ${token.market_cap:,.0f}\n"
        f"Chain: {token.chain}\n\n"
        f"5m Price Change: {price_change_5m:.2f}%\n"
        f"1h Price Change: {price_change_1h:.2f}%\n"
        f"1h Volume Change: {volume_change:.2f}%\n\n"
    )
    
    if token.address:
        message += f"Contract: `{token.address}`\n\n"
    
    # Add quick buy button if auto-buy is not enabled
    keyboard = None
    if not alert.auto_buy:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Quick Buy", 
                    callback_data=f"meme_quick_buy_{token.token_id}"
                )
            ]
        ]
        message += "_Use the Quick Buy button to purchase this token._"
    else:
        message += "_Auto-buy is enabled for this alert._"
    
    try:
        await application.bot.send_message(
            chat_id=alert.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        logger.info(f"Sent meme coin alert notification to user {alert.user_id}")
    except Exception as e:
        logger.error(f"Failed to send meme coin alert notification: {str(e)}")

async def meme_buy_callback(alert: MemeSniperAlert, token: MemeToken, amount: float) -> None:
    """
    Callback function for auto-buying meme coins.
    
    Args:
        alert (MemeSniperAlert): The alert that triggered the buy
        token (MemeToken): The token to buy
        amount (float): Amount to buy in USD
    """
    # This would typically place an order to buy the token
    # For now, we'll just send a notification to the user
    
    message = (
        f"💰 *Auto-Buy Executed*\n\n"
        f"Token: {token.name} ({token.symbol})\n"
        f"Amount: ${amount:.2f}\n"
        f"Price: ${token.price:.8f}\n"
        f"Chain: {token.chain}\n\n"
        f"_Auto-buy executed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_"
    )
    
    try:
        await application.bot.send_message(
            chat_id=alert.user_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Sent auto-buy notification to user {alert.user_id}")
    except Exception as e:
        logger.error(f"Failed to send auto-buy notification: {str(e)}")

# Initialize managers
price_alert_manager = PriceAlertManager(
    get_exchange_func=get_exchange,
    notification_callback=alert_notification_callback,
    check_interval=60
)

strategy_manager = StrategyManager(
    get_exchange_func=get_exchange,
    order_callback=strategy_order_callback
)

scheduler = TaskScheduler()

meme_sniper = MemeSniper(
    notification_callback=meme_notification_callback,
    buy_callback=meme_buy_callback,
    check_interval=60
)

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    welcome_message = (
        f"👋 Hello, {user.first_name}!\n\n"
        f"Welcome to the Crypto Trading Bot. This bot helps you with cryptocurrency trading "
        f"and meme coin sniping on BTCC and Coinbase exchanges.\n\n"
        f"Use /help to see available commands or use the menu below to navigate."
    )
    
    # Create and send the main menu keyboard
    keyboard = KeyboardFactory.create_main_menu_keyboard()
    
    await update.message.reply_text(welcome_message, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with all available commands when the command /help is issued."""
    logger.info(f"User {update.effective_user.id} requested help")
    
    help_text = (
        "🤖 *Crypto Trading Bot Commands*\n\n"
        "*Basic Commands:*\n"
        "/start - Start the bot and get a welcome message\n"
        "/help - Show this help message\n\n"
        
        "*Exchange Commands:*\n"
        "/price <symbol> <exchange> - Get current price for a symbol (e.g., /price BTC/USDT btcc)\n"
        "/balance <exchange> - Check your wallet balance (e.g., /balance coinbase)\n"
        "/buy <symbol> <amount> <exchange> - Place a market buy order\n"
        "/sell <symbol> <amount> <exchange> - Place a market sell order\n"
        "/limit_buy <symbol> <amount> <price> <exchange> - Place a limit buy order\n"
        "/limit_sell <symbol> <amount> <price> <exchange> - Place a limit sell order\n"
        "/orderbook <symbol> <exchange> - Get order book for a symbol\n"
        "/cancel <order_id> <symbol> <exchange> - Cancel an order\n\n"
        
        "*Price Alert Commands:*\n"
        "/set_alert <symbol> <price> <above|below> <exchange> - Set a price alert\n"
        "/alerts - List your active price alerts\n"
        "/remove_alert <alert_id> - Remove a price alert\n\n"
        
        "*Automatic Trading Commands:*\n"
        "/set_strategy <name> <type> <symbol> <exchange> - Set up a trading strategy\n"
        "/strategies - List your active strategies\n"
        "/remove_strategy <name> - Remove a strategy\n"
        "/run_strategy <name> - Run a strategy once\n\n"
        
        "*Futures Trading Commands:*\n"
        "/futures_balance - Check your futures account balance\n"
        "/futures_positions - View your open futures positions\n"
        "/futures_leverage <symbol> <leverage> - Set leverage for a symbol\n"
        "/futures_long <symbol> <amount> - Open a long position\n"
        "/futures_short <symbol> <amount> - Open a short position\n"
        "/futures_close <symbol> - Close a futures position\n\n"
        
        "*Meme Coin Commands:*\n"
        "/meme_trending - Show trending meme coins\n"
        "/meme_new - Show new meme coin listings\n"
        "/set_sniper - Set up a meme coin sniper\n"
        "/snipers - List your active snipers\n"
        "/remove_sniper <id> - Remove a sniper\n\n"
        
        "*Photon-SOL Commands:*\n"
        "/photon_price <symbol> - Get current price for a token on Photon-SOL\n"
        "/photon_balance - Check your Photon-SOL wallet balance\n"
        "/photon_buy <symbol> <amount> - Place a market buy order on Photon-SOL\n"
        "/photon_sell <symbol> <amount> - Place a market sell order on Photon-SOL\n"
        "/photon_tokens - List available tokens on Photon-SOL\n"
        "/photon_trending - Show trending tokens on Photon-SOL\n"
        "/photon_new - Show new token listings on Photon-SOL\n"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get current price for a symbol."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and exchange name.\n"
            "Example: /price BTC/USDT btcc"
        )
        return
    
    symbol = args[0]
    exchange_name = args[1].lower()
    
    try:
        exchange = get_exchange(exchange_name)
        ticker = exchange.get_ticker(symbol)
        
        # Format the response based on the exchange
        if exchange_name == 'btcc':
            price = ticker.get('data', {}).get('last', 'N/A')
            high = ticker.get('data', {}).get('high', 'N/A')
            low = ticker.get('data', {}).get('low', 'N/A')
            volume = ticker.get('data', {}).get('volume', 'N/A')
        elif exchange_name == 'coinbase':
            price = ticker.get('price', 'N/A')
            high = ticker.get('high_24h', 'N/A')
            low = ticker.get('low_24h', 'N/A')
            volume = ticker.get('volume_24h', 'N/A')
        
        message = (
            f"📊 *{symbol} Price on {exchange_name.upper()}*\n\n"
            f"Current Price: {price}\n"
            f"24h High: {high}\n"
            f"24h Low: {low}\n"
            f"24h Volume: {volume}\n\n"
            f"_Updated: {update.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        )
        
        # Add price alert button
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔔 Set Price Alert", 
                    callback_data=f"set_alert_{symbol}_{exchange_name}"
                )
            ]
        ]
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error getting price: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting price: {str(e)}"
        )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check wallet balance."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide an exchange name.\n"
            "Example: /balance btcc"
        )
        return
    
    exchange_name = args[0].lower()
    
    try:
        exchange = get_exchange(exchange_name)
        balances = exchange.get_balance()
        
        # Filter out zero balances and format the response
        non_zero_balances = {k: v for k, v in balances.items() if v > 0}
        
        if not non_zero_balances:
            message = f"No assets found in your {exchange_name.upper()} wallet."
        else:
            message = f"💰 *Your {exchange_name.upper()} Wallet Balance*\n\n"
            for asset, amount in non_zero_balances.items():
                message += f"{asset}: {amount}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting balance: {str(e)}"
        )

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Place a market buy order."""
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text(
            "Please provide a symbol, amount, and exchange name.\n"
            "Example: /buy BTC/USDT 0.001 btcc"
        )
        return
    
    symbol = args[0]
    amount = float(args[1])
    exchange_name = args[2].lower()
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"buy_confirm_{symbol}_{amount}_{exchange_name}"),
            InlineKeyboardButton("Cancel", callback_data="buy_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Market Buy Order*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n"
        f"Exchange: {exchange_name.upper()}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Place a market sell order."""
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text(
            "Please provide a symbol, amount, and exchange name.\n"
            "Example: /sell BTC/USDT 0.001 btcc"
        )
        return
    
    symbol = args[0]
    amount = float(args[1])
    exchange_name = args[2].lower()
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"sell_confirm_{symbol}_{amount}_{exchange_name}"),
            InlineKeyboardButton("Cancel", callback_data="sell_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Market Sell Order*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n"
        f"Exchange: {exchange_name.upper()}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def limit_buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Place a limit buy order."""
    args = context.args
    
    if len(args) < 4:
        await update.message.reply_text(
            "Please provide a symbol, amount, price, and exchange name.\n"
            "Example: /limit_buy BTC/USDT 0.001 50000 btcc"
        )
        return
    
    symbol = args[0]
    amount = float(args[1])
    price = float(args[2])
    exchange_name = args[3].lower()
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"limit_buy_confirm_{symbol}_{amount}_{price}_{exchange_name}"),
            InlineKeyboardButton("Cancel", callback_data="limit_buy_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Limit Buy Order*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n"
        f"Price: {price}\n"
        f"Exchange: {exchange_name.upper()}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def limit_sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Place a limit sell order."""
    args = context.args
    
    if len(args) < 4:
        await update.message.reply_text(
            "Please provide a symbol, amount, price, and exchange name.\n"
            "Example: /limit_sell BTC/USDT 0.001 60000 btcc"
        )
        return
    
    symbol = args[0]
    amount = float(args[1])
    price = float(args[2])
    exchange_name = args[3].lower()
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"limit_sell_confirm_{symbol}_{amount}_{price}_{exchange_name}"),
            InlineKeyboardButton("Cancel", callback_data="limit_sell_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Limit Sell Order*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n"
        f"Price: {price}\n"
        f"Exchange: {exchange_name.upper()}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def orderbook_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get order book for a symbol."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and exchange name.\n"
            "Example: /orderbook BTC/USDT btcc"
        )
        return
    
    symbol = args[0]
    exchange_name = args[1].lower()
    limit = 5  # Show top 5 bids and asks by default
    
    if len(args) > 2:
        try:
            limit = int(args[2])
            limit = min(limit, 10)  # Cap at 10 to avoid too long messages
        except ValueError:
            pass
    
    try:
        exchange = get_exchange(exchange_name)
        orderbook = exchange.get_order_book(symbol, limit)
        
        # Format the response based on the exchange
        message = f"📚 *Order Book for {symbol} on {exchange_name.upper()}*\n\n"
        
        # Add bids (buy orders)
        message += "*Bids (Buy Orders)*:\n"
        if exchange_name == 'btcc':
            bids = orderbook.get('data', {}).get('bids', [])
            for i, bid in enumerate(bids[:limit]):
                message += f"{i+1}. Price: {bid[0]}, Amount: {bid[1]}\n"
        elif exchange_name == 'coinbase':
            bids = orderbook.get('bids', [])
            for i, bid in enumerate(bids[:limit]):
                message += f"{i+1}. Price: {bid[0]}, Amount: {bid[1]}\n"
        
        message += "\n*Asks (Sell Orders)*:\n"
        if exchange_name == 'btcc':
            asks = orderbook.get('data', {}).get('asks', [])
            for i, ask in enumerate(asks[:limit]):
                message += f"{i+1}. Price: {ask[0]}, Amount: {ask[1]}\n"
        elif exchange_name == 'coinbase':
            asks = orderbook.get('asks', [])
            for i, ask in enumerate(asks[:limit]):
                message += f"{i+1}. Price: {ask[0]}, Amount: {ask[1]}\n"
        
        message += f"\n_Updated: {update.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting order book: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting order book: {str(e)}"
        )

async def cancel_order_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel an existing order."""
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text(
            "Please provide an order ID, symbol, and exchange name.\n"
            "Example: /cancel 123456 BTC/USDT btcc"
        )
        return
    
    order_id = args[0]
    symbol = args[1]
    exchange_name = args[2].lower()
    
    try:
        exchange = get_exchange(exchange_name)
        success = exchange.cancel_order(order_id, symbol)
        
        if success:
            await update.message.reply_text(
                f"✅ Order {order_id} has been successfully cancelled."
            )
        else:
            await update.message.reply_text(
                f"❌ Failed to cancel order {order_id}. Please check the order ID and try again."
            )
        
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        await update.message.reply_text(
            f"❌ Error cancelling order: {str(e)}"
        )

# Price Alert Commands
async def set_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a price alert for a cryptocurrency."""
    args = context.args
    
    if len(args) < 4:
        await update.message.reply_text(
            "Please provide a symbol, price, condition (above/below), and exchange name.\n"
            "Example: /set_alert BTC/USDT 50000 above btcc"
        )
        return
    
    symbol = args[0]
    try:
        price = float(args[1])
    except ValueError:
        await update.message.reply_text("Price must be a number.")
        return
    
    condition = args[2].lower()
    if condition not in ['above', 'below']:
        await update.message.reply_text("Condition must be 'above' or 'below'.")
        return
    
    exchange_name = args[3].lower()
    
    # Create the alert
    alert = PriceAlert(
        user_id=update.effective_user.id,
        symbol=symbol,
        exchange=exchange_name,
        target_price=price,
        condition=condition
    )
    
    # Add the alert to the manager
    price_alert_manager.add_alert(alert)
    
    # Save alerts to file
    price_alert_manager.save_alerts(ALERTS_FILE)
    
    await update.message.reply_text(
        f"✅ Price alert set for {symbol} on {exchange_name.upper()}.\n"
        f"You will be notified when the price goes {condition} {price}.\n\n"
        f"Alert ID: {alert.alert_id}"
    )

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all active price alerts for the user."""
    user_id = update.effective_user.id
    alerts = price_alert_manager.get_alerts_for_user(user_id)
    
    if not alerts:
        await update.message.reply_text(
            "You don't have any active price alerts. Use /set_alert to create one."
        )
        return
    
    # Convert alerts to dictionaries for the keyboard
    alerts_data = [alert.to_dict() for alert in alerts]
    
    # Create a keyboard with the alerts
    keyboard = KeyboardFactory.create_alert_list_keyboard(alerts_data)
    
    await update.message.reply_text(
        "🔔 *Your Active Price Alerts*\n\n"
        "Select an alert to view details or delete it:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

async def remove_alert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a price alert."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide the alert ID to remove.\n"
            "Example: /remove_alert alert_123456\n\n"
            "You can see your alert IDs with the /alerts command."
        )
        return
    
    alert_id = args[0]
    
    # Check if the alert exists and belongs to the user
    alert = price_alert_manager.get_alert(alert_id)
    if not alert or alert.user_id != update.effective_user.id:
        await update.message.reply_text(
            "❌ Alert not found or you don't have permission to remove it."
        )
        return
    
    # Remove the alert
    success = price_alert_manager.remove_alert(alert_id)
    
    if success:
        # Save alerts to file
        price_alert_manager.save_alerts(ALERTS_FILE)
        
        await update.message.reply_text(
            f"✅ Alert for {alert.symbol} ({alert.condition} {alert.target_price}) has been removed."
        )
    else:
        await update.message.reply_text(
            "❌ Failed to remove the alert. Please try again."
        )

# Automatic Trading Commands
async def set_strategy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set up a trading strategy."""
    args = context.args
    
    if len(args) < 4:
        await update.message.reply_text(
            "Please provide a strategy name, type, symbol, and exchange name.\n"
            "Example: /set_strategy my_btc_strategy sma_crossover BTC/USDT btcc\n\n"
            "Available strategy types: sma_crossover, ema_crossover, rsi, bollinger_bands"
        )
        return
    
    strategy_name = args[0]
    strategy_type = args[1].lower()
    symbol = args[2]
    exchange_name = args[3].lower()
    
    # Check if strategy type is valid
    valid_types = ['sma_crossover', 'ema_crossover', 'rsi', 'bollinger_bands']
    if strategy_type not in valid_types:
        await update.message.reply_text(
            f"❌ Invalid strategy type. Available types: {', '.join(valid_types)}"
        )
        return
    
    # Store user data for the conversation
    context.user_data['strategy'] = {
        'name': f"{strategy_name}_{update.effective_user.id}",
        'type': strategy_type,
        'symbol': symbol,
        'exchange': exchange_name
    }
    
    # Ask for strategy parameters based on type
    if strategy_type == 'sma_crossover':
        await update.message.reply_text(
            "Please provide the parameters for the SMA Crossover strategy:\n"
            "Format: <short_period> <long_period> <timeframe>\n\n"
            "Example: 9 21 1h\n\n"
            "This will create a strategy that generates signals when the 9-period SMA crosses the 21-period SMA on 1-hour candles."
        )
    elif strategy_type == 'ema_crossover':
        await update.message.reply_text(
            "Please provide the parameters for the EMA Crossover strategy:\n"
            "Format: <short_period> <long_period> <timeframe>\n\n"
            "Example: 9 21 1h\n\n"
            "This will create a strategy that generates signals when the 9-period EMA crosses the 21-period EMA on 1-hour candles."
        )
    elif strategy_type == 'rsi':
        await update.message.reply_text(
            "Please provide the parameters for the RSI strategy:\n"
            "Format: <period> <overbought> <oversold> <timeframe>\n\n"
            "Example: 14 70 30 1h\n\n"
            "This will create a strategy that generates signals when the 14-period RSI crosses above 70 (sell) or below 30 (buy) on 1-hour candles."
        )
    elif strategy_type == 'bollinger_bands':
        await update.message.reply_text(
            "Please provide the parameters for the Bollinger Bands strategy:\n"
            "Format: <period> <std_dev> <timeframe>\n\n"
            "Example: 20 2 1h\n\n"
            "This will create a strategy that generates signals when the price touches the upper (sell) or lower (buy) band on 1-hour candles."
        )
    
    return SETTING_STRATEGY

async def strategy_params_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle strategy parameters input."""
    user_id = update.effective_user.id
    strategy_data = context.user_data.get('strategy', {})
    
    if not strategy_data:
        await update.message.reply_text(
            "❌ Strategy setup timed out. Please start again with /set_strategy."
        )
        return ConversationHandler.END
    
    # Parse parameters based on strategy type
    params = {}
    args = update.message.text.split()
    
    try:
        if strategy_data['type'] == 'sma_crossover':
            if len(args) < 3:
                await update.message.reply_text(
                    "Please provide all required parameters: <short_period> <long_period> <timeframe>"
                )
                return SETTING_STRATEGY
            
            params = {
                'short_period': int(args[0]),
                'long_period': int(args[1]),
                'timeframe': args[2]
            }
            
            strategy = SMAStrategy(
                name=strategy_data['name'],
                symbol=strategy_data['symbol'],
                exchange=strategy_data['exchange'],
                params=params
            )
            
        elif strategy_data['type'] == 'ema_crossover':
            if len(args) < 3:
                await update.message.reply_text(
                    "Please provide all required parameters: <short_period> <long_period> <timeframe>"
                )
                return SETTING_STRATEGY
            
            params = {
                'short_period': int(args[0]),
                'long_period': int(args[1]),
                'timeframe': args[2]
            }
            
            strategy = EMAStrategy(
                name=strategy_data['name'],
                symbol=strategy_data['symbol'],
                exchange=strategy_data['exchange'],
                params=params
            )
            
        elif strategy_data['type'] == 'rsi':
            if len(args) < 4:
                await update.message.reply_text(
                    "Please provide all required parameters: <period> <overbought> <oversold> <timeframe>"
                )
                return SETTING_STRATEGY
            
            params = {
                'period': int(args[0]),
                'overbought': float(args[1]),
                'oversold': float(args[2]),
                'timeframe': args[3]
            }
            
            strategy = RSIStrategy(
                name=strategy_data['name'],
                symbol=strategy_data['symbol'],
                exchange=strategy_data['exchange'],
                params=params
            )
            
        elif strategy_data['type'] == 'bollinger_bands':
            if len(args) < 3:
                await update.message.reply_text(
                    "Please provide all required parameters: <period> <std_dev> <timeframe>"
                )
                return SETTING_STRATEGY
            
            params = {
                'period': int(args[0]),
                'std_dev': float(args[1]),
                'timeframe': args[2]
            }
            
            strategy = BollingerBandsStrategy(
                name=strategy_data['name'],
                symbol=strategy_data['symbol'],
                exchange=strategy_data['exchange'],
                params=params
            )
            
        else:
            await update.message.reply_text(
                "❌ Invalid strategy type. Please start again with /set_strategy."
            )
            return ConversationHandler.END
        
        # Add the strategy to the manager
        strategy_manager.add_strategy(strategy)
        
        # Save strategies to file
        strategy_manager.save_strategies(STRATEGIES_FILE)
        
        # Schedule the strategy to run periodically
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
        
        timeframe = params.get('timeframe', '1h')
        interval = interval_map.get(timeframe, '1h')
        
        # Create a task that executes the strategy
        def run_strategy_task():
            asyncio.run_coroutine_threadsafe(
                strategy_manager.execute_strategy(strategy.name),
                application.loop
            )
        
        scheduler.schedule_task(
            task=run_strategy_task,
            interval=interval,
            task_id=f"strategy_{strategy.name}"
        )
        
        # Start the scheduler if it's not already running
        if not scheduler.running:
            scheduler.start()
        
        await update.message.reply_text(
            f"✅ Strategy '{strategy.name}' has been set up and scheduled to run every {interval}.\n\n"
            f"Type: {strategy_data['type']}\n"
            f"Symbol: {strategy_data['symbol']}\n"
            f"Exchange: {strategy_data['exchange'].upper()}\n"
            f"Parameters: {params}\n\n"
            f"You will receive notifications when the strategy generates trading signals."
        )
        
        # Clear user data
        context.user_data.pop('strategy', None)
        
        return ConversationHandler.END
        
    except (ValueError, IndexError) as e:
        await update.message.reply_text(
            f"❌ Error setting up strategy: {str(e)}\n"
            f"Please try again with valid parameters."
        )
        return SETTING_STRATEGY

async def strategies_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all active trading strategies for the user."""
    user_id = update.effective_user.id
    
    # Get all strategies and filter by user ID
    all_strategies = list(strategy_manager.strategies.values())
    user_strategies = [s for s in all_strategies if s.name.endswith(f"_{user_id}")]
    
    if not user_strategies:
        await update.message.reply_text(
            "You don't have any active trading strategies. Use /set_strategy to create one."
        )
        return
    
    message = "📊 *Your Active Trading Strategies*\n\n"
    
    for i, strategy in enumerate(user_strategies, 1):
        # Extract the base name without user ID
        base_name = strategy.name.rsplit('_', 1)[0]
        
        message += (
            f"{i}. *{base_name}*\n"
            f"   Type: {strategy.strategy_type.value}\n"
            f"   Symbol: {strategy.symbol}\n"
            f"   Exchange: {strategy.exchange.upper()}\n"
            f"   Last Signal: {strategy.last_signal.value.upper() if strategy.last_signal else 'None'}\n"
            f"   Last Update: {strategy.last_update.strftime('%Y-%m-%d %H:%M:%S') if strategy.last_update else 'Never'}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def remove_strategy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a trading strategy."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide the strategy name to remove.\n"
            "Example: /remove_strategy my_btc_strategy\n\n"
            "You can see your strategy names with the /strategies command."
        )
        return
    
    strategy_name = args[0]
    user_id = update.effective_user.id
    
    # Append user ID to the strategy name for security
    full_strategy_name = f"{strategy_name}_{user_id}"
    
    # Check if the strategy exists
    strategy = strategy_manager.get_strategy(full_strategy_name)
    if not strategy:
        await update.message.reply_text(
            "❌ Strategy not found. Please check the name and try again."
        )
        return
    
    # Cancel the scheduled task
    scheduler.cancel_task(f"strategy_{full_strategy_name}")
    
    # Remove the strategy
    success = strategy_manager.remove_strategy(full_strategy_name)
    
    if success:
        # Save strategies to file
        strategy_manager.save_strategies(STRATEGIES_FILE)
        
        await update.message.reply_text(
            f"✅ Strategy '{strategy_name}' has been removed."
        )
    else:
        await update.message.reply_text(
            "❌ Failed to remove the strategy. Please try again."
        )

async def run_strategy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run a trading strategy once."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide the strategy name to run.\n"
            "Example: /run_strategy my_btc_strategy\n\n"
            "You can see your strategy names with the /strategies command."
        )
        return
    
    strategy_name = args[0]
    user_id = update.effective_user.id
    
    # Append user ID to the strategy name for security
    full_strategy_name = f"{strategy_name}_{user_id}"
    
    # Check if the strategy exists
    strategy = strategy_manager.get_strategy(full_strategy_name)
    if not strategy:
        await update.message.reply_text(
            "❌ Strategy not found. Please check the name and try again."
        )
        return
    
    # Run the strategy
    await update.message.reply_text(
        f"Running strategy '{strategy_name}'... Please wait."
    )
    
    signal = await strategy_manager.execute_strategy(full_strategy_name)
    
    if signal:
        await update.message.reply_text(
            f"✅ Strategy '{strategy_name}' executed successfully.\n\n"
            f"Signal: {signal.value.upper()}\n"
            f"Symbol: {strategy.symbol}\n"
            f"Exchange: {strategy.exchange.upper()}\n\n"
            f"_Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"❌ Failed to execute strategy '{strategy_name}'. Please try again."
        )

# Futures Trading Commands
async def futures_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check futures account balance."""
    try:
        exchange = get_exchange('btcc_futures')
        balances = exchange.get_balance()
        
        # Filter out zero balances and format the response
        non_zero_balances = {k: v for k, v in balances.items() if v > 0}
        
        if not non_zero_balances:
            message = "No assets found in your BTCC Futures wallet."
        else:
            message = "💰 *Your BTCC Futures Wallet Balance*\n\n"
            for asset, amount in non_zero_balances.items():
                message += f"{asset}: {amount}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting futures balance: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting futures balance: {str(e)}"
        )

async def futures_positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View open futures positions."""
    args = context.args
    symbol = None
    
    if len(args) > 0:
        symbol = args[0]
    
    try:
        exchange = get_exchange('btcc_futures')
        positions = exchange.get_futures_positions(symbol)
        
        # Format the response
        if not positions.get('data') or len(positions.get('data', [])) == 0:
            message = f"No open positions found{' for ' + symbol if symbol else ''}."
        else:
            message = f"📈 *Your BTCC Futures Positions*\n\n"
            
            for position in positions.get('data', []):
                symbol = position.get('symbol', '').replace('_', '/')
                side = position.get('side', '').upper()
                size = position.get('size', 0)
                entry_price = position.get('entryPrice', 0)
                mark_price = position.get('markPrice', 0)
                liquidation_price = position.get('liquidationPrice', 0)
                unrealized_pnl = position.get('unrealizedPnl', 0)
                leverage = position.get('leverage', 1)
                
                message += (
                    f"*{symbol}*\n"
                    f"Side: {side}\n"
                    f"Size: {size}\n"
                    f"Entry Price: {entry_price}\n"
                    f"Mark Price: {mark_price}\n"
                    f"Liquidation Price: {liquidation_price}\n"
                    f"Unrealized PnL: {unrealized_pnl}\n"
                    f"Leverage: {leverage}x\n\n"
                )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting futures positions: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting futures positions: {str(e)}"
        )

async def futures_leverage_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set leverage for a symbol."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and leverage value.\n"
            "Example: /futures_leverage BTC/USDT 10"
        )
        return
    
    symbol = args[0]
    try:
        leverage = int(args[1])
    except ValueError:
        await update.message.reply_text("Leverage must be an integer.")
        return
    
    try:
        exchange = get_exchange('btcc_futures')
        result = exchange.set_futures_leverage(symbol, leverage)
        
        await update.message.reply_text(
            f"✅ Leverage for {symbol} has been set to {leverage}x."
        )
        
    except Exception as e:
        logger.error(f"Error setting futures leverage: {str(e)}")
        await update.message.reply_text(
            f"❌ Error setting futures leverage: {str(e)}"
        )

async def futures_long_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Open a long position."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and amount.\n"
            "Example: /futures_long BTC/USDT 0.1"
        )
        return
    
    symbol = args[0]
    try:
        amount = float(args[1])
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"futures_long_confirm_{symbol}_{amount}"),
            InlineKeyboardButton("Cancel", callback_data="futures_long_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Futures Long Position*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def futures_short_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Open a short position."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and amount.\n"
            "Example: /futures_short BTC/USDT 0.1"
        )
        return
    
    symbol = args[0]
    try:
        amount = float(args[1])
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"futures_short_confirm_{symbol}_{amount}"),
            InlineKeyboardButton("Cancel", callback_data="futures_short_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Futures Short Position*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def futures_close_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close a futures position."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide a symbol.\n"
            "Example: /futures_close BTC/USDT"
        )
        return
    
    symbol = args[0]
    
    # Ask for confirmation before closing the position
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"futures_close_confirm_{symbol}"),
            InlineKeyboardButton("Cancel", callback_data="futures_close_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Close Futures Position*\n\n"
        f"Symbol: {symbol}\n\n"
        f"Please confirm this action:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Meme Coin Commands
async def meme_trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trending meme coins."""
    try:
        trending_tokens = meme_sniper.get_trending_tokens(limit=10)
        
        if not trending_tokens:
            await update.message.reply_text(
                "No trending meme coins found. Please try again later."
            )
            return
        
        message = "🔥 *Trending Meme Coins*\n\n"
        
        for i, token in enumerate(trending_tokens, 1):
            price_change_24h = token.price_change_24h or 0
            price_change_1h = token.calculate_price_change(minutes=60) or 0
            
            message += (
                f"{i}. *{token.name} ({token.symbol})*\n"
                f"   Price: ${token.price:.8f}\n"
                f"   Market Cap: ${token.market_cap:,.0f}\n"
                f"   24h Change: {price_change_24h:.2f}%\n"
                f"   1h Change: {price_change_1h:.2f}%\n\n"
            )
        
        # Add quick buy buttons for the top 3 tokens
        keyboard = []
        for i in range(min(3, len(trending_tokens))):
            token = trending_tokens[i]
            keyboard.append([
                InlineKeyboardButton(
                    f"Buy {token.symbol}", 
                    callback_data=f"meme_quick_buy_{token.token_id}"
                )
            ])
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        
    except Exception as e:
        logger.error(f"Error getting trending meme coins: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting trending meme coins: {str(e)}"
        )

async def meme_new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show new meme coin listings."""
    try:
        new_tokens = meme_sniper.get_new_listings(days=7, limit=10)
        
        if not new_tokens:
            await update.message.reply_text(
                "No new meme coin listings found. Please try again later."
            )
            return
        
        message = "🆕 *New Meme Coin Listings*\n\n"
        
        for i, token in enumerate(new_tokens, 1):
            days_old = (datetime.now() - token.created_at).days
            hours_old = int((datetime.now() - token.created_at).total_seconds() / 3600)
            
            age_text = f"{days_old}d" if days_old > 0 else f"{hours_old}h"
            
            message += (
                f"{i}. *{token.name} ({token.symbol})*\n"
                f"   Age: {age_text}\n"
                f"   Price: ${token.price:.8f}\n"
                f"   Market Cap: ${token.market_cap:,.0f}\n"
                f"   Chain: {token.chain}\n\n"
            )
        
        # Add quick buy buttons for the top 3 tokens
        keyboard = []
        for i in range(min(3, len(new_tokens))):
            token = new_tokens[i]
            keyboard.append([
                InlineKeyboardButton(
                    f"Buy {token.symbol}", 
                    callback_data=f"meme_quick_buy_{token.token_id}"
                )
            ])
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        
    except Exception as e:
        logger.error(f"Error getting new meme coin listings: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting new meme coin listings: {str(e)}"
        )

async def set_sniper_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set up a meme coin sniper."""
    await update.message.reply_text(
        "🚀 *Meme Coin Sniper Setup*\n\n"
        "Please provide the parameters for your sniper in the following format:\n\n"
        "<min_price_change> <min_volume_change> <max_market_cap> <keywords>\n\n"
        "Example: 20 50 10000000 doge,shib,pepe\n\n"
        "This will create a sniper that alerts you when a meme coin has:\n"
        "- At least 20% price increase in 5 minutes\n"
        "- At least 50% volume increase in 5 minutes\n"
        "- Maximum market cap of $10 million\n"
        "- Contains 'doge', 'shib', or 'pepe' in the name or symbol\n\n"
        "Use 0 for any parameter you want to ignore.\n"
        "Separate keywords with commas (no spaces).",
        parse_mode='Markdown'
    )
    
    return SETTING_MEME_SNIPER

async def sniper_params_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle meme sniper parameters input."""
    user_id = update.effective_user.id
    
    try:
        # Parse parameters
        args = update.message.text.split()
        
        if len(args) < 4:
            await update.message.reply_text(
                "Please provide all required parameters: <min_price_change> <min_volume_change> <max_market_cap> <keywords>"
            )
            return SETTING_MEME_SNIPER
        
        min_price_change = float(args[0]) if args[0] != '0' else None
        min_volume_change = float(args[1]) if args[1] != '0' else None
        max_market_cap = float(args[2]) if args[2] != '0' else None
        keywords_str = args[3]
        
        # Parse keywords
        keywords = keywords_str.split(',') if keywords_str != '0' else []
        
        # Create the alert
        alert = MemeSniperAlert(
            user_id=user_id,
            min_price_change=min_price_change,
            min_volume_change=min_volume_change,
            max_market_cap=max_market_cap,
            keywords=keywords,
            auto_buy=False
        )
        
        # Add the alert to the manager
        meme_sniper.add_alert(alert)
        
        # Save alerts to file
        meme_sniper.save_data(MEME_TOKENS_FILE, MEME_ALERTS_FILE)
        
        # Ask if user wants to enable auto-buy
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"meme_auto_buy_yes_{alert.alert_id}"),
                InlineKeyboardButton("No", callback_data=f"meme_auto_buy_no_{alert.alert_id}")
            ]
        ]
        
        await update.message.reply_text(
            f"✅ Meme coin sniper has been set up with the following parameters:\n\n"
            f"Min Price Change: {min_price_change}%\n"
            f"Min Volume Change: {min_volume_change}%\n"
            f"Max Market Cap: ${max_market_cap:,.0f}\n"
            f"Keywords: {', '.join(keywords)}\n\n"
            f"Would you like to enable auto-buy for this sniper?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return ConversationHandler.END
        
    except (ValueError, IndexError) as e:
        await update.message.reply_text(
            f"❌ Error setting up sniper: {str(e)}\n"
            f"Please try again with valid parameters."
        )
        return SETTING_MEME_SNIPER

async def snipers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all active meme coin snipers for the user."""
    user_id = update.effective_user.id
    alerts = meme_sniper.get_alerts_for_user(user_id)
    
    if not alerts:
        await update.message.reply_text(
            "You don't have any active meme coin snipers. Use /set_sniper to create one."
        )
        return
    
    message = "🚀 *Your Active Meme Coin Snipers*\n\n"
    
    for i, alert in enumerate(alerts, 1):
        message += (
            f"{i}. *Sniper {i}*\n"
            f"   ID: {alert.alert_id}\n"
            f"   Min Price Change: {alert.min_price_change}%\n"
            f"   Min Volume Change: {alert.min_volume_change}%\n"
            f"   Max Market Cap: ${alert.max_market_cap:,.0f}\n"
            f"   Keywords: {', '.join(alert.keywords)}\n"
            f"   Auto-Buy: {'Enabled' if alert.auto_buy else 'Disabled'}\n\n"
        )
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def remove_sniper_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a meme coin sniper."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide the sniper ID to remove.\n"
            "Example: /remove_sniper meme_sniper_123456\n\n"
            "You can see your sniper IDs with the /snipers command."
        )
        return
    
    alert_id = args[0]
    
    # Check if the alert exists and belongs to the user
    alert = meme_sniper.get_alert(alert_id)
    if not alert or alert.user_id != update.effective_user.id:
        await update.message.reply_text(
            "❌ Sniper not found or you don't have permission to remove it."
        )
        return
    
    # Remove the alert
    success = meme_sniper.remove_alert(alert_id)
    
    if success:
        # Save alerts to file
        meme_sniper.save_data(MEME_TOKENS_FILE, MEME_ALERTS_FILE)
        
        await update.message.reply_text(
            f"✅ Meme coin sniper has been removed."
        )
    else:
        await update.message.reply_text(
            "❌ Failed to remove the sniper. Please try again."
        )

# Photon-SOL Commands
async def photon_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get current price for a token on Photon-SOL."""
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "Please provide a symbol.\n"
            "Example: /photon_price SOL/USDC"
        )
        return
    
    symbol = args[0]
    
    try:
        exchange = get_exchange('photon_sol')
        ticker = exchange.get_ticker(symbol)
        
        price = ticker.get('price', 'N/A')
        change_24h = ticker.get('change_24h', 'N/A')
        volume_24h = ticker.get('volume_24h', 'N/A')
        
        message = (
            f"📊 *{symbol} Price on Photon-SOL*\n\n"
            f"Current Price: {price}\n"
            f"24h Change: {change_24h}%\n"
            f"24h Volume: {volume_24h}\n\n"
            f"_Updated: {update.message.date.strftime('%Y-%m-%d %H:%M:%S UTC')}_"
        )
        
        # Add price alert button
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔔 Set Price Alert", 
                    callback_data=f"set_alert_{symbol}_photon_sol"
                )
            ]
        ]
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error getting Photon-SOL price: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting price: {str(e)}"
        )

async def photon_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check Photon-SOL wallet balance."""
    try:
        exchange = get_exchange('photon_sol')
        balances = exchange.get_balance()
        
        # Filter out zero balances and format the response
        non_zero_balances = {k: v for k, v in balances.items() if v > 0}
        
        if not non_zero_balances:
            message = "No assets found in your Photon-SOL wallet."
        else:
            message = f"💰 *Your Photon-SOL Wallet Balance*\n\n"
            for asset, amount in non_zero_balances.items():
                message += f"{asset}: {amount}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting Photon-SOL balance: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting balance: {str(e)}"
        )

async def photon_buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Place a market buy order on Photon-SOL."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and amount.\n"
            "Example: /photon_buy SOL/USDC 0.1"
        )
        return
    
    symbol = args[0]
    amount = float(args[1])
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"photon_buy_confirm_{symbol}_{amount}"),
            InlineKeyboardButton("Cancel", callback_data="photon_buy_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Photon-SOL Market Buy Order*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def photon_sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Place a market sell order on Photon-SOL."""
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "Please provide a symbol and amount.\n"
            "Example: /photon_sell SOL/USDC 0.1"
        )
        return
    
    symbol = args[0]
    amount = float(args[1])
    
    # Ask for confirmation before placing the order
    keyboard = [
        [
            InlineKeyboardButton("Confirm", callback_data=f"photon_sell_confirm_{symbol}_{amount}"),
            InlineKeyboardButton("Cancel", callback_data="photon_sell_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *Confirm Photon-SOL Market Sell Order*\n\n"
        f"Symbol: {symbol}\n"
        f"Amount: {amount}\n\n"
        f"Please confirm this order:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def photon_tokens_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List available tokens on Photon-SOL."""
    try:
        exchange = get_exchange('photon_sol')
        tokens = exchange.list_tokens()
        
        if not tokens:
            await update.message.reply_text(
                "No tokens found on Photon-SOL. Please try again later."
            )
            return
        
        # Limit to top 10 tokens to avoid message length issues
        tokens = tokens[:10]
        
        message = "🪙 *Available Tokens on Photon-SOL*\n\n"
        
        for i, token in enumerate(tokens, 1):
            symbol = token.get('symbol', 'Unknown')
            name = token.get('name', 'Unknown')
            price = token.get('price', 'N/A')
            
            message += (
                f"{i}. *{symbol}* ({name})\n"
                f"   Price: {price}\n\n"
            )
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error getting Photon-SOL tokens: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting tokens: {str(e)}"
        )

async def photon_trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trending tokens on Photon-SOL."""
    try:
        exchange = get_exchange('photon_sol')
        trending_tokens = exchange.get_trending_tokens(limit=10)
        
        if not trending_tokens:
            await update.message.reply_text(
                "No trending tokens found on Photon-SOL. Please try again later."
            )
            return
        
        message = "🔥 *Trending Tokens on Photon-SOL*\n\n"
        
        for i, token in enumerate(trending_tokens, 1):
            symbol = token.get('symbol', 'Unknown')
            name = token.get('name', 'Unknown')
            price = token.get('price', 'N/A')
            change_24h = token.get('change_24h', 'N/A')
            
            message += (
                f"{i}. *{symbol}* ({name})\n"
                f"   Price: {price}\n"
                f"   24h Change: {change_24h}%\n\n"
            )
        
        # Add quick buy buttons for the top 3 tokens
        keyboard = []
        for i in range(min(3, len(trending_tokens))):
            token = trending_tokens[i]
            symbol = token.get('symbol', 'Unknown')
            keyboard.append([
                InlineKeyboardButton(
                    f"Buy {symbol}", 
                    callback_data=f"photon_quick_buy_{symbol}"
                )
            ])
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        
    except Exception as e:
        logger.error(f"Error getting Photon-SOL trending tokens: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting trending tokens: {str(e)}"
        )

async def photon_new_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show new token listings on Photon-SOL."""
    try:
        exchange = get_exchange('photon_sol')
        new_tokens = exchange.get_new_tokens(days=7, limit=10)
        
        if not new_tokens:
            await update.message.reply_text(
                "No new token listings found on Photon-SOL. Please try again later."
            )
            return
        
        message = "🆕 *New Token Listings on Photon-SOL*\n\n"
        
        for i, token in enumerate(new_tokens, 1):
            symbol = token.get('symbol', 'Unknown')
            name = token.get('name', 'Unknown')
            price = token.get('price', 'N/A')
            age = token.get('age', 'Unknown')
            
            message += (
                f"{i}. *{symbol}* ({name})\n"
                f"   Price: {price}\n"
                f"   Age: {age}\n\n"
            )
        
        # Add quick buy buttons for the top 3 tokens
        keyboard = []
        for i in range(min(3, len(new_tokens))):
            token = new_tokens[i]
            symbol = token.get('symbol', 'Unknown')
            keyboard.append([
                InlineKeyboardButton(
                    f"Buy {symbol}", 
                    callback_data=f"photon_quick_buy_{symbol}"
                )
            ])
        
        await update.message.reply_text(
            message, 
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
        
    except Exception as e:
        logger.error(f"Error getting Photon-SOL new tokens: {str(e)}")
        await update.message.reply_text(
            f"❌ Error getting new tokens: {str(e)}"
        )

# Callback query handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Handle buy/sell order confirmations
    if callback_data.startswith("buy_confirm_"):
        # Extract data from callback
        _, _, symbol, amount, exchange_name = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange(exchange_name)
            result = exchange.place_market_order(symbol, "buy", amount)
            
            # Format response based on exchange
            if exchange_name == 'btcc':
                order_id = result.get('data', {}).get('orderId', 'Unknown')
            elif exchange_name == 'coinbase':
                order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Market buy order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Exchange: {exchange_name.upper()}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing buy order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing buy order: {str(e)}"
            )
    
    elif callback_data == "buy_cancel":
        await query.edit_message_text("Buy order cancelled.")
    
    elif callback_data.startswith("sell_confirm_"):
        # Extract data from callback
        _, _, symbol, amount, exchange_name = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange(exchange_name)
            result = exchange.place_market_order(symbol, "sell", amount)
            
            # Format response based on exchange
            if exchange_name == 'btcc':
                order_id = result.get('data', {}).get('orderId', 'Unknown')
            elif exchange_name == 'coinbase':
                order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Market sell order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Exchange: {exchange_name.upper()}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing sell order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing sell order: {str(e)}"
            )
    
    elif callback_data == "sell_cancel":
        await query.edit_message_text("Sell order cancelled.")
    
    elif callback_data.startswith("limit_buy_confirm_"):
        # Extract data from callback
        _, _, _, symbol, amount, price, exchange_name = callback_data.split("_", 6)
        amount = float(amount)
        price = float(price)
        
        try:
            exchange = get_exchange(exchange_name)
            result = exchange.place_limit_order(symbol, "buy", amount, price)
            
            # Format response based on exchange
            if exchange_name == 'btcc':
                order_id = result.get('data', {}).get('orderId', 'Unknown')
            elif exchange_name == 'coinbase':
                order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Limit buy order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Price: {price}\n"
                f"Exchange: {exchange_name.upper()}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing limit buy order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing limit buy order: {str(e)}"
            )
    
    elif callback_data == "limit_buy_cancel":
        await query.edit_message_text("Limit buy order cancelled.")
    
    elif callback_data.startswith("limit_sell_confirm_"):
        # Extract data from callback
        _, _, _, symbol, amount, price, exchange_name = callback_data.split("_", 6)
        amount = float(amount)
        price = float(price)
        
        try:
            exchange = get_exchange(exchange_name)
            result = exchange.place_limit_order(symbol, "sell", amount, price)
            
            # Format response based on exchange
            if exchange_name == 'btcc':
                order_id = result.get('data', {}).get('orderId', 'Unknown')
            elif exchange_name == 'coinbase':
                order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Limit sell order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Price: {price}\n"
                f"Exchange: {exchange_name.upper()}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing limit sell order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing limit sell order: {str(e)}"
            )
    
    elif callback_data == "limit_sell_cancel":
        await query.edit_message_text("Limit sell order cancelled.")
    
    # Handle price alert setup
    elif callback_data.startswith("set_alert_"):
        # Extract data from callback
        _, symbol, exchange_name = callback_data.split("_", 2)
        
        # Get current price
        try:
            exchange = get_exchange(exchange_name)
            ticker = exchange.get_ticker(symbol)
            
            # Format the response based on the exchange
            if exchange_name == 'btcc':
                current_price = float(ticker.get('data', {}).get('last', 0))
            elif exchange_name == 'coinbase':
                current_price = float(ticker.get('price', 0))
            else:
                current_price = 0
            
            # Create keyboard for alert condition
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"Price Above {current_price * 1.05:.2f}", 
                        callback_data=f"alert_set_{symbol}_{exchange_name}_above_{current_price * 1.05:.2f}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"Price Below {current_price * 0.95:.2f}", 
                        callback_data=f"alert_set_{symbol}_{exchange_name}_below_{current_price * 0.95:.2f}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Custom Alert", 
                        callback_data=f"alert_custom_{symbol}_{exchange_name}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Cancel", 
                        callback_data="alert_cancel"
                    )
                ]
            ]
            
            await query.edit_message_text(
                f"🔔 *Set Price Alert for {symbol}*\n\n"
                f"Current Price: {current_price}\n\n"
                f"Choose an alert condition:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error setting up price alert: {str(e)}")
            await query.edit_message_text(
                f"❌ Error setting up price alert: {str(e)}"
            )
    
    elif callback_data.startswith("alert_set_"):
        # Extract data from callback
        _, _, symbol, exchange_name, condition, price = callback_data.split("_", 5)
        price = float(price)
        
        # Create the alert
        alert = PriceAlert(
            user_id=query.from_user.id,
            symbol=symbol,
            exchange=exchange_name,
            target_price=price,
            condition=condition
        )
        
        # Add the alert to the manager
        price_alert_manager.add_alert(alert)
        
        # Save alerts to file
        price_alert_manager.save_alerts(ALERTS_FILE)
        
        await query.edit_message_text(
            f"✅ Price alert set for {symbol} on {exchange_name.upper()}.\n"
            f"You will be notified when the price goes {condition} {price}.\n\n"
            f"Alert ID: {alert.alert_id}"
        )
    
    elif callback_data == "alert_cancel":
        await query.edit_message_text("Price alert setup cancelled.")
    
    # Handle futures trading confirmations
    elif callback_data.startswith("futures_long_confirm_"):
        # Extract data from callback
        _, _, _, symbol, amount = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange('btcc_futures')
            result = exchange.place_futures_market_order(symbol, "buy", amount)
            
            order_id = result.get('data', {}).get('orderId', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Futures long position opened successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error opening futures long position: {str(e)}")
            await query.edit_message_text(
                f"❌ Error opening futures long position: {str(e)}"
            )
    
    elif callback_data == "futures_long_cancel":
        await query.edit_message_text("Futures long position cancelled.")
    
    elif callback_data.startswith("futures_short_confirm_"):
        # Extract data from callback
        _, _, _, symbol, amount = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange('btcc_futures')
            result = exchange.place_futures_market_order(symbol, "sell", amount)
            
            order_id = result.get('data', {}).get('orderId', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Futures short position opened successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error opening futures short position: {str(e)}")
            await query.edit_message_text(
                f"❌ Error opening futures short position: {str(e)}"
            )
    
    elif callback_data == "futures_short_cancel":
        await query.edit_message_text("Futures short position cancelled.")
    
    elif callback_data.startswith("futures_close_confirm_"):
        # Extract data from callback
        _, _, _, symbol = callback_data.split("_", 3)
        
        try:
            exchange = get_exchange('btcc_futures')
            result = exchange.close_futures_position(symbol)
            
            if result.get('success', False):
                await query.edit_message_text(
                    f"✅ Futures position for {symbol} closed successfully!"
                )
            else:
                await query.edit_message_text(
                    f"❌ Failed to close futures position: {result.get('message', 'Unknown error')}"
                )
            
        except Exception as e:
            logger.error(f"Error closing futures position: {str(e)}")
            await query.edit_message_text(
                f"❌ Error closing futures position: {str(e)}"
            )
    
    elif callback_data == "futures_close_cancel":
        await query.edit_message_text("Futures position closure cancelled.")
    
    # Handle Photon-SOL trading confirmations
    elif callback_data.startswith("photon_buy_confirm_"):
        # Extract data from callback
        _, _, _, symbol, amount = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange('photon_sol')
            result = exchange.place_market_order(symbol, "buy", amount)
            
            order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Photon-SOL market buy order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing Photon-SOL buy order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing buy order: {str(e)}"
            )
    
    elif callback_data == "photon_buy_cancel":
        await query.edit_message_text("Photon-SOL buy order cancelled.")
    
    elif callback_data.startswith("photon_sell_confirm_"):
        # Extract data from callback
        _, _, _, symbol, amount = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange('photon_sol')
            result = exchange.place_market_order(symbol, "sell", amount)
            
            order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Photon-SOL market sell order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: {amount}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing Photon-SOL sell order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing sell order: {str(e)}"
            )
    
    elif callback_data == "photon_sell_cancel":
        await query.edit_message_text("Photon-SOL sell order cancelled.")
    
    elif callback_data.startswith("photon_quick_buy_"):
        # Extract data from callback
        _, _, _, symbol = callback_data.split("_", 3)
        
        # Ask for buy amount
        keyboard = [
            [
                InlineKeyboardButton("$10", callback_data=f"photon_buy_amount_{symbol}_10"),
                InlineKeyboardButton("$50", callback_data=f"photon_buy_amount_{symbol}_50"),
                InlineKeyboardButton("$100", callback_data=f"photon_buy_amount_{symbol}_100")
            ],
            [
                InlineKeyboardButton("$500", callback_data=f"photon_buy_amount_{symbol}_500"),
                InlineKeyboardButton("$1000", callback_data=f"photon_buy_amount_{symbol}_1000"),
                InlineKeyboardButton("Custom", callback_data=f"photon_buy_custom_{symbol}")
            ],
            [
                InlineKeyboardButton("Cancel", callback_data="photon_buy_cancel")
            ]
        ]
        
        await query.edit_message_text(
            f"💰 *Quick Buy {symbol} on Photon-SOL*\n\n"
            f"Select amount to buy:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("photon_buy_amount_"):
        # Extract data from callback
        _, _, _, symbol, amount = callback_data.split("_", 4)
        amount = float(amount)
        
        try:
            exchange = get_exchange('photon_sol')
            result = exchange.place_market_order(symbol, "buy", amount)
            
            order_id = result.get('order_id', 'Unknown')
            
            await query.edit_message_text(
                f"✅ Photon-SOL market buy order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: ${amount}\n"
                f"Order ID: {order_id}"
            )
            
        except Exception as e:
            logger.error(f"Error placing Photon-SOL quick buy order: {str(e)}")
            await query.edit_message_text(
                f"❌ Error placing buy order: {str(e)}"
            )
    
    elif callback_data.startswith("photon_buy_custom_"):
        # Extract symbol
        _, _, _, symbol = callback_data.split("_", 3)
        
        await query.edit_message_text(
            "Please enter the amount in USD to buy.\n\n"
            "Reply to this message with the amount (e.g., 100)."
        )
        
        # Store the symbol in user data for the next step
        context.user_data['photon_buy_symbol'] = symbol
    
    # Handle meme coin auto-buy setup
    elif callback_data.startswith("meme_auto_buy_yes_"):
        # Extract data from callback
        _, _, _, _, alert_id = callback_data.split("_", 4)
        
        # Get the alert
        alert = meme_sniper.get_alert(alert_id)
        if not alert:
            await query.edit_message_text(
                "❌ Sniper not found. Please try setting it up again."
            )
            return
        
        # Ask for auto-buy amount
        await query.edit_message_text(
            "Please enter the amount in USD to auto-buy when the sniper is triggered.\n\n"
            "Reply to this message with the amount (e.g., 100)."
        )
        
        # Store the alert ID in user data for the next step
        context.user_data['auto_buy_alert_id'] = alert_id
        
    elif callback_data.startswith("meme_auto_buy_no_"):
        await query.edit_message_text(
            "✅ Meme coin sniper setup complete. Auto-buy is disabled.\n\n"
            "You will receive notifications when the sniper detects matching tokens."
        )
    
    # Handle meme coin quick buy
    elif callback_data.startswith("meme_quick_buy_"):
        # Extract data from callback
        _, _, _, token_id = callback_data.split("_", 3)
        
        # Get the token
        token = None
        with meme_sniper.lock:
            token = meme_sniper.tokens.get(token_id)
        
        if not token:
            await query.edit_message_text(
                "❌ Token not found. It may have been removed or expired."
            )
            return
        
        # Ask for buy amount
        keyboard = [
            [
                InlineKeyboardButton("$10", callback_data=f"meme_buy_{token_id}_10"),
                InlineKeyboardButton("$50", callback_data=f"meme_buy_{token_id}_50"),
                InlineKeyboardButton("$100", callback_data=f"meme_buy_{token_id}_100")
            ],
            [
                InlineKeyboardButton("$500", callback_data=f"meme_buy_{token_id}_500"),
                InlineKeyboardButton("$1000", callback_data=f"meme_buy_{token_id}_1000"),
                InlineKeyboardButton("Custom", callback_data=f"meme_buy_custom_{token_id}")
            ],
            [
                InlineKeyboardButton("Cancel", callback_data="meme_buy_cancel")
            ]
        ]
        
        await query.edit_message_text(
            f"💰 *Quick Buy {token.name} ({token.symbol})*\n\n"
            f"Current Price: ${token.price:.8f}\n"
            f"Chain: {token.chain}\n\n"
            f"Select amount to buy:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("meme_buy_"):
        if callback_data == "meme_buy_cancel":
            await query.edit_message_text("Buy operation cancelled.")
            return
        
        if callback_data.startswith("meme_buy_custom_"):
            # Extract token ID
            _, _, _, token_id = callback_data.split("_", 3)
            
            await query.edit_message_text(
                "Please enter the amount in USD to buy.\n\n"
                "Reply to this message with the amount (e.g., 100)."
            )
            
            # Store the token ID in user data for the next step
            context.user_data['buy_token_id'] = token_id
            return
        
        # Extract data from callback
        _, _, token_id, amount = callback_data.split("_", 3)
        amount = float(amount)
        
        # Get the token
        token = None
        with meme_sniper.lock:
            token = meme_sniper.tokens.get(token_id)
        
        if not token:
            await query.edit_message_text(
                "❌ Token not found. It may have been removed or expired."
            )
            return
        
        # Simulate buying the token
        # In a real implementation, this would call the appropriate exchange API
        await query.edit_message_text(
            f"💰 *Buy Order Executed*\n\n"
            f"Token: {token.name} ({token.symbol})\n"
            f"Amount: ${amount:.2f}\n"
            f"Price: ${token.price:.8f}\n"
            f"Chain: {token.chain}\n\n"
            f"_Order executed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_",
            parse_mode='Markdown'
        )

# Message handlers
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages."""
    text = update.message.text
    
    # Handle auto-buy amount input
    if 'auto_buy_alert_id' in context.user_data:
        alert_id = context.user_data.pop('auto_buy_alert_id')
        
        try:
            amount = float(text)
            
            # Get the alert
            alert = meme_sniper.get_alert(alert_id)
            if not alert:
                await update.message.reply_text(
                    "❌ Sniper not found. Please try setting it up again."
                )
                return
            
            # Enable auto-buy
            alert.auto_buy = True
            alert.auto_buy_amount = amount
            
            # Save alerts to file
            meme_sniper.save_data(MEME_TOKENS_FILE, MEME_ALERTS_FILE)
            
            await update.message.reply_text(
                f"✅ Auto-buy enabled for meme coin sniper.\n\n"
                f"Amount: ${amount:.2f}\n\n"
                f"You will receive notifications when tokens are automatically purchased."
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a number."
            )
    
    # Handle custom buy amount input
    elif 'buy_token_id' in context.user_data:
        token_id = context.user_data.pop('buy_token_id')
        
        try:
            amount = float(text)
            
            # Get the token
            token = None
            with meme_sniper.lock:
                token = meme_sniper.tokens.get(token_id)
            
            if not token:
                await update.message.reply_text(
                    "❌ Token not found. It may have been removed or expired."
                )
                return
            
            # Simulate buying the token
            # In a real implementation, this would call the appropriate exchange API
            await update.message.reply_text(
                f"💰 *Buy Order Executed*\n\n"
                f"Token: {token.name} ({token.symbol})\n"
                f"Amount: ${amount:.2f}\n"
                f"Price: ${token.price:.8f}\n"
                f"Chain: {token.chain}\n\n"
                f"_Order executed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a number."
            )
    
    # Handle Photon-SOL custom buy amount input
    elif 'photon_buy_symbol' in context.user_data:
        symbol = context.user_data.pop('photon_buy_symbol')
        
        try:
            amount = float(text)
            
            # Execute the buy order
            exchange = get_exchange('photon_sol')
            result = exchange.place_market_order(symbol, "buy", amount)
            
            order_id = result.get('order_id', 'Unknown')
            
            await update.message.reply_text(
                f"✅ Photon-SOL market buy order placed successfully!\n\n"
                f"Symbol: {symbol}\n"
                f"Amount: ${amount:.2f}\n"
                f"Order ID: {order_id}\n\n"
                f"_Order executed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a number."
            )
        except Exception as e:
            logger.error(f"Error placing Photon-SOL buy order: {str(e)}")
            await update.message.reply_text(
                f"❌ Error placing buy order: {str(e)}"
            )
    
    # Handle custom keyboard menu selections
    elif text == "💰 Balance":
        # Show balance menu
        keyboard = [
            [KeyboardButton("BTCC Balance"), KeyboardButton("Coinbase Balance")],
            [KeyboardButton("BTCC Futures Balance"), KeyboardButton("Back to Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Select an exchange to check your balance:",
            reply_markup=reply_markup
        )
    
    elif text == "📊 Markets":
        # Show markets menu
        keyboard = [
            [KeyboardButton("BTC Price"), KeyboardButton("ETH Price")],
            [KeyboardButton("Check Other Price"), KeyboardButton("Order Book")],
            [KeyboardButton("Back to Main Menu")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "Select a market option:",
            reply_markup=reply_markup
        )
    
    elif text == "⚙️ Trading":
        # Show trading menu
        keyboard = KeyboardFactory.create_trading_keyboard()
        
        await update.message.reply_text(
            "Select a trading option:",
            reply_markup=keyboard
        )
    
    elif text == "🔔 Alerts":
        # Show alerts menu
        keyboard = KeyboardFactory.create_alerts_keyboard()
        
        await update.message.reply_text(
            "Select an alerts option:",
            reply_markup=keyboard
        )
    
    elif text == "📈 Futures":
        # Show futures menu
        keyboard = KeyboardFactory.create_futures_keyboard()
        
        await update.message.reply_text(
            "Select a futures trading option:",
            reply_markup=keyboard
        )
    
    elif text == "🚀 Meme Coins":
        # Show meme coins menu
        keyboard = KeyboardFactory.create_meme_coins_keyboard()
        
        await update.message.reply_text(
            "Select a meme coins option:",
            reply_markup=keyboard
        )
    
    elif text == "ℹ️ Help":
        # Show help message
        await help_command(update, context)
    
    elif text == "Back to Main Menu":
        # Show main menu
        keyboard = KeyboardFactory.create_main_menu_keyboard()
        
        await update.message.reply_text(
            "Main Menu:",
            reply_markup=keyboard
        )
    
    # Handle specific keyboard actions
    elif text == "BTCC Balance":
        # Create args for the balance command
        context.args = ["btcc"]
        await balance_command(update, context)
    
    elif text == "Coinbase Balance":
        # Create args for the balance command
        context.args = ["coinbase"]
        await balance_command(update, context)
    
    elif text == "BTCC Futures Balance":
        await futures_balance_command(update, context)
    
    elif text == "BTC Price":
        # Create args for the price command
        context.args = ["BTC/USDT", "btcc"]
        await price_command(update, context)
    
    elif text == "ETH Price":
        # Create args for the price command
        context.args = ["ETH/USDT", "btcc"]
        await price_command(update, context)
    
    elif text == "Check Other Price":
        await update.message.reply_text(
            "Please use the /price command with a symbol and exchange name.\n"
            "Example: /price BTC/USDT btcc"
        )
    
    elif text == "Order Book":
        await update.message.reply_text(
            "Please use the /orderbook command with a symbol and exchange name.\n"
            "Example: /orderbook BTC/USDT btcc"
        )
    
    elif text == "Buy":
        await update.message.reply_text(
            "Please use the /buy command with a symbol, amount, and exchange name.\n"
            "Example: /buy BTC/USDT 0.001 btcc"
        )
    
    elif text == "Sell":
        await update.message.reply_text(
            "Please use the /sell command with a symbol, amount, and exchange name.\n"
            "Example: /sell BTC/USDT 0.001 btcc"
        )
    
    elif text == "Limit Buy":
        await update.message.reply_text(
            "Please use the /limit_buy command with a symbol, amount, price, and exchange name.\n"
            "Example: /limit_buy BTC/USDT 0.001 50000 btcc"
        )
    
    elif text == "Limit Sell":
        await update.message.reply_text(
            "Please use the /limit_sell command with a symbol, amount, price, and exchange name.\n"
            "Example: /limit_sell BTC/USDT 0.001 60000 btcc"
        )
    
    elif text == "Cancel Order":
        await update.message.reply_text(
            "Please use the /cancel command with an order ID, symbol, and exchange name.\n"
            "Example: /cancel 123456 BTC/USDT btcc"
        )
    
    elif text == "Auto Trading":
        await update.message.reply_text(
            "Automatic Trading Options:\n\n"
            "/set_strategy - Set up a new trading strategy\n"
            "/strategies - List your active strategies\n"
            "/remove_strategy - Remove a strategy\n"
            "/run_strategy - Run a strategy once"
        )
    
    elif text == "Set Alert":
        await update.message.reply_text(
            "Please use the /set_alert command with a symbol, price, condition, and exchange name.\n"
            "Example: /set_alert BTC/USDT 50000 above btcc"
        )
    
    elif text == "My Alerts":
        await alerts_command(update, context)
    
    elif text == "Remove Alert":
        await update.message.reply_text(
            "Please use the /remove_alert command with an alert ID.\n"
            "Example: /remove_alert alert_123456\n\n"
            "You can see your alert IDs with the /alerts command."
        )
    
    elif text == "Long":
        await update.message.reply_text(
            "Please use the /futures_long command with a symbol and amount.\n"
            "Example: /futures_long BTC/USDT 0.1"
        )
    
    elif text == "Short":
        await update.message.reply_text(
            "Please use the /futures_short command with a symbol and amount.\n"
            "Example: /futures_short BTC/USDT 0.1"
        )
    
    elif text == "Close Position":
        await update.message.reply_text(
            "Please use the /futures_close command with a symbol.\n"
            "Example: /futures_close BTC/USDT"
        )
    
    elif text == "Set Leverage":
        await update.message.reply_text(
            "Please use the /futures_leverage command with a symbol and leverage value.\n"
            "Example: /futures_leverage BTC/USDT 10"
        )
    
    elif text == "Funding Rate":
        await update.message.reply_text(
            "Please provide a symbol to check the funding rate.\n"
            "Example: BTC/USDT"
        )
        context.user_data['expecting_funding_rate'] = True
    
    elif text == "New Listings":
        await meme_new_command(update, context)
    
    elif text == "Trending":
        await meme_trending_command(update, context)
    
    elif text == "Set Sniper":
        await set_sniper_command(update, context)
    
    elif text == "My Snipers":
        await snipers_command(update, context)
    
    elif text == "Quick Buy":
        await update.message.reply_text(
            "Please use the /meme_trending or /meme_new commands to see available tokens for quick buy."
        )
    
    # Handle funding rate check
    elif context.user_data.get('expecting_funding_rate'):
        context.user_data.pop('expecting_funding_rate', None)
        symbol = text
        
        try:
            exchange = get_exchange('btcc_futures')
            result = exchange.get_futures_funding_rate(symbol)
            
            funding_rate = result.get('data', {}).get('fundingRate', 'N/A')
            next_funding_time = result.get('data', {}).get('nextFundingTime', 'N/A')
            
            await update.message.reply_text(
                f"📊 *Funding Rate for {symbol}*\n\n"
                f"Current Rate: {funding_rate}\n"
                f"Next Funding Time: {next_funding_time}\n\n"
                f"_Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}_",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error getting funding rate: {str(e)}")
            await update.message.reply_text(
                f"❌ Error getting funding rate: {str(e)}"
            )
    
    else:
        # Unknown command
        await update.message.reply_text(
            "I don't understand that command. Use /help to see available commands."
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram-python-bot library."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Send a message to the user
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. The error has been logged and will be addressed."
        )

def main() -> None:
    """Start the bot."""
    global application
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("buy", buy_command))
    application.add_handler(CommandHandler("sell", sell_command))
    application.add_handler(CommandHandler("limit_buy", limit_buy_command))
    application.add_handler(CommandHandler("limit_sell", limit_sell_command))
    application.add_handler(CommandHandler("orderbook", orderbook_command))
    application.add_handler(CommandHandler("cancel", cancel_order_command))
    
    # Add price alert handlers
    application.add_handler(CommandHandler("set_alert", set_alert_command))
    application.add_handler(CommandHandler("alerts", alerts_command))
    application.add_handler(CommandHandler("remove_alert", remove_alert_command))
    
    # Add strategy handlers
    strategy_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_strategy", set_strategy_command)],
        states={
            SETTING_STRATEGY: [MessageHandler(filters.TEXT & ~filters.COMMAND, strategy_params_handler)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(strategy_conv_handler)
    application.add_handler(CommandHandler("strategies", strategies_command))
    application.add_handler(CommandHandler("remove_strategy", remove_strategy_command))
    application.add_handler(CommandHandler("run_strategy", run_strategy_command))
    
    # Add futures trading handlers
    application.add_handler(CommandHandler("futures_balance", futures_balance_command))
    application.add_handler(CommandHandler("futures_positions", futures_positions_command))
    application.add_handler(CommandHandler("futures_leverage", futures_leverage_command))
    application.add_handler(CommandHandler("futures_long", futures_long_command))
    application.add_handler(CommandHandler("futures_short", futures_short_command))
    application.add_handler(CommandHandler("futures_close", futures_close_command))
    
    # Add meme coin handlers
    meme_sniper_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_sniper", set_sniper_command)],
        states={
            SETTING_MEME_SNIPER: [MessageHandler(filters.TEXT & ~filters.COMMAND, sniper_params_handler)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    application.add_handler(meme_sniper_conv_handler)
    application.add_handler(CommandHandler("meme_trending", meme_trending_command))
    application.add_handler(CommandHandler("meme_new", meme_new_command))
    application.add_handler(CommandHandler("snipers", snipers_command))
    application.add_handler(CommandHandler("remove_sniper", remove_sniper_command))
    
    # Add Photon-SOL handlers
    application.add_handler(CommandHandler("photon_price", photon_price_command))
    application.add_handler(CommandHandler("photon_balance", photon_balance_command))
    application.add_handler(CommandHandler("photon_buy", photon_buy_command))
    application.add_handler(CommandHandler("photon_sell", photon_sell_command))
    application.add_handler(CommandHandler("photon_tokens", photon_tokens_command))
    application.add_handler(CommandHandler("photon_trending", photon_trending_command))
    application.add_handler(CommandHandler("photon_new", photon_new_command))
    
    # Add callback query handler for button callbacks
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Load saved data
    price_alert_manager.load_alerts(ALERTS_FILE)
    strategy_manager.load_strategies(STRATEGIES_FILE)
    meme_sniper.load_data(MEME_TOKENS_FILE, MEME_ALERTS_FILE)
    
    # Start monitoring
    price_alert_manager.start_monitoring()
    scheduler.start()
    meme_sniper.start_monitoring()
    
    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

