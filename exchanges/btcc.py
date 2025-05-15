
"""
BTCC Exchange API integration.

This module provides functionality for interacting with the BTCC cryptocurrency exchange API.
"""

import time
import hmac
import hashlib
import json
import logging
import urllib.parse
from typing import Dict, List, Optional, Union, Any
import requests

from .base import BaseExchange
from utils.logger import setup_logger

class BTCCExchange(BaseExchange):
    """
    BTCC Exchange API client implementation.
    
    This class provides methods for interacting with the BTCC API for trading
    and accessing market data.
    """
    
    BASE_URL = "https://api.btcc.com"
    
    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the BTCC API client.
        
        Args:
            api_key (str): BTCC API key
            api_secret (str): BTCC API secret
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(api_key, api_secret, logger or setup_logger("btcc_exchange"))
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CryptoTradingTelegramBot/1.0'
        })
    
    def _generate_signature(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, str]:
        """
        Generate HMAC signature for API request authentication.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            
        Returns:
            Dict[str, str]: Headers with authentication information
        """
        timestamp = str(int(time.time() * 1000))
        
        # Create the string to sign
        query_string = ""
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            
        body_string = ""
        if data:
            body_string = json.dumps(data)
        
        message = f"{timestamp}{method.upper()}{endpoint}"
        if query_string:
            message += f"?{query_string}"
        if body_string:
            message += body_string
            
        # Create signature using HMAC-SHA256
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Return headers with authentication
        return {
            'BTCC-API-KEY': self.api_key,
            'BTCC-API-TIMESTAMP': timestamp,
            'BTCC-API-SIGNATURE': signature
        }
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, 
                 auth: bool = False) -> Dict:
        """
        Send request to BTCC API.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            auth (bool): Whether authentication is required
            
        Returns:
            Dict: API response
            
        Raises:
            Exception: If API request fails
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}
        
        if auth:
            headers.update(self._generate_signature(method, endpoint, params, data))
        
        try:
            self.logger.debug(f"Sending {method} request to {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response: {e.response.text}")
            raise
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price ticker for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            
        Returns:
            Dict[str, Any]: Ticker data including price information
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = f"/v1/market/ticker/{formatted_symbol}"
        response = self._request('GET', endpoint)
        
        self.logger.info(f"Retrieved ticker for {symbol}")
        return response
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance for all assets.
        
        Returns:
            Dict[str, float]: Dictionary mapping asset symbols to their balances
        """
        endpoint = "/v1/account/balance"
        response = self._request('GET', endpoint, auth=True)
        
        # Process the response to extract balances
        balances = {}
        for asset in response.get('data', []):
            balances[asset['currency']] = float(asset['available'])
        
        self.logger.info("Retrieved account balances")
        return balances
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            limit (int): Maximum number of orders to retrieve
            
        Returns:
            Dict[str, Any]: Order book data with bids and asks
        """
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = f"/v1/market/depth/{formatted_symbol}"
        params = {'limit': limit}
        response = self._request('GET', endpoint, params=params)
        
        self.logger.info(f"Retrieved order book for {symbol} with limit {limit}")
        return response
    
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
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'market',
            'quantity': str(amount)
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed market {side} order for {amount} {symbol}")
        return response
    
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
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'limit',
            'quantity': str(amount),
            'price': str(price)
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed limit {side} order for {amount} {symbol} at price {price}")
        return response
    
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id (str): ID of the order to cancel
            symbol (Optional[str]): Trading pair symbol (required for BTCC)
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        if not symbol:
            raise ValueError("Symbol is required for canceling orders on BTCC")
        
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/order/cancel"
        data = {
            'symbol': formatted_symbol,
            'orderId': order_id
        }
        
        try:
            response = self._request('POST', endpoint, data=data, auth=True)
            self.logger.info(f"Cancelled order {order_id} for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of an order.
        
        Args:
            order_id (str): ID of the order
            symbol (Optional[str]): Trading pair symbol (required for BTCC)
            
        Returns:
            Dict[str, Any]: Order status and details
        """
        if not symbol:
            raise ValueError("Symbol is required for getting order status on BTCC")
        
        # Format symbol for BTCC (replace / with _)
        formatted_symbol = symbol.replace('/', '_')
        
        endpoint = "/v1/order/status"
        params = {
            'symbol': formatted_symbol,
            'orderId': order_id
        }
        
        response = self._request('GET', endpoint, params=params, auth=True)
        
        self.logger.info(f"Retrieved status for order {order_id}")
        return response
# === Convenience wrapper for Telegram bot ===

def quick_buy_btc(btcc_exchange: BTCCExchange, amount: float = 0.0005) -> Dict[str, Any]:
    """
    Places a quick market buy order for BTC/USDT.

    Args:
        btcc_exchange (BTCCExchange): An instance of the BTCCExchange client
        amount (float): Amount of BTC to buy (default: 0.0005 BTC)

    Returns:
        Dict[str, Any]: API response from BTCC
    """
    try:
        result = btcc_exchange.place_market_order("BTC/USDT", "buy", amount)
        return result
    except Exception as e:
        return {"error": str(e)}
