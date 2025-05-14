
"""
BTCC Futures Trading API integration.

This module provides functionality for interacting with the BTCC cryptocurrency
exchange API for futures trading.
"""

import time
import hmac
import hashlib
import json
import logging
import urllib.parse
from typing import Dict, List, Optional, Union, Any
import requests

from exchanges.btcc import BTCCExchange
from utils.logger import setup_logger

class BTCCFuturesExchange(BTCCExchange):
    """
    BTCC Futures Exchange API client implementation.
    
    This class extends the BTCCExchange class to provide methods for
    interacting with the BTCC Futures API for trading and accessing market data.
    """
    
    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the BTCC Futures API client.
        
        Args:
            api_key (str): BTCC API key
            api_secret (str): BTCC API secret
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(api_key, api_secret, logger or setup_logger("btcc_futures_exchange"))
    
    def get_futures_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current futures positions.
        
        Args:
            symbol (Optional[str]): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Current futures positions
        """
        endpoint = "/v1/futures/positions"
        params = {}
        
        if symbol:
            # Format symbol for BTCC (replace / with _)
            formatted_symbol = symbol.replace('/', '_')
            params['symbol'] = formatted_symbol
        
        response = self._request('GET', endpoint, params=params, auth=True)
        
        self.logger.info(f"Retrieved futures positions for {symbol if symbol else 'all symbols'}")
        return response
    
    def get_futures_leverage(self, symbol: str) -> Dict[str, Any]:
        """
        Get current leverage for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Current leverage information
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = f"/v1/futures/leverage/{formatted_symbol}"
        response = self._request('GET', endpoint, auth=True)
        
        self.logger.info(f"Retrieved futures leverage for {symbol}")
        return response
    
    def set_futures_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        Set leverage for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            leverage (int): Leverage value (e.g., 1, 2, 5, 10, 20, etc.)
            
        Returns:
            Dict[str, Any]: Updated leverage information
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/leverage"
        data = {
            'symbol': formatted_symbol,
            'leverage': leverage
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Set futures leverage for {symbol} to {leverage}x")
        return response
    
    def place_futures_market_order(self, symbol: str, side: str, amount: float, 
                                  reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a futures market order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in contracts
            reduce_only (bool): Whether the order should only reduce position
            
        Returns:
            Dict[str, Any]: Order details
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'market',
            'quantity': str(amount),
            'reduceOnly': reduce_only
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed futures market {side} order for {amount} contracts of {symbol}")
        return response
    
    def place_futures_limit_order(self, symbol: str, side: str, amount: float, price: float,
                                 reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a futures limit order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in contracts
            price (float): Limit price
            reduce_only (bool): Whether the order should only reduce position
            
        Returns:
            Dict[str, Any]: Order details
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'limit',
            'quantity': str(amount),
            'price': str(price),
            'reduceOnly': reduce_only
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed futures limit {side} order for {amount} contracts of {symbol} at price {price}")
        return response
    
    def place_futures_stop_order(self, symbol: str, side: str, amount: float, 
                               stop_price: float, reduce_only: bool = False) -> Dict[str, Any]:
        """
        Place a futures stop market order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in contracts
            stop_price (float): Stop price to trigger the order
            reduce_only (bool): Whether the order should only reduce position
            
        Returns:
            Dict[str, Any]: Order details
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'stop_market',
            'quantity': str(amount),
            'stopPrice': str(stop_price),
            'reduceOnly': reduce_only
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed futures stop {side} order for {amount} contracts of {symbol} at stop price {stop_price}")
        return response
    
    def place_futures_take_profit_order(self, symbol: str, side: str, amount: float, 
                                      take_profit_price: float, reduce_only: bool = True) -> Dict[str, Any]:
        """
        Place a futures take profit market order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in contracts
            take_profit_price (float): Take profit price to trigger the order
            reduce_only (bool): Whether the order should only reduce position
            
        Returns:
            Dict[str, Any]: Order details
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'take_profit_market',
            'quantity': str(amount),
            'stopPrice': str(take_profit_price),
            'reduceOnly': reduce_only
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed futures take profit {side} order for {amount} contracts of {symbol} at price {take_profit_price}")
        return response
    
    def cancel_futures_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel a futures order.
        
        Args:
            order_id (str): ID of the order to cancel
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/order/cancel"
        data = {
            'symbol': formatted_symbol,
            'orderId': order_id
        }
        
        try:
            response = self._request('POST', endpoint, data=data, auth=True)
            self.logger.info(f"Cancelled futures order {order_id} for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel futures order {order_id}: {str(e)}")
            return False
    
    def get_futures_order_status(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Get status of a futures order.
        
        Args:
            order_id (str): ID of the order
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Order status and details
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/futures/order/status"
        params = {
            'symbol': formatted_symbol,
            'orderId': order_id
        }
        
        response = self._request('GET', endpoint, params=params, auth=True)
        
        self.logger.info(f"Retrieved status for futures order {order_id}")
        return response
    
    def get_futures_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all open futures orders.
        
        Args:
            symbol (Optional[str]): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Open orders
        """
        endpoint = "/v1/futures/orders/open"
        params = {}
        
        if symbol:
            # Format symbol for BTCC (replace / with _)
            formatted_symbol = symbol.replace('/', '_')
            params['symbol'] = formatted_symbol
        
        response = self._request('GET', endpoint, params=params, auth=True)
        
        self.logger.info(f"Retrieved open futures orders for {symbol if symbol else 'all symbols'}")
        return response
    
    def get_futures_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Get current funding rate for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Current funding rate information
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = f"/v1/futures/funding/{formatted_symbol}"
        response = self._request('GET', endpoint)
        
        self.logger.info(f"Retrieved funding rate for {symbol}")
        return response
    
    def close_futures_position(self, symbol: str) -> Dict[str, Any]:
        """
        Close an open futures position.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Result of the position closure
        """
        # First, get the current position
        positions = self.get_futures_positions(symbol)
        
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        # Find the position for the specified symbol
        position = None
        for pos in positions.get('data', []):
            if pos.get('symbol') == formatted_symbol:
                position = pos
                break
        
        if not position or float(position.get('size', 0)) == 0:
            self.logger.warning(f"No open position found for {symbol}")
            return {'success': False, 'message': 'No open position found'}
        
        # Determine the side and amount for closing the position
        position_size = float(position.get('size', 0))
        position_side = position.get('side', '').lower()
        
        if position_side == 'long':
            close_side = 'sell'
        elif position_side == 'short':
            close_side = 'buy'
        else:
            self.logger.warning(f"Unknown position side: {position_side}")
            return {'success': False, 'message': f'Unknown position side: {position_side}'}
        
        # Place a market order to close the position
        result = self.place_futures_market_order(
            symbol=symbol,
            side=close_side,
            amount=abs(position_size),
            reduce_only=True
        )
        
        self.logger.info(f"Closed futures position for {symbol}")
        return result

