
"""
Base exchange class that defines the interface for all exchange implementations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any

class BaseExchange(ABC):
    """
    Abstract base class for cryptocurrency exchange implementations.
    
    All exchange-specific implementations should inherit from this class
    and implement its abstract methods.
    """
    
    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the exchange with API credentials.
        
        Args:
            api_key (str): The API key for the exchange
            api_secret (str): The API secret for the exchange
            logger (Optional[logging.Logger]): Logger instance
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price ticker for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Ticker data including price information
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance for all assets.
        
        Returns:
            Dict[str, float]: Dictionary mapping asset symbols to their balances
        """
        pass
    
    @abstractmethod
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            limit (int): Maximum number of orders to retrieve
            
        Returns:
            Dict[str, Any]: Order book data with bids and asks
        """
        pass
    
    @abstractmethod
    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in base currency
            
        Returns:
            Dict[str, Any]: Order details
        """
        pass
    
    @abstractmethod
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in base currency
            price (float): Limit price
            
        Returns:
            Dict[str, Any]: Order details
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id (str): ID of the order to cancel
            symbol (Optional[str]): Trading pair symbol (may be required by some exchanges)
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of an order.
        
        Args:
            order_id (str): ID of the order
            symbol (Optional[str]): Trading pair symbol (may be required by some exchanges)
            
        Returns:
            Dict[str, Any]: Order status and details
        """
        pass
