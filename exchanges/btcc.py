import os
import time
import hashlib
import json
import logging
import requests
from typing import Dict, Optional, Any

from .base import BaseExchange
from utils.logger import setup_logger


class BTCCExchange(BaseExchange):
    BASE_URL = os.getenv("BTCC_API_BASE_URL", "https://spotapi2.btcccdn.com")

    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        super().__init__(api_key, api_secret, logger or setup_logger("btcc_exchange"))
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CryptoTradingTelegramBot/1.0'
        })

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generates the BTCC MD5 signature used for v1.6 Spot API auth."""
        params_with_key = params.copy()
        params_with_key["secret_key"] = self.api_secret
        sorted_params = sorted(params_with_key.items())
        query_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        signature = hashlib.md5(query_string.encode('utf-8')).hexdigest()
        return signature

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, auth: bool = False) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}

        if auth:
            params = params or {}
            params["access_id"] = self.api_key
            params["tm"] = int(time.time())
            signature = self._generate_signature(params)
            headers["authorization"] = signature

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        symbol_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "sol": "solana",
            "xrp": "ripple",
            "ada": "cardano",
            "doge": "dogecoin"
        }
    
        clean_symbol = symbol.lower().split("/")[0]
        coin_id = symbol_map.get(clean_symbol)
    
        if not coin_id:
            raise ValueError(f"Symbol '{symbol}' not supported.")
    
        response = requests.get("https://api.coingecko.com/api/v3/simple/price", params={
            "ids": coin_id,
            "vs_currencies": "usd"
        })
        response.raise_for_status()
        return response.json()
    
    def get_current_price(self, symbol: str) -> str:
        prices = self.get_ticker(symbol)
        coin_id = list(prices.keys())[0]
        return str(prices.get(coin_id, {}).get("usd", "N/A"))

    def get_balance(self) -> Dict[str, float]:
        endpoint = "/btcc_api_trade/asset/query"
        response = self._request("GET", endpoint, auth=True)
        balances = {}
        for asset in response.get('data', []):
            balances[asset['currency']] = float(asset.get('available', 0.0))
        return balances

    # Deprecated endpoints below are kept for later reimplementation (Futures API):
    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        raise NotImplementedError("Order book not supported in Spot API v1.6")

    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        raise NotImplementedError("Market orders are not yet implemented in this version.")

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        raise NotImplementedError("Limit orders are not yet implemented in this version.")

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        raise NotImplementedError("Cancel order is not yet implemented.")

    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("Order status is not yet implemented.")
