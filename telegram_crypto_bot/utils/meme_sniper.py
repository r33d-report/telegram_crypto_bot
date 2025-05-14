
"""
Meme Coin Sniping Module for Crypto Trading Telegram Bot.

This module provides functionality for monitoring and sniping new meme coin listings
and tokens with sudden price/volume increases.
"""

import time
import threading
import logging
import json
import re
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime, timedelta
import requests

from utils.logger import setup_logger

class MemeToken:
    """
    Represents a meme token with its metadata and price information.
    """
    
    def __init__(self, token_id: str, symbol: str, name: str, 
                 address: Optional[str] = None, chain: Optional[str] = None,
                 price: Optional[float] = None, market_cap: Optional[float] = None,
                 volume_24h: Optional[float] = None, price_change_24h: Optional[float] = None,
                 created_at: Optional[datetime] = None):
        """
        Initialize a meme token.
        
        Args:
            token_id (str): Unique identifier for the token
            symbol (str): Token symbol (e.g., 'DOGE')
            name (str): Token name (e.g., 'Dogecoin')
            address (Optional[str]): Token contract address
            chain (Optional[str]): Blockchain (e.g., 'ethereum', 'bsc')
            price (Optional[float]): Current price in USD
            market_cap (Optional[float]): Market capitalization in USD
            volume_24h (Optional[float]): 24-hour trading volume in USD
            price_change_24h (Optional[float]): 24-hour price change percentage
            created_at (Optional[datetime]): Token creation timestamp
        """
        self.token_id = token_id
        self.symbol = symbol
        self.name = name
        self.address = address
        self.chain = chain
        self.price = price
        self.market_cap = market_cap
        self.volume_24h = volume_24h
        self.price_change_24h = price_change_24h
        self.created_at = created_at or datetime.now()
        self.last_updated = datetime.now()
        self.price_history: List[Dict[str, Any]] = []
        self.volume_history: List[Dict[str, Any]] = []
    
    def update_price(self, price: float, market_cap: Optional[float] = None,
                    volume_24h: Optional[float] = None, price_change_24h: Optional[float] = None) -> None:
        """
        Update the token's price information.
        
        Args:
            price (float): Current price in USD
            market_cap (Optional[float]): Market capitalization in USD
            volume_24h (Optional[float]): 24-hour trading volume in USD
            price_change_24h (Optional[float]): 24-hour price change percentage
        """
        timestamp = datetime.now()
        
        # Add to price history
        self.price_history.append({
            'timestamp': timestamp,
            'price': price,
            'price_change_24h': price_change_24h
        })
        
        # Keep only the last 100 price points
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        # Add to volume history if volume is provided
        if volume_24h is not None:
            self.volume_history.append({
                'timestamp': timestamp,
                'volume': volume_24h
            })
            
            # Keep only the last 100 volume points
            if len(self.volume_history) > 100:
                self.volume_history = self.volume_history[-100:]
        
        # Update current values
        self.price = price
        if market_cap is not None:
            self.market_cap = market_cap
        if volume_24h is not None:
            self.volume_24h = volume_24h
        if price_change_24h is not None:
            self.price_change_24h = price_change_24h
        
        self.last_updated = timestamp
    
    def calculate_price_change(self, minutes: int = 5) -> Optional[float]:
        """
        Calculate price change over the specified time period.
        
        Args:
            minutes (int): Time period in minutes
            
        Returns:
            Optional[float]: Price change percentage, or None if not enough data
        """
        if not self.price_history or len(self.price_history) < 2:
            return None
        
        # Get current price
        current_price = self.price
        
        # Find price from 'minutes' ago
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        historical_prices = [p for p in self.price_history if p['timestamp'] < cutoff_time]
        
        if not historical_prices:
            return None
        
        # Get the most recent price before the cutoff
        historical_price = historical_prices[-1]['price']
        
        # Calculate percentage change
        if historical_price == 0:
            return None
        
        return ((current_price - historical_price) / historical_price) * 100
    
    def calculate_volume_change(self, minutes: int = 5) -> Optional[float]:
        """
        Calculate volume change over the specified time period.
        
        Args:
            minutes (int): Time period in minutes
            
        Returns:
            Optional[float]: Volume change percentage, or None if not enough data
        """
        if not self.volume_history or len(self.volume_history) < 2:
            return None
        
        # Get current volume
        current_volume = self.volume_24h
        
        # Find volume from 'minutes' ago
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        historical_volumes = [v for v in self.volume_history if v['timestamp'] < cutoff_time]
        
        if not historical_volumes:
            return None
        
        # Get the most recent volume before the cutoff
        historical_volume = historical_volumes[-1]['volume']
        
        # Calculate percentage change
        if historical_volume == 0:
            return None
        
        return ((current_volume - historical_volume) / historical_volume) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the token to a dictionary for storage.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the token
        """
        return {
            'token_id': self.token_id,
            'symbol': self.symbol,
            'name': self.name,
            'address': self.address,
            'chain': self.chain,
            'price': self.price,
            'market_cap': self.market_cap,
            'volume_24h': self.volume_24h,
            'price_change_24h': self.price_change_24h,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'price_history': [
                {
                    'timestamp': p['timestamp'].isoformat(),
                    'price': p['price'],
                    'price_change_24h': p.get('price_change_24h')
                }
                for p in self.price_history
            ],
            'volume_history': [
                {
                    'timestamp': v['timestamp'].isoformat(),
                    'volume': v['volume']
                }
                for v in self.volume_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemeToken':
        """
        Create a MemeToken instance from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of the token
            
        Returns:
            MemeToken: New MemeToken instance
        """
        token = cls(
            token_id=data['token_id'],
            symbol=data['symbol'],
            name=data['name'],
            address=data.get('address'),
            chain=data.get('chain'),
            price=data.get('price'),
            market_cap=data.get('market_cap'),
            volume_24h=data.get('volume_24h'),
            price_change_24h=data.get('price_change_24h'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )
        
        token.last_updated = datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now()
        
        # Load price history
        token.price_history = [
            {
                'timestamp': datetime.fromisoformat(p['timestamp']),
                'price': p['price'],
                'price_change_24h': p.get('price_change_24h')
            }
            for p in data.get('price_history', [])
        ]
        
        # Load volume history
        token.volume_history = [
            {
                'timestamp': datetime.fromisoformat(v['timestamp']),
                'volume': v['volume']
            }
            for v in data.get('volume_history', [])
        ]
        
        return token


class MemeSniperAlert:
    """
    Represents an alert for meme coin sniping.
    """
    
    def __init__(self, user_id: int, alert_id: Optional[str] = None,
                 min_price_change: Optional[float] = None,
                 min_volume_change: Optional[float] = None,
                 max_market_cap: Optional[float] = None,
                 chains: Optional[List[str]] = None,
                 keywords: Optional[List[str]] = None,
                 exclude_keywords: Optional[List[str]] = None,
                 auto_buy: bool = False,
                 auto_buy_amount: Optional[float] = None):
        """
        Initialize a meme sniper alert.
        
        Args:
            user_id (int): Telegram user ID who set the alert
            alert_id (Optional[str]): Unique identifier for the alert
            min_price_change (Optional[float]): Minimum price change percentage to trigger
            min_volume_change (Optional[float]): Minimum volume change percentage to trigger
            max_market_cap (Optional[float]): Maximum market cap for tokens to consider
            chains (Optional[List[str]]): List of blockchains to monitor
            keywords (Optional[List[str]]): Keywords to match in token name/symbol
            exclude_keywords (Optional[List[str]]): Keywords to exclude from token name/symbol
            auto_buy (bool): Whether to automatically buy when triggered
            auto_buy_amount (Optional[float]): Amount to buy in USD
        """
        self.user_id = user_id
        self.alert_id = alert_id or f"meme_sniper_{user_id}_{int(time.time())}"
        self.min_price_change = min_price_change
        self.min_volume_change = min_volume_change
        self.max_market_cap = max_market_cap
        self.chains = chains or ['ethereum', 'bsc']
        self.keywords = keywords or []
        self.exclude_keywords = exclude_keywords or []
        self.auto_buy = auto_buy
        self.auto_buy_amount = auto_buy_amount
        self.created_at = datetime.now()
        self.triggered_tokens: List[str] = []
    
    def matches_token(self, token: MemeToken) -> bool:
        """
        Check if a token matches the alert criteria.
        
        Args:
            token (MemeToken): Token to check
            
        Returns:
            bool: True if the token matches the criteria, False otherwise
        """
        # Check if token has already triggered this alert
        if token.token_id in self.triggered_tokens:
            return False
        
        # Check chain
        if self.chains and token.chain and token.chain.lower() not in [c.lower() for c in self.chains]:
            return False
        
        # Check market cap
        if self.max_market_cap is not None and token.market_cap is not None:
            if token.market_cap > self.max_market_cap:
                return False
        
        # Check keywords
        if self.keywords:
            token_text = f"{token.name} {token.symbol}".lower()
            if not any(keyword.lower() in token_text for keyword in self.keywords):
                return False
        
        # Check excluded keywords
        if self.exclude_keywords:
            token_text = f"{token.name} {token.symbol}".lower()
            if any(keyword.lower() in token_text for keyword in self.exclude_keywords):
                return False
        
        # Check price change
        if self.min_price_change is not None:
            price_change_5m = token.calculate_price_change(minutes=5)
            if price_change_5m is None or price_change_5m < self.min_price_change:
                return False
        
        # Check volume change
        if self.min_volume_change is not None:
            volume_change_5m = token.calculate_volume_change(minutes=5)
            if volume_change_5m is None or volume_change_5m < self.min_volume_change:
                return False
        
        return True
    
    def mark_token_triggered(self, token_id: str) -> None:
        """
        Mark a token as having triggered this alert.
        
        Args:
            token_id (str): ID of the token that triggered the alert
        """
        if token_id not in self.triggered_tokens:
            self.triggered_tokens.append(token_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the alert to a dictionary for storage.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the alert
        """
        return {
            'alert_id': self.alert_id,
            'user_id': self.user_id,
            'min_price_change': self.min_price_change,
            'min_volume_change': self.min_volume_change,
            'max_market_cap': self.max_market_cap,
            'chains': self.chains,
            'keywords': self.keywords,
            'exclude_keywords': self.exclude_keywords,
            'auto_buy': self.auto_buy,
            'auto_buy_amount': self.auto_buy_amount,
            'created_at': self.created_at.isoformat(),
            'triggered_tokens': self.triggered_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemeSniperAlert':
        """
        Create a MemeSniperAlert instance from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of the alert
            
        Returns:
            MemeSniperAlert: New MemeSniperAlert instance
        """
        alert = cls(
            user_id=data['user_id'],
            alert_id=data['alert_id'],
            min_price_change=data.get('min_price_change'),
            min_volume_change=data.get('min_volume_change'),
            max_market_cap=data.get('max_market_cap'),
            chains=data.get('chains'),
            keywords=data.get('keywords'),
            exclude_keywords=data.get('exclude_keywords'),
            auto_buy=data.get('auto_buy', False),
            auto_buy_amount=data.get('auto_buy_amount')
        )
        
        alert.created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        alert.triggered_tokens = data.get('triggered_tokens', [])
        
        return alert


class MemeSniper:
    """
    Meme coin sniping system for monitoring and trading new tokens.
    """
    
    def __init__(self, notification_callback: Callable, buy_callback: Callable,
                 check_interval: int = 60, logger: Optional[logging.Logger] = None):
        """
        Initialize the meme sniper.
        
        Args:
            notification_callback (Callable): Function to call when an alert is triggered
            buy_callback (Callable): Function to call for auto-buying tokens
            check_interval (int): Interval in seconds to check for new tokens
            logger (Optional[logging.Logger]): Logger instance
        """
        self.tokens: Dict[str, MemeToken] = {}
        self.alerts: Dict[str, MemeSniperAlert] = {}
        self.notification_callback = notification_callback
        self.buy_callback = buy_callback
        self.check_interval = check_interval
        self.logger = logger or setup_logger("meme_sniper")
        self.running = False
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        # API endpoints for token data
        self.api_endpoints = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'dextools': 'https://api.dextools.io/v1',
            'dexscreener': 'https://api.dexscreener.com/latest'
        }
    
    def add_alert(self, alert: MemeSniperAlert) -> bool:
        """
        Add a new meme sniper alert.
        
        Args:
            alert (MemeSniperAlert): Alert to add
            
        Returns:
            bool: True if alert was added successfully, False otherwise
        """
        with self.lock:
            self.alerts[alert.alert_id] = alert
            self.logger.info(f"Added meme sniper alert {alert.alert_id} for user {alert.user_id}")
            return True
    
    def remove_alert(self, alert_id: str) -> bool:
        """
        Remove a meme sniper alert.
        
        Args:
            alert_id (str): ID of the alert to remove
            
        Returns:
            bool: True if alert was removed successfully, False otherwise
        """
        with self.lock:
            if alert_id in self.alerts:
                del self.alerts[alert_id]
                self.logger.info(f"Removed meme sniper alert {alert_id}")
                return True
            return False
    
    def get_alerts_for_user(self, user_id: int) -> List[MemeSniperAlert]:
        """
        Get all alerts for a specific user.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            List[MemeSniperAlert]: List of alerts for the user
        """
        with self.lock:
            return [alert for alert in self.alerts.values() if alert.user_id == user_id]
    
    def get_alert(self, alert_id: str) -> Optional[MemeSniperAlert]:
        """
        Get a specific alert by ID.
        
        Args:
            alert_id (str): Alert ID
            
        Returns:
            Optional[MemeSniperAlert]: Alert if found, None otherwise
        """
        with self.lock:
            return self.alerts.get(alert_id)
    
    def start_monitoring(self) -> None:
        """
        Start the token monitoring thread.
        """
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_tokens, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Meme token monitoring started")
    
    def stop_monitoring(self) -> None:
        """
        Stop the token monitoring thread.
        """
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None
        self.logger.info("Meme token monitoring stopped")
    
    def _monitor_tokens(self) -> None:
        """
        Monitor tokens and trigger alerts when conditions are met.
        This method runs in a separate thread.
        """
        while self.running:
            try:
                self._update_token_data()
                self._check_alerts()
            except Exception as e:
                self.logger.error(f"Error monitoring tokens: {str(e)}")
            
            # Sleep for the check interval
            time.sleep(self.check_interval)
    
    def _update_token_data(self) -> None:
        """
        Update token data from various sources.
        """
        try:
            # Get new token listings
            new_tokens = self._fetch_new_listings()
            
            # Update existing tokens
            self._update_existing_tokens()
            
            # Add new tokens
            for token_data in new_tokens:
                token_id = token_data.get('id') or token_data.get('token_id')
                if not token_id:
                    continue
                
                with self.lock:
                    if token_id not in self.tokens:
                        token = MemeToken(
                            token_id=token_id,
                            symbol=token_data.get('symbol', ''),
                            name=token_data.get('name', ''),
                            address=token_data.get('address'),
                            chain=token_data.get('chain') or token_data.get('platform'),
                            price=token_data.get('price') or token_data.get('current_price'),
                            market_cap=token_data.get('market_cap'),
                            volume_24h=token_data.get('volume_24h') or token_data.get('total_volume'),
                            price_change_24h=token_data.get('price_change_24h_percentage'),
                            created_at=datetime.now()
                        )
                        self.tokens[token_id] = token
                        self.logger.info(f"Added new token: {token.name} ({token.symbol})")
            
        except Exception as e:
            self.logger.error(f"Error updating token data: {str(e)}")
    
    def _fetch_new_listings(self) -> List[Dict[str, Any]]:
        """
        Fetch new token listings from various sources.
        
        Returns:
            List[Dict[str, Any]]: List of new token data
        """
        new_tokens = []
        
        try:
            # CoinGecko - New coins
            url = f"{self.api_endpoints['coingecko']}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'created_desc',
                'per_page': 50,
                'page': 1,
                'sparkline': 'false',
                'category': 'meme-token'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                new_tokens.extend(data)
                
        except Exception as e:
            self.logger.error(f"Error fetching new listings from CoinGecko: {str(e)}")
        
        # Add more sources here as needed
        
        return new_tokens
    
    def _update_existing_tokens(self) -> None:
        """
        Update data for existing tokens.
        """
        with self.lock:
            token_ids = list(self.tokens.keys())
        
        if not token_ids:
            return
        
        try:
            # Update in batches of 50 tokens
            batch_size = 50
            for i in range(0, len(token_ids), batch_size):
                batch_ids = token_ids[i:i+batch_size]
                
                # CoinGecko - Update prices
                ids_param = ','.join(batch_ids)
                url = f"{self.api_endpoints['coingecko']}/coins/markets"
                params = {
                    'vs_currency': 'usd',
                    'ids': ids_param,
                    'order': 'market_cap_desc',
                    'per_page': batch_size,
                    'page': 1,
                    'sparkline': 'false'
                }
                
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    with self.lock:
                        for token_data in data:
                            token_id = token_data.get('id')
                            if token_id in self.tokens:
                                token = self.tokens[token_id]
                                token.update_price(
                                    price=token_data.get('current_price', 0),
                                    market_cap=token_data.get('market_cap'),
                                    volume_24h=token_data.get('total_volume'),
                                    price_change_24h=token_data.get('price_change_percentage_24h')
                                )
                
        except Exception as e:
            self.logger.error(f"Error updating existing tokens: {str(e)}")
    
    def _check_alerts(self) -> None:
        """
        Check all alerts against current token data.
        """
        triggered_alerts = []
        
        with self.lock:
            for alert_id, alert in self.alerts.items():
                for token_id, token in self.tokens.items():
                    if alert.matches_token(token):
                        triggered_alerts.append((alert, token))
                        alert.mark_token_triggered(token_id)
        
        # Process triggered alerts
        for alert, token in triggered_alerts:
            self.logger.info(f"Alert {alert.alert_id} triggered for token {token.name} ({token.symbol})")
            
            # Call notification callback
            self.notification_callback(alert, token)
            
            # Handle auto-buy if enabled
            if alert.auto_buy and alert.auto_buy_amount:
                self.buy_callback(alert, token, alert.auto_buy_amount)
    
    def get_trending_tokens(self, limit: int = 10) -> List[MemeToken]:
        """
        Get trending meme tokens based on price and volume changes.
        
        Args:
            limit (int): Maximum number of tokens to return
            
        Returns:
            List[MemeToken]: List of trending tokens
        """
        with self.lock:
            # Calculate scores based on price and volume changes
            scored_tokens = []
            for token in self.tokens.values():
                price_change_24h = token.price_change_24h or 0
                price_change_1h = token.calculate_price_change(minutes=60) or 0
                volume_change = token.calculate_volume_change(minutes=60) or 0
                
                # Calculate a simple score
                score = price_change_1h * 0.4 + price_change_24h * 0.3 + volume_change * 0.3
                
                scored_tokens.append((token, score))
            
            # Sort by score (descending)
            scored_tokens.sort(key=lambda x: x[1], reverse=True)
            
            # Return top tokens
            return [token for token, _ in scored_tokens[:limit]]
    
    def get_new_listings(self, days: int = 7, limit: int = 10) -> List[MemeToken]:
        """
        Get recently listed tokens.
        
        Args:
            days (int): Maximum age in days
            limit (int): Maximum number of tokens to return
            
        Returns:
            List[MemeToken]: List of new tokens
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.lock:
            # Filter tokens by creation date
            new_tokens = [
                token for token in self.tokens.values()
                if token.created_at >= cutoff_date
            ]
            
            # Sort by creation date (newest first)
            new_tokens.sort(key=lambda x: x.created_at, reverse=True)
            
            # Return top tokens
            return new_tokens[:limit]
    
    def search_tokens(self, query: str, limit: int = 10) -> List[MemeToken]:
        """
        Search for tokens by name or symbol.
        
        Args:
            query (str): Search query
            limit (int): Maximum number of tokens to return
            
        Returns:
            List[MemeToken]: List of matching tokens
        """
        query = query.lower()
        
        with self.lock:
            # Filter tokens by name or symbol
            matching_tokens = [
                token for token in self.tokens.values()
                if query in token.name.lower() or query in token.symbol.lower()
            ]
            
            # Sort by market cap (descending)
            matching_tokens.sort(key=lambda x: x.market_cap or 0, reverse=True)
            
            # Return top tokens
            return matching_tokens[:limit]
    
    def save_data(self, tokens_filepath: str, alerts_filepath: str) -> bool:
        """
        Save tokens and alerts to files.
        
        Args:
            tokens_filepath (str): Path to save tokens
            alerts_filepath (str): Path to save alerts
            
        Returns:
            bool: True if data was saved successfully, False otherwise
        """
        import json
        
        try:
            # Save tokens
            with self.lock:
                tokens_data = {token_id: token.to_dict() for token_id, token in self.tokens.items()}
                alerts_data = {alert_id: alert.to_dict() for alert_id, alert in self.alerts.items()}
            
            with open(tokens_filepath, 'w') as f:
                json.dump(tokens_data, f, indent=2)
            
            with open(alerts_filepath, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.tokens)} tokens and {len(self.alerts)} alerts")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving data: {str(e)}")
            return False
    
    def load_data(self, tokens_filepath: str, alerts_filepath: str) -> bool:
        """
        Load tokens and alerts from files.
        
        Args:
            tokens_filepath (str): Path to load tokens from
            alerts_filepath (str): Path to load alerts from
            
        Returns:
            bool: True if data was loaded successfully, False otherwise
        """
        import json
        import os
        
        success = True
        
        # Load tokens
        if os.path.exists(tokens_filepath):
            try:
                with open(tokens_filepath, 'r') as f:
                    tokens_data = json.load(f)
                
                with self.lock:
                    self.tokens = {token_id: MemeToken.from_dict(data) for token_id, data in tokens_data.items()}
                
                self.logger.info(f"Loaded {len(self.tokens)} tokens")
                
            except Exception as e:
                self.logger.error(f"Error loading tokens: {str(e)}")
                success = False
        
        # Load alerts
        if os.path.exists(alerts_filepath):
            try:
                with open(alerts_filepath, 'r') as f:
                    alerts_data = json.load(f)
                
                with self.lock:
                    self.alerts = {alert_id: MemeSniperAlert.from_dict(data) for alert_id, data in alerts_data.items()}
                
                self.logger.info(f"Loaded {len(self.alerts)} alerts")
                
            except Exception as e:
                self.logger.error(f"Error loading alerts: {str(e)}")
                success = False
        
        return success

