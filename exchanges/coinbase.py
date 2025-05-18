import os
import requests
import logging
from typing import Dict, Optional, Any
from .base import BaseExchange
from utils.logger import setup_logger

class CoinbaseExchange(BaseExchange):
    BASE_URL = os.getenv("COINBASE_API_BASE_URL", "https://api.coinbase.com/v2")

    def __init__(self, api_key: str, api_secret: str = "", logger: Optional[logging.Logger] = None):
        super().__init__(api_key, api_secret, logger or setup_logger("coinbase_exchange"))
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "CB-VERSION": "2023-01-01",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, auth: bool = True) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError("Unsupported HTTP method")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise

    def get_balance(self) -> Dict[str, float]:
        endpoint = "/accounts"
        response = self._request("GET", endpoint)
        balances = {}
        for account in response.get("data", []):
            currency = account.get("balance", {}).get("currency")
            amount = float(account.get("balance", {}).get("amount", 0))
            if amount > 0:
                balances[currency] = amount
        return balances

    def get_current_price(self, symbol: str) -> str:
        pair = f"{symbol.upper()}-USD"
        endpoint = f"/prices/{pair}/spot"
        try:
            response = self._request("GET", endpoint)
            return response.get("data", {}).get("amount", "N/A")
        except Exception as e:
            self.logger.error(f"Failed to fetch price for {pair}: {e}")
            return "N/A"

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

    def place_market_order(self, symbol: str, side: str, amount: float) -> Dict[str, Any]:
        self.logger.warning("place_market_order not implemented for Coinbase")
        return {"status": "not_implemented", "message": "place_market_order not yet supported"}
