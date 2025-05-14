
"""
Custom Keyboards for Crypto Trading Telegram Bot.

This module provides functionality for creating custom keyboards and inline keyboards
for the Telegram bot interface.
"""

from typing import List, Dict, Any, Optional, Union
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class KeyboardFactory:
    """
    Factory class for creating various types of keyboards for the Telegram bot.
    """
    
    @staticmethod
    def create_main_menu_keyboard() -> ReplyKeyboardMarkup:
        """
        Create the main menu keyboard with common commands.
        
        Returns:
            ReplyKeyboardMarkup: Main menu keyboard
        """
        keyboard = [
            [KeyboardButton("💰 Balance"), KeyboardButton("📊 Markets")],
            [KeyboardButton("⚙️ Trading"), KeyboardButton("🔔 Alerts")],
            [KeyboardButton("📈 Futures"), KeyboardButton("🚀 Meme Coins")],
            [KeyboardButton("ℹ️ Help")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_trading_keyboard() -> ReplyKeyboardMarkup:
        """
        Create the trading menu keyboard.
        
        Returns:
            ReplyKeyboardMarkup: Trading menu keyboard
        """
        keyboard = [
            [KeyboardButton("Buy"), KeyboardButton("Sell")],
            [KeyboardButton("Limit Buy"), KeyboardButton("Limit Sell")],
            [KeyboardButton("Order Book"), KeyboardButton("Cancel Order")],
            [KeyboardButton("Auto Trading"), KeyboardButton("Back to Main Menu")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_futures_keyboard() -> ReplyKeyboardMarkup:
        """
        Create the futures trading menu keyboard.
        
        Returns:
            ReplyKeyboardMarkup: Futures trading menu keyboard
        """
        keyboard = [
            [KeyboardButton("Long"), KeyboardButton("Short")],
            [KeyboardButton("Close Position"), KeyboardButton("Set Leverage")],
            [KeyboardButton("Stop Loss"), KeyboardButton("Take Profit")],
            [KeyboardButton("Funding Rate"), KeyboardButton("Back to Main Menu")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_alerts_keyboard() -> ReplyKeyboardMarkup:
        """
        Create the price alerts menu keyboard.
        
        Returns:
            ReplyKeyboardMarkup: Price alerts menu keyboard
        """
        keyboard = [
            [KeyboardButton("Set Alert"), KeyboardButton("My Alerts")],
            [KeyboardButton("Remove Alert"), KeyboardButton("Back to Main Menu")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_meme_coins_keyboard() -> ReplyKeyboardMarkup:
        """
        Create the meme coins menu keyboard.
        
        Returns:
            ReplyKeyboardMarkup: Meme coins menu keyboard
        """
        keyboard = [
            [KeyboardButton("New Listings"), KeyboardButton("Trending")],
            [KeyboardButton("Set Sniper"), KeyboardButton("My Snipers")],
            [KeyboardButton("Quick Buy"), KeyboardButton("Back to Main Menu")]
        ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def create_exchange_selection_keyboard() -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for selecting an exchange.
        
        Returns:
            InlineKeyboardMarkup: Exchange selection keyboard
        """
        keyboard = [
            [
                InlineKeyboardButton("BTCC", callback_data="exchange_btcc"),
                InlineKeyboardButton("Coinbase", callback_data="exchange_coinbase")
            ],
            [InlineKeyboardButton("Cancel", callback_data="exchange_cancel")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_confirmation_keyboard(action: str, params: Dict[str, Any]) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for confirming an action.
        
        Args:
            action (str): Action to confirm (e.g., 'buy', 'sell', 'alert')
            params (Dict[str, Any]): Parameters for the action
            
        Returns:
            InlineKeyboardMarkup: Confirmation keyboard
        """
        # Create a callback data string with action and parameters
        callback_data = f"{action}_confirm"
        for key, value in params.items():
            callback_data += f"_{key}_{value}"
        
        keyboard = [
            [
                InlineKeyboardButton("Confirm", callback_data=callback_data),
                InlineKeyboardButton("Cancel", callback_data=f"{action}_cancel")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_alert_condition_keyboard() -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for selecting an alert condition.
        
        Returns:
            InlineKeyboardMarkup: Alert condition keyboard
        """
        keyboard = [
            [
                InlineKeyboardButton("Price Above", callback_data="alert_condition_above"),
                InlineKeyboardButton("Price Below", callback_data="alert_condition_below")
            ],
            [InlineKeyboardButton("Cancel", callback_data="alert_condition_cancel")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_timeframe_keyboard() -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for selecting a timeframe.
        
        Returns:
            InlineKeyboardMarkup: Timeframe keyboard
        """
        keyboard = [
            [
                InlineKeyboardButton("1m", callback_data="timeframe_1m"),
                InlineKeyboardButton("5m", callback_data="timeframe_5m"),
                InlineKeyboardButton("15m", callback_data="timeframe_15m")
            ],
            [
                InlineKeyboardButton("1h", callback_data="timeframe_1h"),
                InlineKeyboardButton("4h", callback_data="timeframe_4h"),
                InlineKeyboardButton("1d", callback_data="timeframe_1d")
            ],
            [InlineKeyboardButton("Cancel", callback_data="timeframe_cancel")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_leverage_keyboard() -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for selecting leverage.
        
        Returns:
            InlineKeyboardMarkup: Leverage keyboard
        """
        keyboard = [
            [
                InlineKeyboardButton("1x", callback_data="leverage_1"),
                InlineKeyboardButton("2x", callback_data="leverage_2"),
                InlineKeyboardButton("5x", callback_data="leverage_5")
            ],
            [
                InlineKeyboardButton("10x", callback_data="leverage_10"),
                InlineKeyboardButton("20x", callback_data="leverage_20"),
                InlineKeyboardButton("50x", callback_data="leverage_50")
            ],
            [
                InlineKeyboardButton("100x", callback_data="leverage_100"),
                InlineKeyboardButton("Cancel", callback_data="leverage_cancel")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_strategy_type_keyboard() -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for selecting a strategy type.
        
        Returns:
            InlineKeyboardMarkup: Strategy type keyboard
        """
        keyboard = [
            [
                InlineKeyboardButton("SMA Crossover", callback_data="strategy_type_sma_crossover"),
                InlineKeyboardButton("EMA Crossover", callback_data="strategy_type_ema_crossover")
            ],
            [
                InlineKeyboardButton("RSI", callback_data="strategy_type_rsi"),
                InlineKeyboardButton("Bollinger Bands", callback_data="strategy_type_bollinger_bands")
            ],
            [InlineKeyboardButton("Cancel", callback_data="strategy_type_cancel")]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_pagination_keyboard(current_page: int, total_pages: int, 
                                 base_callback: str) -> InlineKeyboardMarkup:
        """
        Create a pagination keyboard for navigating through multiple pages.
        
        Args:
            current_page (int): Current page number
            total_pages (int): Total number of pages
            base_callback (str): Base callback data string
            
        Returns:
            InlineKeyboardMarkup: Pagination keyboard
        """
        keyboard = []
        
        # Add navigation buttons
        navigation = []
        
        if current_page > 1:
            navigation.append(InlineKeyboardButton(
                "◀️ Previous", callback_data=f"{base_callback}_page_{current_page - 1}"
            ))
        
        if current_page < total_pages:
            navigation.append(InlineKeyboardButton(
                "Next ▶️", callback_data=f"{base_callback}_page_{current_page + 1}"
            ))
        
        if navigation:
            keyboard.append(navigation)
        
        # Add page indicator
        keyboard.append([
            InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="pagination_info")
        ])
        
        # Add close button
        keyboard.append([
            InlineKeyboardButton("Close", callback_data=f"{base_callback}_close")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def create_alert_list_keyboard(alerts: List[Dict[str, Any]], 
                                 page: int = 1, 
                                 alerts_per_page: int = 5) -> InlineKeyboardMarkup:
        """
        Create an inline keyboard for displaying and managing alerts.
        
        Args:
            alerts (List[Dict[str, Any]]): List of alerts
            page (int): Current page number
            alerts_per_page (int): Number of alerts to display per page
            
        Returns:
            InlineKeyboardMarkup: Alert list keyboard
        """
        keyboard = []
        
        # Calculate pagination
        total_alerts = len(alerts)
        total_pages = (total_alerts + alerts_per_page - 1) // alerts_per_page
        start_idx = (page - 1) * alerts_per_page
        end_idx = min(start_idx + alerts_per_page, total_alerts)
        
        # Add alert buttons
        for i in range(start_idx, end_idx):
            alert = alerts[i]
            alert_id = alert.get('alert_id', '')
            symbol = alert.get('symbol', '')
            condition = alert.get('condition', '')
            price = alert.get('target_price', 0)
            
            button_text = f"{symbol}: {condition} {price}"
            keyboard.append([
                InlineKeyboardButton(
                    button_text, 
                    callback_data=f"alert_view_{alert_id}"
                ),
                InlineKeyboardButton(
                    "❌", 
                    callback_data=f"alert_delete_{alert_id}"
                )
            ])
        
        # Add pagination buttons
        pagination = []
        
        if page > 1:
            pagination.append(InlineKeyboardButton(
                "◀️ Previous", callback_data=f"alert_list_page_{page - 1}"
            ))
        
        if page < total_pages:
            pagination.append(InlineKeyboardButton(
                "Next ▶️", callback_data=f"alert_list_page_{page + 1}"
            ))
        
        if pagination:
            keyboard.append(pagination)
        
        # Add page indicator and close button
        if total_pages > 0:
            keyboard.append([
                InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="pagination_info")
            ])
        
        keyboard.append([
            InlineKeyboardButton("Close", callback_data="alert_list_close")
        ])
        
        return InlineKeyboardMarkup(keyboard)

