import time
import hmac
import hashlib
import json
import logging
import requests
from typing import Dict, Any, Optional

from .base import BaseExchange
from utils.logger import setup_logger


class BTCCExchange(BaseExchange):
    BASE_URL = "https://api.btcc.com"

    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        super().__init__(api_key, api_secret, logger or setup_logger("btcc_exchange"))
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'CryptoTradingTelegramBot/1.0'
        })

    def _generate_signature(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items())) if params else ""
        body_string = json.dumps(data) if data else ""

        message = f"{timestamp}{method.upper()}{endpoint}"
        if query_string:
            message += f"?{query_string}"
        if body_string:
            message += body_string

        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            'BTCC-API-KEY': self.api_key,
            'BTCC-API-TIMESTAMP': timestamp,
            'BTCC-API-SIGNATURE': signature
        }

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, auth: bool = False) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._generate_signature(method, endpoint, params, data) if auth else {}

        try:
            response = self.session.request(method=method, url=url, params=params, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        formatted_symbol = symbol.replace('/', '_')
        endpoint = f"/v1/market/ticker/{formatted_symbol}"
        return self._request("GET", endpoint)

    def get_balance(self) -> Dict[str, float]:
        endpoint = "/v1/account/balance"
        res = self._request("GET", endpoint, auth=True)
        return {asset['currency']: float(asset['available']) for asset in res.get('data', [])}

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        formatted_symbol = symbol.replace('/', '_')
        endpoint = f"/v1/market/depth/{formatted_symbol}"
        params = {'limit': limit}
        return self._request("GET", endpoint, params=params)

    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        formatted_symbol = symbol.replace('/', '_')
        endpoint = "/v1/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'market',
            'quantity': str(amount)
        }
        return self._request("POST", endpoint, data=data, auth=True)

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        formatted_symbol = symbol.replace('/', '_')
        endpoint = "/v1/order/create"
        data = {
            'symbol': formatted_symbol,
            'side': side.lower(),
            'type': 'limit',
            'quantity': str(amount),
            'price': str(price)
        }
        return self._request("POST", endpoint, data=data, auth=True)

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        if not symbol:
            raise ValueError("Symbol is required to cancel orders on BTCC")
        formatted_symbol = symbol.replace('/', '_')
        endpoint = "/v1/order/cancel"
        data = {'symbol': formatted_symbol, 'orderId': order_id}
        self._request("POST", endpoint, data=data, auth=True)
        return True

    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        if not symbol:
            raise ValueError("Symbol is required for order status")
        formatted_symbol = symbol.replace('/', '_')
        endpoint = "/v1/order/status"
        params = {'symbol': formatted_symbol, 'orderId': order_id}
        return self._request("GET", endpoint, params=params, auth=True)
