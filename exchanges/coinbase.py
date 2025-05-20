import os
import time
import uuid
import json
import hmac
import hashlib
import base64
import requests
import logging
from typing import Dict, Optional, Any
from .base import BaseExchange
from utils.logger import setup_logger


class CoinbaseExchange(BaseExchange):
    BASE_URL = os.getenv("COINBASE_API_BASE_URL", "https://api.coinbase.com/api/v3")

    def __init__(self, api_key: str, api_secret: str, logger: Optional[logging.Logger] = None):
        super().__init__(api_key, api_secret, logger or setup_logger("coinbase_exchange"))
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()

    def _generate_headers(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        timestamp = str(int(time.time()))
        message = f"{timestamp}{method.upper()}{endpoint}{body}"
        signature = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()

        return {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature_b64,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        body = json.dumps(data) if data else ""
        headers = self._generate_headers(method, endpoint, body)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, data=body, headers=headers)
            else:
                raise ValueError("Unsupported HTTP method")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise

    def get_balance(self) -> Dict[str, float]:
        endpoint = "/brokerage/accounts"
        response = self._request("GET", endpoint)
        balances = {}
        for account in response.get("accounts", []):
            balance = float(account.get("available_balance", {}).get("value", 0))
            currency = account.get("currency")
            if balance > 0:
                balances[currency] = balance
        return balances

    def get_current_price(self, symbol: str) -> str:
        pair = f"{symbol.upper()}-USD"
        endpoint = f"/brokerage/products/{pair}/ticker"
        try:
            response = self._request("GET", endpoint)
            return response.get("price", "N/A")
        except Exception as e:
            self.logger.error(f"Failed to fetch price for {pair}: {e}")
            return "N/A"

    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        endpoint = "/brokerage/orders"
        data = {
            "client_order_id": str(uuid.uuid4()),
            "product_id": f"{symbol.upper()}-USD",
            "side": side,
            "order_configuration": {
                "market_market_ioc": {
                    "base_size": str(amount)
                }
            }
        }
        return self._request("POST", endpoint, data=data)

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        self.logger.warning("cancel_order not implemented for Coinbase")
        return False

    def get_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        self.logger.warning("get_order_book not implemented for Coinbase")
        return {}

    def get_order_status(self, order_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        self.logger.warning("get_order_status not implemented for Coinbase")
        return {}

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        self.logger.warning("get_ticker not implemented for Coinbase (use get_current_price instead)")
        return {}

    def place_limit_order(self, symbol: str, side: str, amount: float, price: float) -> Dict[str, Any]:
        self.logger.warning("place_limit_order not implemented for Coinbase")
        return {"status": "not_implemented", "message": "place_limit_order not yet supported"}
