
"""
Coinbase Exchange API integration.

This module provides functionality for interacting with the Coinbase Advanced Trade API.
"""

import time
import hmac
import hashlib
import base64
import json
import logging
from typing import Dict, List, Optional, Union, Any
import requests

from .base import BaseExchange
from utils.logger import setup_logger

class CoinbaseExchange(BaseExchange):
    """
    Coinbase Exchange API client implementation.
    
    This class provides methods for interacting with the Coinbase Advanced Trade API
    for trading and accessing market data.
    """
    
    BASE_URL = "https://api.coinbase.com"
    ADVANCED_TRADE_URL = "https://api.coinbase.com/api/v3/brokerage"
    
    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the Coinbase API client.
        
        Args:
            api_key (str): Coinbase API key
            api_secret (str): Coinbase API secret
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(api_key, api_secret, logger or setup_logger("coinbase_exchange"))
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CryptoTradingTelegramBot/1.0'
        })
    
    def _generate_signature(self, method: str, endpoint: str, timestamp: str, body: str = "") -> Dict[str, str]:
        """
        Generate signature for Coinbase API request authentication.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            timestamp (str): Request timestamp
            body (str, optional): Request body as a string
            
        Returns:
            Dict[str, str]: Headers with authentication information
        """
        # Create the message to sign
        message = f"{timestamp}{method.upper()}{endpoint}{body}"
        
        # Create signature using HMAC-SHA256
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message.encode('utf-8'),
            hashlib.sha256
        )
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
        
        # Return headers with authentication
        return {
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp
        }
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, 
                 auth: bool = False, advanced_trade: bool = True) -> Dict:
        """
        Send request to Coinbase API.
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            auth (bool): Whether authentication is required
            advanced_trade (bool): Whether to use Advanced Trade API
            
        Returns:
            Dict: API response
            
        Raises:
            Exception: If API request fails
        """
        base = self.ADVANCED_TRADE_URL if advanced_trade else self.BASE_URL
        url = f"{base}{endpoint}"
        headers = {}
        
        if auth:
            timestamp = str(int(time.time()))
            body = json.dumps(data) if data else ""
            headers.update(self._generate_signature(method, endpoint, timestamp, body))
        
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
            if hasattr(e, 'response') and e.response:
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
        # Format symbol for Coinbase (replace / with -)
        formatted_symbol = symbol.replace('/', '-')
        
        endpoint = f"/products/{formatted_symbol}/ticker"
        response = self._request('GET', endpoint, advanced_trade=False)
        
        self.logger.info(f"Retrieved ticker for {symbol}")
        return response
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance for all assets.
        
        Returns:
            Dict[str, float]: Dictionary mapping asset symbols to their balances
        """
        endpoint = "/accounts"
        response = self._request('GET', endpoint, auth=True)
        
        # Process the response to extract balances
        balances = {}
        for account in response.get('accounts', []):
            currency = account.get('currency', '')
            available = float(account.get('available_balance', {}).get('value', 0))
            balances[currency] = available
        
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
        # Format symbol for Coinbase (replace / with -)
        formatted_symbol = symbol.replace('/', '-')
        
        endpoint = f"/products/{formatted_symbol}/book"
        params = {'level': 2}  # Level 2 provides top 50 bids and asks
        response = self._request('GET', endpoint, params=params, advanced_trade=False)
        
        # Limit the results to the requested number
        if 'bids' in response:
            response['bids'] = response['bids'][:limit]
        if 'asks' in response:
            response['asks'] = response['asks'][:limit]
        
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
        # Format symbol for Coinbase (replace / with -)
        formatted_symbol = symbol.replace('/', '-')
        
        endpoint = "/orders"
        
        # Generate a client order ID
        client_order_id = f"bot_{int(time.time() * 1000)}"
        
        data = {
            "client_order_id": client_order_id,
            "product_id": formatted_symbol,
            "side": side.lower(),
            "order_configuration": {
                "market_market_ioc": {
                    "base_size": str(amount)
                }
            }
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
        # Format symbol for Coinbase (replace / with -)
        formatted_symbol = symbol.replace('/', '-')
        
        endpoint = "/orders"
        
        # Generate a client order ID
        client_order_id = f"bot_{int(time.time() * 1000)}"
        
        data = {
            "client_order_id": client_order_id,
            "product_id": formatted_symbol,
            "side": side.lower(),
            "order_configuration": {
                "limit_limit_gtc": {
                    "base_size": str(amount),
                    "limit_price": str(price),
                    "post_only": False
                }
            }
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed limit {side} order for {amount} {symbol} at price {price}")
        return response
    
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id (str): ID of the order to cancel
            symbol (Optional[str]): Trading pair symbol (not required for Coinbase)
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        endpoint = "/orders/batch_cancel"
        data = {
            "order_ids": [order_id]
        }
        
        try:
            response = self._request('POST', endpoint, data=data, auth=True)
            
            # Check if the cancellation was successful
            results = response.get('results', [])
            if results and results[0].get('success'):
                self.logger.info(f"Cancelled order {order_id}")
                return True
            else:
                error_msg = results[0].get('error_message', 'Unknown error') if results else 'No results returned'
                self.logger.error(f"Failed to cancel order {order_id}: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status of an order.
        
        Args:
            order_id (str): ID of the order
            symbol (Optional[str]): Trading pair symbol (not required for Coinbase)
            
        Returns:
            Dict[str, Any]: Order status and details
        """
        endpoint = f"/orders/{order_id}"
        response = self._request('GET', endpoint, auth=True)
        
        self.logger.info(f"Retrieved status for order {order_id}")
        return response
