
"""
Price Alert System for Crypto Trading Telegram Bot.

This module provides functionality for setting, managing, and triggering price alerts
for cryptocurrency trading pairs.
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime

from utils.logger import setup_logger
from exchanges.base import BaseExchange

class PriceAlert:
    """
    Represents a single price alert for a cryptocurrency.
    """
    
    def __init__(self, user_id: int, symbol: str, exchange: str, 
                 target_price: float, condition: str, alert_id: Optional[str] = None):
        """
        Initialize a price alert.
        
        Args:
            user_id (int): Telegram user ID who set the alert
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            exchange (str): Exchange name ('btcc' or 'coinbase')
            target_price (float): Target price to trigger the alert
            condition (str): Condition for triggering ('above' or 'below')
            alert_id (Optional[str]): Unique identifier for the alert
        """
        self.user_id = user_id
        self.symbol = symbol
        self.exchange = exchange.lower()
        self.target_price = target_price
        self.condition = condition.lower()
        self.alert_id = alert_id or f"{user_id}_{symbol}_{exchange}_{int(time.time())}"
        self.created_at = datetime.now()
        self.triggered = False
        
    def is_triggered(self, current_price: float) -> bool:
        """
        Check if the alert should be triggered based on the current price.
        
        Args:
            current_price (float): Current price of the cryptocurrency
            
        Returns:
            bool: True if the alert should be triggered, False otherwise
        """
        if self.condition == 'above':
            return current_price >= self.target_price
        elif self.condition == 'below':
            return current_price <= self.target_price
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the alert to a dictionary for storage.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the alert
        """
        return {
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'target_price': self.target_price,
            'condition': self.condition,
            'created_at': self.created_at.isoformat(),
            'triggered': self.triggered
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceAlert':
        """
        Create a PriceAlert instance from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of the alert
            
        Returns:
            PriceAlert: New PriceAlert instance
        """
        alert = cls(
            user_id=data['user_id'],
            symbol=data['symbol'],
            exchange=data['exchange'],
            target_price=data['target_price'],
            condition=data['condition'],
            alert_id=data['alert_id']
        )
        alert.created_at = datetime.fromisoformat(data['created_at'])
        alert.triggered = data.get('triggered', False)
        return alert


class PriceAlertManager:
    """
    Manages price alerts for all users.
    """
    
    def __init__(self, get_exchange_func: Callable, notification_callback: Callable, 
                 check_interval: int = 60, logger: Optional[logging.Logger] = None):
        """
        Initialize the price alert manager.
        
        Args:
            get_exchange_func (Callable): Function to get exchange instance
            notification_callback (Callable): Function to call when alert is triggered
            check_interval (int): Interval in seconds to check prices
            logger (Optional[logging.Logger]): Logger instance
        """
        self.alerts: Dict[str, PriceAlert] = {}
        self.get_exchange = get_exchange_func
        self.notification_callback = notification_callback
        self.check_interval = check_interval
        self.logger = logger or setup_logger("price_alerts")
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
    
    def add_alert(self, alert: PriceAlert) -> bool:
        """
        Add a new price alert.
        
        Args:
            alert (PriceAlert): Alert to add
            
        Returns:
            bool: True if alert was added successfully, False otherwise
        """
        with self.lock:
            self.alerts[alert.alert_id] = alert
            self.logger.info(f"Added price alert {alert.alert_id} for {alert.symbol} on {alert.exchange}")
            return True
    
    def remove_alert(self, alert_id: str) -> bool:
        """
        Remove a price alert.
        
        Args:
            alert_id (str): ID of the alert to remove
            
        Returns:
            bool: True if alert was removed successfully, False otherwise
        """
        with self.lock:
            if alert_id in self.alerts:
                del self.alerts[alert_id]
                self.logger.info(f"Removed price alert {alert_id}")
                return True
            return False
    
    def get_alerts_for_user(self, user_id: int) -> List[PriceAlert]:
        """
        Get all alerts for a specific user.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            List[PriceAlert]: List of alerts for the user
        """
        with self.lock:
            return [alert for alert in self.alerts.values() if alert.user_id == user_id]
    
    def get_alert(self, alert_id: str) -> Optional[PriceAlert]:
        """
        Get a specific alert by ID.
        
        Args:
            alert_id (str): Alert ID
            
        Returns:
            Optional[PriceAlert]: Alert if found, None otherwise
        """
        with self.lock:
            return self.alerts.get(alert_id)
    
    def start_monitoring(self) -> None:
        """
        Start the price monitoring thread.
        """
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_prices, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Price alert monitoring started")
    
    def stop_monitoring(self) -> None:
        """
        Stop the price monitoring thread.
        """
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None
        self.logger.info("Price alert monitoring stopped")
    
    def _monitor_prices(self) -> None:
        """
        Monitor prices and trigger alerts when conditions are met.
        This method runs in a separate thread.
        """
        while self.running:
            try:
                self._check_alerts()
            except Exception as e:
                self.logger.error(f"Error checking price alerts: {str(e)}")
            
            # Sleep for the check interval
            time.sleep(self.check_interval)
    
    def _check_alerts(self) -> None:
        """
        Check all active alerts against current prices.
        """
        # Group alerts by exchange and symbol to minimize API calls
        exchange_symbol_map = {}
        
        with self.lock:
            for alert in self.alerts.values():
                if alert.triggered:
                    continue
                
                key = f"{alert.exchange}_{alert.symbol}"
                if key not in exchange_symbol_map:
                    exchange_symbol_map[key] = []
                exchange_symbol_map[key].append(alert)
        
        # Check each group of alerts
        for key, alerts in exchange_symbol_map.items():
            if not alerts:
                continue
            
            exchange_name, symbol = key.split('_', 1)
            
            try:
                # Get current price from exchange
                exchange = self.get_exchange(exchange_name)
                ticker = exchange.get_ticker(symbol)
                
                # Extract current price based on exchange
                if exchange_name == 'btcc':
                    current_price = float(ticker.get('data', {}).get('last', 0))
                elif exchange_name == 'coinbase':
                    current_price = float(ticker.get('price', 0))
                else:
                    continue
                
                if current_price <= 0:
                    self.logger.warning(f"Invalid price {current_price} for {symbol} on {exchange_name}")
                    continue
                
                # Check each alert in the group
                triggered_alerts = []
                with self.lock:
                    for alert in alerts:
                        if alert.is_triggered(current_price):
                            alert.triggered = True
                            triggered_alerts.append(alert)
                
                # Notify users of triggered alerts
                for alert in triggered_alerts:
                    self.logger.info(f"Alert {alert.alert_id} triggered: {symbol} is {alert.condition} {alert.target_price}")
                    self.notification_callback(alert, current_price)
                
            except Exception as e:
                self.logger.error(f"Error checking price for {symbol} on {exchange_name}: {str(e)}")
    
    def save_alerts(self, filepath: str) -> bool:
        """
        Save all alerts to a file.
        
        Args:
            filepath (str): Path to save the alerts
            
        Returns:
            bool: True if alerts were saved successfully, False otherwise
        """
        import json
        
        try:
            with self.lock:
                alerts_data = {alert_id: alert.to_dict() for alert_id, alert in self.alerts.items()}
            
            with open(filepath, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.alerts)} alerts to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving alerts to {filepath}: {str(e)}")
            return False
    
    def load_alerts(self, filepath: str) -> bool:
        """
        Load alerts from a file.
        
        Args:
            filepath (str): Path to load the alerts from
            
        Returns:
            bool: True if alerts were loaded successfully, False otherwise
        """
        import json
        import os
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Alerts file {filepath} does not exist")
            return False
        
        try:
            with open(filepath, 'r') as f:
                alerts_data = json.load(f)
            
            with self.lock:
                self.alerts = {alert_id: PriceAlert.from_dict(data) for alert_id, data in alerts_data.items()}
            
            self.logger.info(f"Loaded {len(self.alerts)} alerts from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading alerts from {filepath}: {str(e)}")
            return False

