
"""
Configuration module for the Crypto Trading Telegram Bot.

This module handles loading environment variables and provides
a central place for accessing configuration settings.
"""

import os
import logging
from dotenv import load_dotenv
from typing import Dict, Optional

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class for the Crypto Trading Telegram Bot.
    
    This class provides access to configuration settings loaded from
    environment variables and handles validation of required settings.
    """
    
    # Telegram Bot settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # BTCC API settings
    BTCC_API_KEY = os.getenv("BTCC_API_KEY")
    BTCC_API_SECRET = os.getenv("BTCC_API_SECRET")
    
    # Coinbase API settings
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
    
    # Photon-SOL API settings
    PHOTON_SOL_API_KEY = os.getenv("PHOTON_SOL_API_KEY")
    PHOTON_SOL_API_SECRET = os.getenv("PHOTON_SOL_API_SECRET")
    
    @classmethod
    def validate_telegram_config(cls) -> bool:
        """
        Validate Telegram bot configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return bool(cls.TELEGRAM_BOT_TOKEN)
    
    @classmethod
    def validate_exchange_config(cls, exchange: str) -> bool:
        """
        Validate exchange API configuration.
        
        Args:
            exchange (str): Exchange name ('btcc', 'coinbase', or 'photon_sol')
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if exchange.lower() == 'btcc':
            return bool(cls.BTCC_API_KEY and cls.BTCC_API_SECRET)
        elif exchange.lower() == 'coinbase':
            return bool(cls.COINBASE_API_KEY and cls.COINBASE_API_SECRET)
        elif exchange.lower() == 'photon_sol':
            return bool(cls.PHOTON_SOL_API_KEY and cls.PHOTON_SOL_API_SECRET)
        else:
            return False
    
    @classmethod
    def get_exchange_credentials(cls, exchange: str) -> Dict[str, str]:
        """
        Get API credentials for a specific exchange.
        
        Args:
            exchange (str): Exchange name ('btcc', 'coinbase', or 'photon_sol')
            
        Returns:
            Dict[str, str]: Dictionary with 'api_key' and 'api_secret'
            
        Raises:
            ValueError: If exchange is not supported or credentials are missing
        """
        if exchange.lower() == 'btcc':
            if not cls.validate_exchange_config('btcc'):
                raise ValueError("BTCC API credentials are not configured")
            return {
                'api_key': cls.BTCC_API_KEY,
                'api_secret': cls.BTCC_API_SECRET
            }
        elif exchange.lower() == 'coinbase':
            if not cls.validate_exchange_config('coinbase'):
                raise ValueError("Coinbase API credentials are not configured")
            return {
                'api_key': cls.COINBASE_API_KEY,
                'api_secret': cls.COINBASE_API_SECRET
            }
        elif exchange.lower() == 'photon_sol':
            if not cls.validate_exchange_config('photon_sol'):
                raise ValueError("Photon-SOL API credentials are not configured")
            return {
                'api_key': cls.PHOTON_SOL_API_KEY,
                'api_secret': cls.PHOTON_SOL_API_SECRET
            }
        else:
            raise ValueError(f"Unsupported exchange: {exchange}")

# Create a singleton instance
config = Config()
