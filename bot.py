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

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

BTCC_API_KEY = os.getenv("BTCC_API_KEY")
BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")

# Set up Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

# Import utility modules
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
