
"""
Photon-SOL Exchange API integration.

This module provides functionality for interacting with the Photon-SOL cryptocurrency exchange API
on the Solana blockchain.
"""

import time
import hmac
import hashlib
import base64
import json
import logging
import urllib.parse
from typing import Dict, List, Optional, Union, Any
import requests

from .base import BaseExchange
from utils.logger import setup_logger

class PhotonSOLExchange(BaseExchange):
    """
    Photon-SOL Exchange API client implementation.
    
    This class provides methods for interacting with the Photon-SOL API for trading
    and accessing market data on the Solana blockchain.
    """
    
    BASE_URL = "https://api.photon-sol.tinyastro.io"
    API_VERSION = "1"
    
    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the Photon-SOL API client.
        
        Args:
            api_key (str): Photon-SOL API key
            api_secret (str): Photon-SOL API secret
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(api_key, api_secret, logger or setup_logger("photon_sol_exchange"))
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CryptoTradingTelegramBot/1.0'
        })
    
    def _generate_signature(self, method: str, endpoint: str, timestamp: str, body: str = "") -> Dict[str, str]:
        """
        Generate signature for Photon-SOL API request authentication.
        
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
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        )
        signature_hex = signature.hexdigest()
        
        # Return headers with authentication
        return {
            'PHOTON-API-KEY': self.api_key,
            'PHOTON-API-TIMESTAMP': timestamp,
            'PHOTON-API-SIGNATURE': signature_hex
        }
    
    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, 
                 auth: bool = False) -> Dict:
        """
        Send request to Photon-SOL API.
        
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
        url = f"{self.BASE_URL}/api/{self.API_VERSION}{endpoint}"
        headers = {}
        
        if auth:
            timestamp = str(int(time.time() * 1000))
            body = json.dumps(data) if data else ""
            headers.update(self._generate_signature(method, endpoint, timestamp, body))
        
        try:
            self.logger.debug(f"Sending {method} request to {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, params=params, json=data, headers=headers)
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
            symbol (str): Trading pair symbol (e.g., 'SOL/USDC')
            
        Returns:
            Dict[str, Any]: Ticker data including price information
        """
        # Format symbol for Photon-SOL (extract token address if needed)
        token_address = symbol
        if '/' in symbol:
            # Extract the base token from the trading pair
            base_token = symbol.split('/')[0]
            # Get token address from the token registry
            tokens = self.list_tokens()
            for token in tokens:
                if token.get('symbol') == base_token:
                    token_address = token.get('address')
                    break
        
        endpoint = f"/tokens/{token_address}/price"
        response = self._request('GET', endpoint)
        
        self.logger.info(f"Retrieved ticker for {symbol}")
        return response
    
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance for all assets.
        
        Returns:
            Dict[str, float]: Dictionary mapping asset symbols to their balances
        """
        endpoint = "/wallet/balance"
        response = self._request('GET', endpoint, auth=True)
        
        # Process the response to extract balances
        balances = {}
        for asset in response.get('balances', []):
            symbol = asset.get('symbol', '')
            available = float(asset.get('available', 0))
            balances[symbol] = available
        
        self.logger.info("Retrieved account balances")
        return balances
    
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Get order book for a symbol.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'SOL/USDC')
            limit (int): Maximum number of orders to retrieve
            
        Returns:
            Dict[str, Any]: Order book data with bids and asks
        """
        # Format symbol for Photon-SOL (extract token address if needed)
        token_address = symbol
        if '/' in symbol:
            # Extract the base token from the trading pair
            base_token = symbol.split('/')[0]
            # Get token address from the token registry
            tokens = self.list_tokens()
            for token in tokens:
                if token.get('symbol') == base_token:
                    token_address = token.get('address')
                    break
        
        endpoint = f"/tokens/{token_address}/orderbook"
        params = {'limit': limit}
        response = self._request('GET', endpoint, params=params)
        
        self.logger.info(f"Retrieved order book for {symbol} with limit {limit}")
        return response
    
    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'SOL/USDC')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in base currency
            
        Returns:
            Dict[str, Any]: Order details
        """
        # Format symbol for Photon-SOL (extract token address if needed)
        token_address = symbol
        if '/' in symbol:
            # Extract the base token from the trading pair
            base_token = symbol.split('/')[0]
            # Get token address from the token registry
            tokens = self.list_tokens()
            for token in tokens:
                if token.get('symbol') == base_token:
                    token_address = token.get('address')
                    break
        
        endpoint = "/transfers"
        
        # For market orders, we use the transfers endpoint with appropriate parameters
        data = {
            'token_address': token_address,
            'amount': str(amount),
            'side': side.lower(),
            'order_type': 'market',
            'slippage': 0.5,  # Default slippage tolerance of 0.5%
            'priority_fee': 'medium'  # Default priority fee
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed market {side} order for {amount} {symbol}")
        return response
    
    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'SOL/USDC')
            side (str): Order side ('buy' or 'sell')
            amount (float): Order amount in base currency
            price (float): Limit price
            
        Returns:
            Dict[str, Any]: Order details
        """
        # Format symbol for Photon-SOL (extract token address if needed)
        token_address = symbol
        if '/' in symbol:
            # Extract the base token from the trading pair
            base_token = symbol.split('/')[0]
            # Get token address from the token registry
            tokens = self.list_tokens()
            for token in tokens:
                if token.get('symbol') == base_token:
                    token_address = token.get('address')
                    break
        
        endpoint = "/transfers"
        
        # For limit orders, we use the transfers endpoint with price parameter
        data = {
            'token_address': token_address,
            'amount': str(amount),
            'side': side.lower(),
            'order_type': 'limit',
            'price': str(price),
            'priority_fee': 'medium'  # Default priority fee
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Placed limit {side} order for {amount} {symbol} at price {price}")
        return response
    
    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id (str): ID of the order to cancel
            symbol (Optional[str]): Trading pair symbol (may be required for some exchanges)
            
        Returns:
            bool: True if cancellation was successful, False otherwise
        """
        endpoint = f"/transfers/{order_id}/cancel"
        
        try:
            response = self._request('POST', endpoint, auth=True)
            
            # Check if the cancellation was successful
            success = response.get('success', False)
            
            if success:
                self.logger.info(f"Cancelled order {order_id}")
                return True
            else:
                error_msg = response.get('error', 'Unknown error')
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
            symbol (Optional[str]): Trading pair symbol (not required for Photon-SOL)
            
        Returns:
            Dict[str, Any]: Order status and details
        """
        endpoint = f"/transferstatus/{order_id}"
        response = self._request('GET', endpoint, auth=True)
        
        self.logger.info(f"Retrieved status for order {order_id}")
        return response
    
    # Additional Photon-SOL specific methods
    
    def list_tokens(self) -> List[Dict[str, Any]]:
        """
        List all registered tokens on Photon-SOL.
        
        Returns:
            List[Dict[str, Any]]: List of token information
        """
        endpoint = "/tokens"
        response = self._request('GET', endpoint)
        
        self.logger.info("Retrieved token list")
        return response.get('tokens', [])
    
    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific token.
        
        Args:
            token_address (str): Token address on Solana
            
        Returns:
            Dict[str, Any]: Token details
        """
        endpoint = f"/tokens/{token_address}"
        response = self._request('GET', endpoint)
        
        self.logger.info(f"Retrieved token info for {token_address}")
        return response
    
    def connect_wallet(self, wallet_address: str) -> Dict[str, Any]:
        """
        Connect a Solana wallet to the Photon-SOL platform.
        
        Args:
            wallet_address (str): Solana wallet address
            
        Returns:
            Dict[str, Any]: Connection status and details
        """
        endpoint = "/wallet/connect"
        data = {
            'wallet_address': wallet_address
        }
        
        response = self._request('POST', endpoint, data=data, auth=True)
        
        self.logger.info(f"Connected wallet {wallet_address}")
        return response
    
    def get_wallet_info(self) -> Dict[str, Any]:
        """
        Get information about the connected wallet.
        
        Returns:
            Dict[str, Any]: Wallet information
        """
        endpoint = "/wallet/info"
        response = self._request('GET', endpoint, auth=True)
        
        self.logger.info("Retrieved wallet information")
        return response
    
    def get_token_price_history(self, token_address: str, timeframe: str = '1h', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get historical price data for a token.
        
        Args:
            token_address (str): Token address on Solana
            timeframe (str): Timeframe for candles (e.g., '1m', '5m', '1h', '1d')
            limit (int): Maximum number of candles to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of candle data
        """
        endpoint = f"/tokens/{token_address}/history"
        params = {
            'timeframe': timeframe,
            'limit': limit
        }
        
        response = self._request('GET', endpoint, params=params)
        
        self.logger.info(f"Retrieved price history for {token_address}")
        return response.get('candles', [])
    
    def get_trending_tokens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending tokens on Photon-SOL.
        
        Args:
            limit (int): Maximum number of tokens to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of trending tokens
        """
        endpoint = "/tokens/trending"
        params = {'limit': limit}
        
        response = self._request('GET', endpoint, params=params)
        
        self.logger.info(f"Retrieved trending tokens (limit: {limit})")
        return response.get('tokens', [])
    
    def get_new_tokens(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get newly listed tokens on Photon-SOL.
        
        Args:
            days (int): Number of days to look back
            limit (int): Maximum number of tokens to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of new tokens
        """
        endpoint = "/tokens/new"
        params = {
            'days': days,
            'limit': limit
        }
        
        response = self._request('GET', endpoint, params=params)
        
        self.logger.info(f"Retrieved new tokens (days: {days}, limit: {limit})")
        return response.get('tokens', [])
