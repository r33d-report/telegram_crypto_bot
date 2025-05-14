
"""
Trading Strategies for Crypto Trading Telegram Bot.

This module provides implementations of various trading strategies
that can be used for automated trading.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Union, Any, Callable
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

from utils.logger import setup_logger
from exchanges.base import BaseExchange

class StrategyType(Enum):
    """Enum for different strategy types."""
    SMA_CROSSOVER = "sma_crossover"
    EMA_CROSSOVER = "ema_crossover"
    RSI = "rsi"
    BOLLINGER_BANDS = "bollinger_bands"
    CUSTOM = "custom"

class TradingSignal(Enum):
    """Enum for trading signals."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class Strategy:
    """
    Base class for all trading strategies.
    """
    
    def __init__(self, name: str, symbol: str, exchange: str, 
                 strategy_type: StrategyType, params: Dict[str, Any],
                 logger: Optional[logging.Logger] = None):
        """
        Initialize a trading strategy.
        
        Args:
            name (str): Strategy name
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            exchange (str): Exchange name ('btcc' or 'coinbase')
            strategy_type (StrategyType): Type of strategy
            params (Dict[str, Any]): Strategy-specific parameters
            logger (Optional[logging.Logger]): Logger instance
        """
        self.name = name
        self.symbol = symbol
        self.exchange = exchange.lower()
        self.strategy_type = strategy_type
        self.params = params
        self.logger = logger or setup_logger(f"strategy_{name}")
        self.last_signal = TradingSignal.HOLD
        self.last_update = None
    
    def get_historical_data(self, exchange_instance: BaseExchange, 
                           timeframe: str, limit: int) -> List[Dict[str, Any]]:
        """
        Get historical price data for analysis.
        
        Args:
            exchange_instance (BaseExchange): Exchange instance
            timeframe (str): Timeframe for data (e.g., '1h', '1d')
            limit (int): Number of candles to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of candles with OHLCV data
        """
        # This is a placeholder. In a real implementation, you would call
        # the exchange API to get historical candles.
        # For now, we'll just return an empty list
        self.logger.warning("get_historical_data is not implemented for this exchange")
        return []
    
    def analyze(self, exchange_instance: BaseExchange) -> TradingSignal:
        """
        Analyze market data and generate a trading signal.
        
        Args:
            exchange_instance (BaseExchange): Exchange instance
            
        Returns:
            TradingSignal: Trading signal (BUY, SELL, or HOLD)
        """
        # This method should be overridden by subclasses
        self.logger.warning("analyze method not implemented")
        return TradingSignal.HOLD
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the strategy to a dictionary for storage.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the strategy
        """
        return {
            'name': self.name,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'strategy_type': self.strategy_type.value,
            'params': self.params,
            'last_signal': self.last_signal.value,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """
        Create a Strategy instance from a dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary representation of the strategy
            
        Returns:
            Strategy: New Strategy instance
        """
        strategy_type = StrategyType(data['strategy_type'])
        
        # Create the appropriate strategy subclass based on type
        if strategy_type == StrategyType.SMA_CROSSOVER:
            strategy = SMAStrategy(
                name=data['name'],
                symbol=data['symbol'],
                exchange=data['exchange'],
                params=data['params']
            )
        elif strategy_type == StrategyType.EMA_CROSSOVER:
            strategy = EMAStrategy(
                name=data['name'],
                symbol=data['symbol'],
                exchange=data['exchange'],
                params=data['params']
            )
        elif strategy_type == StrategyType.RSI:
            strategy = RSIStrategy(
                name=data['name'],
                symbol=data['symbol'],
                exchange=data['exchange'],
                params=data['params']
            )
        elif strategy_type == StrategyType.BOLLINGER_BANDS:
            strategy = BollingerBandsStrategy(
                name=data['name'],
                symbol=data['symbol'],
                exchange=data['exchange'],
                params=data['params']
            )
        else:
            # Default to base Strategy class
            strategy = cls(
                name=data['name'],
                symbol=data['symbol'],
                exchange=data['exchange'],
                strategy_type=strategy_type,
                params=data['params']
            )
        
        # Set last signal and update time
        strategy.last_signal = TradingSignal(data['last_signal']) if data.get('last_signal') else TradingSignal.HOLD
        if data.get('last_update'):
            strategy.last_update = datetime.fromisoformat(data['last_update'])
        
        return strategy


class SMAStrategy(Strategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.
    
    This strategy generates buy signals when a shorter-term SMA crosses above
    a longer-term SMA, and sell signals when it crosses below.
    """
    
    def __init__(self, name: str, symbol: str, exchange: str, 
                 params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the SMA Crossover strategy.
        
        Args:
            name (str): Strategy name
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            exchange (str): Exchange name ('btcc' or 'coinbase')
            params (Dict[str, Any]): Strategy parameters including:
                - short_period (int): Period for short-term SMA
                - long_period (int): Period for long-term SMA
                - timeframe (str): Candle timeframe (e.g., '1h', '1d')
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(
            name=name,
            symbol=symbol,
            exchange=exchange,
            strategy_type=StrategyType.SMA_CROSSOVER,
            params=params,
            logger=logger or setup_logger(f"sma_strategy_{name}")
        )
        
        # Validate required parameters
        required_params = ['short_period', 'long_period', 'timeframe']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        self.short_period = params['short_period']
        self.long_period = params['long_period']
        self.timeframe = params['timeframe']
    
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices (List[float]): List of prices
            period (int): SMA period
            
        Returns:
            List[float]: List of SMA values
        """
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(len(prices) - period + 1):
            sma = sum(prices[i:i+period]) / period
            sma_values.append(sma)
        
        return sma_values
    
    def analyze(self, exchange_instance: BaseExchange) -> TradingSignal:
        """
        Analyze market data and generate a trading signal based on SMA crossover.
        
        Args:
            exchange_instance (BaseExchange): Exchange instance
            
        Returns:
            TradingSignal: Trading signal (BUY, SELL, or HOLD)
        """
        try:
            # Get historical data
            candles = self.get_historical_data(
                exchange_instance, 
                self.timeframe, 
                self.long_period + 10  # Get a few extra candles
            )
            
            if not candles or len(candles) < self.long_period + 2:
                self.logger.warning(f"Not enough historical data for {self.symbol}")
                return TradingSignal.HOLD
            
            # Extract closing prices
            close_prices = [float(candle['close']) for candle in candles]
            
            # Calculate SMAs
            short_sma = self.calculate_sma(close_prices, self.short_period)
            long_sma = self.calculate_sma(close_prices, self.long_period)
            
            if not short_sma or not long_sma:
                return TradingSignal.HOLD
            
            # Check for crossover
            # We need at least 2 values to check for a crossover
            if len(short_sma) < 2 or len(long_sma) < 2:
                return TradingSignal.HOLD
            
            # Adjust indices since SMAs have different lengths
            offset = self.long_period - self.short_period
            
            # Current values
            current_short = short_sma[-1]
            current_long = long_sma[-1]
            
            # Previous values
            prev_short = short_sma[-2]
            prev_long = long_sma[-2]
            
            # Check for crossover
            if prev_short <= prev_long and current_short > current_long:
                # Bullish crossover (short crosses above long)
                signal = TradingSignal.BUY
            elif prev_short >= prev_long and current_short < current_long:
                # Bearish crossover (short crosses below long)
                signal = TradingSignal.SELL
            else:
                # No crossover
                signal = TradingSignal.HOLD
            
            self.last_signal = signal
            self.last_update = datetime.now()
            
            self.logger.info(f"SMA analysis for {self.symbol}: {signal.value}")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in SMA analysis: {str(e)}")
            return TradingSignal.HOLD


class EMAStrategy(Strategy):
    """
    Exponential Moving Average (EMA) Crossover Strategy.
    
    This strategy generates buy signals when a shorter-term EMA crosses above
    a longer-term EMA, and sell signals when it crosses below.
    """
    
    def __init__(self, name: str, symbol: str, exchange: str, 
                 params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the EMA Crossover strategy.
        
        Args:
            name (str): Strategy name
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            exchange (str): Exchange name ('btcc' or 'coinbase')
            params (Dict[str, Any]): Strategy parameters including:
                - short_period (int): Period for short-term EMA
                - long_period (int): Period for long-term EMA
                - timeframe (str): Candle timeframe (e.g., '1h', '1d')
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(
            name=name,
            symbol=symbol,
            exchange=exchange,
            strategy_type=StrategyType.EMA_CROSSOVER,
            params=params,
            logger=logger or setup_logger(f"ema_strategy_{name}")
        )
        
        # Validate required parameters
        required_params = ['short_period', 'long_period', 'timeframe']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        self.short_period = params['short_period']
        self.long_period = params['long_period']
        self.timeframe = params['timeframe']
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices (List[float]): List of prices
            period (int): EMA period
            
        Returns:
            List[float]: List of EMA values
        """
        if len(prices) < period:
            return []
        
        # Calculate multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate first EMA as SMA
        ema_values = [sum(prices[:period]) / period]
        
        # Calculate subsequent EMAs
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    def analyze(self, exchange_instance: BaseExchange) -> TradingSignal:
        """
        Analyze market data and generate a trading signal based on EMA crossover.
        
        Args:
            exchange_instance (BaseExchange): Exchange instance
            
        Returns:
            TradingSignal: Trading signal (BUY, SELL, or HOLD)
        """
        try:
            # Get historical data
            candles = self.get_historical_data(
                exchange_instance, 
                self.timeframe, 
                self.long_period + 10  # Get a few extra candles
            )
            
            if not candles or len(candles) < self.long_period + 2:
                self.logger.warning(f"Not enough historical data for {self.symbol}")
                return TradingSignal.HOLD
            
            # Extract closing prices
            close_prices = [float(candle['close']) for candle in candles]
            
            # Calculate EMAs
            short_ema = self.calculate_ema(close_prices, self.short_period)
            long_ema = self.calculate_ema(close_prices, self.long_period)
            
            if not short_ema or not long_ema:
                return TradingSignal.HOLD
            
            # Check for crossover
            # We need at least 2 values to check for a crossover
            if len(short_ema) < 2 or len(long_ema) < 2:
                return TradingSignal.HOLD
            
            # Current values
            current_short = short_ema[-1]
            current_long = long_ema[-1]
            
            # Previous values
            prev_short = short_ema[-2]
            prev_long = long_ema[-2]
            
            # Check for crossover
            if prev_short <= prev_long and current_short > current_long:
                # Bullish crossover (short crosses above long)
                signal = TradingSignal.BUY
            elif prev_short >= prev_long and current_short < current_long:
                # Bearish crossover (short crosses below long)
                signal = TradingSignal.SELL
            else:
                # No crossover
                signal = TradingSignal.HOLD
            
            self.last_signal = signal
            self.last_update = datetime.now()
            
            self.logger.info(f"EMA analysis for {self.symbol}: {signal.value}")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in EMA analysis: {str(e)}")
            return TradingSignal.HOLD


class RSIStrategy(Strategy):
    """
    Relative Strength Index (RSI) Strategy.
    
    This strategy generates buy signals when RSI falls below the oversold threshold
    and sell signals when it rises above the overbought threshold.
    """
    
    def __init__(self, name: str, symbol: str, exchange: str, 
                 params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the RSI strategy.
        
        Args:
            name (str): Strategy name
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            exchange (str): Exchange name ('btcc' or 'coinbase')
            params (Dict[str, Any]): Strategy parameters including:
                - period (int): RSI calculation period
                - overbought (float): Overbought threshold (default: 70)
                - oversold (float): Oversold threshold (default: 30)
                - timeframe (str): Candle timeframe (e.g., '1h', '1d')
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(
            name=name,
            symbol=symbol,
            exchange=exchange,
            strategy_type=StrategyType.RSI,
            params=params,
            logger=logger or setup_logger(f"rsi_strategy_{name}")
        )
        
        # Validate required parameters
        required_params = ['period', 'timeframe']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        self.period = params['period']
        self.overbought = params.get('overbought', 70)
        self.oversold = params.get('oversold', 30)
        self.timeframe = params['timeframe']
    
    def calculate_rsi(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices (List[float]): List of prices
            period (int): RSI period
            
        Returns:
            List[float]: List of RSI values
        """
        if len(prices) <= period:
            return []
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Calculate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate first RS and RSI
        rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
        rsi_values = [100 - (100 / (1 + rs))]
        
        # Calculate subsequent RSIs
        for i in range(period, len(deltas)):
            # Update average gain and loss using smoothing
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss if avg_loss != 0 else float('inf')
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        return rsi_values
    
    def analyze(self, exchange_instance: BaseExchange) -> TradingSignal:
        """
        Analyze market data and generate a trading signal based on RSI.
        
        Args:
            exchange_instance (BaseExchange): Exchange instance
            
        Returns:
            TradingSignal: Trading signal (BUY, SELL, or HOLD)
        """
        try:
            # Get historical data
            candles = self.get_historical_data(
                exchange_instance, 
                self.timeframe, 
                self.period + 10  # Get a few extra candles
            )
            
            if not candles or len(candles) < self.period + 2:
                self.logger.warning(f"Not enough historical data for {self.symbol}")
                return TradingSignal.HOLD
            
            # Extract closing prices
            close_prices = [float(candle['close']) for candle in candles]
            
            # Calculate RSI
            rsi_values = self.calculate_rsi(close_prices, self.period)
            
            if not rsi_values:
                return TradingSignal.HOLD
            
            # Get current RSI
            current_rsi = rsi_values[-1]
            
            # Generate signal based on RSI thresholds
            if current_rsi <= self.oversold:
                signal = TradingSignal.BUY
            elif current_rsi >= self.overbought:
                signal = TradingSignal.SELL
            else:
                signal = TradingSignal.HOLD
            
            self.last_signal = signal
            self.last_update = datetime.now()
            
            self.logger.info(f"RSI analysis for {self.symbol}: {signal.value} (RSI: {current_rsi:.2f})")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in RSI analysis: {str(e)}")
            return TradingSignal.HOLD


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Strategy.
    
    This strategy generates buy signals when price touches the lower band
    and sell signals when price touches the upper band.
    """
    
    def __init__(self, name: str, symbol: str, exchange: str, 
                 params: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the Bollinger Bands strategy.
        
        Args:
            name (str): Strategy name
            symbol (str): Trading pair symbol (e.g., 'BTC/USDT')
            exchange (str): Exchange name ('btcc' or 'coinbase')
            params (Dict[str, Any]): Strategy parameters including:
                - period (int): Period for SMA calculation
                - std_dev (float): Number of standard deviations for bands
                - timeframe (str): Candle timeframe (e.g., '1h', '1d')
            logger (Optional[logging.Logger]): Logger instance
        """
        super().__init__(
            name=name,
            symbol=symbol,
            exchange=exchange,
            strategy_type=StrategyType.BOLLINGER_BANDS,
            params=params,
            logger=logger or setup_logger(f"bb_strategy_{name}")
        )
        
        # Validate required parameters
        required_params = ['period', 'std_dev', 'timeframe']
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        self.period = params['period']
        self.std_dev = params['std_dev']
        self.timeframe = params['timeframe']
    
    def calculate_bollinger_bands(self, prices: List[float], period: int, std_dev: float) -> Dict[str, List[float]]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices (List[float]): List of prices
            period (int): Period for SMA calculation
            std_dev (float): Number of standard deviations for bands
            
        Returns:
            Dict[str, List[float]]: Dictionary with 'middle', 'upper', and 'lower' bands
        """
        if len(prices) < period:
            return {'middle': [], 'upper': [], 'lower': []}
        
        # Calculate SMA (middle band)
        middle_band = []
        for i in range(len(prices) - period + 1):
            sma = sum(prices[i:i+period]) / period
            middle_band.append(sma)
        
        # Calculate upper and lower bands
        upper_band = []
        lower_band = []
        
        for i in range(len(middle_band)):
            # Calculate standard deviation
            price_slice = prices[i:i+period]
            std = np.std(price_slice)
            
            # Calculate bands
            upper = middle_band[i] + (std_dev * std)
            lower = middle_band[i] - (std_dev * std)
            
            upper_band.append(upper)
            lower_band.append(lower)
        
        return {
            'middle': middle_band,
            'upper': upper_band,
            'lower': lower_band
        }
    
    def analyze(self, exchange_instance: BaseExchange) -> TradingSignal:
        """
        Analyze market data and generate a trading signal based on Bollinger Bands.
        
        Args:
            exchange_instance (BaseExchange): Exchange instance
            
        Returns:
            TradingSignal: Trading signal (BUY, SELL, or HOLD)
        """
        try:
            # Get historical data
            candles = self.get_historical_data(
                exchange_instance, 
                self.timeframe, 
                self.period + 10  # Get a few extra candles
            )
            
            if not candles or len(candles) < self.period + 2:
                self.logger.warning(f"Not enough historical data for {self.symbol}")
                return TradingSignal.HOLD
            
            # Extract closing prices
            close_prices = [float(candle['close']) for candle in candles]
            
            # Calculate Bollinger Bands
            bands = self.calculate_bollinger_bands(close_prices, self.period, self.std_dev)
            
            if not bands['middle'] or not bands['upper'] or not bands['lower']:
                return TradingSignal.HOLD
            
            # Get current price and bands
            current_price = close_prices[-1]
            current_upper = bands['upper'][-1]
            current_lower = bands['lower'][-1]
            current_middle = bands['middle'][-1]
            
            # Generate signal based on price position relative to bands
            if current_price <= current_lower:
                signal = TradingSignal.BUY
            elif current_price >= current_upper:
                signal = TradingSignal.SELL
            else:
                signal = TradingSignal.HOLD
            
            self.last_signal = signal
            self.last_update = datetime.now()
            
            self.logger.info(f"Bollinger Bands analysis for {self.symbol}: {signal.value}")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in Bollinger Bands analysis: {str(e)}")
            return TradingSignal.HOLD


class StrategyManager:
    """
    Manages trading strategies and their execution.
    """
    
    def __init__(self, get_exchange_func: Callable, order_callback: Callable,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the strategy manager.
        
        Args:
            get_exchange_func (Callable): Function to get exchange instance
            order_callback (Callable): Function to call when a strategy generates a signal
            logger (Optional[logging.Logger]): Logger instance
        """
        self.strategies: Dict[str, Strategy] = {}
        self.get_exchange = get_exchange_func
        self.order_callback = order_callback
        self.logger = logger or setup_logger("strategy_manager")
        self.lock = threading.Lock()
    
    def add_strategy(self, strategy: Strategy) -> bool:
        """
        Add a new trading strategy.
        
        Args:
            strategy (Strategy): Strategy to add
            
        Returns:
            bool: True if strategy was added successfully, False otherwise
        """
        with self.lock:
            self.strategies[strategy.name] = strategy
            self.logger.info(f"Added strategy {strategy.name} for {strategy.symbol} on {strategy.exchange}")
            return True
    
    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Remove a trading strategy.
        
        Args:
            strategy_name (str): Name of the strategy to remove
            
        Returns:
            bool: True if strategy was removed successfully, False otherwise
        """
        with self.lock:
            if strategy_name in self.strategies:
                del self.strategies[strategy_name]
                self.logger.info(f"Removed strategy {strategy_name}")
                return True
            return False
    
    def get_strategy(self, strategy_name: str) -> Optional[Strategy]:
        """
        Get a specific strategy by name.
        
        Args:
            strategy_name (str): Strategy name
            
        Returns:
            Optional[Strategy]: Strategy if found, None otherwise
        """
        with self.lock:
            return self.strategies.get(strategy_name)
    
    def get_strategies_for_symbol(self, symbol: str, exchange: str) -> List[Strategy]:
        """
        Get all strategies for a specific symbol and exchange.
        
        Args:
            symbol (str): Trading pair symbol
            exchange (str): Exchange name
            
        Returns:
            List[Strategy]: List of strategies
        """
        with self.lock:
            return [
                strategy for strategy in self.strategies.values()
                if strategy.symbol == symbol and strategy.exchange.lower() == exchange.lower()
            ]
    
    def execute_strategy(self, strategy_name: str) -> Optional[TradingSignal]:
        """
        Execute a specific strategy and generate a trading signal.
        
        Args:
            strategy_name (str): Name of the strategy to execute
            
        Returns:
            Optional[TradingSignal]: Trading signal if strategy was executed successfully, None otherwise
        """
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            self.logger.warning(f"Strategy {strategy_name} not found")
            return None
        
        try:
            exchange = self.get_exchange(strategy.exchange)
            signal = strategy.analyze(exchange)
            
            # Call the order callback if the signal is not HOLD
            if signal != TradingSignal.HOLD:
                self.order_callback(strategy, signal)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error executing strategy {strategy_name}: {str(e)}")
            return None
    
    def save_strategies(self, filepath: str) -> bool:
        """
        Save all strategies to a file.
        
        Args:
            filepath (str): Path to save the strategies
            
        Returns:
            bool: True if strategies were saved successfully, False otherwise
        """
        import json
        
        try:
            with self.lock:
                strategies_data = {name: strategy.to_dict() for name, strategy in self.strategies.items()}
            
            with open(filepath, 'w') as f:
                json.dump(strategies_data, f, indent=2)
            
            self.logger.info(f"Saved {len(self.strategies)} strategies to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving strategies to {filepath}: {str(e)}")
            return False
    
    def load_strategies(self, filepath: str) -> bool:
        """
        Load strategies from a file.
        
        Args:
            filepath (str): Path to load the strategies from
            
        Returns:
            bool: True if strategies were loaded successfully, False otherwise
        """
        import json
        import os
        
        if not os.path.exists(filepath):
            self.logger.warning(f"Strategies file {filepath} does not exist")
            return False
        
        try:
            with open(filepath, 'r') as f:
                strategies_data = json.load(f)
            
            with self.lock:
                self.strategies = {name: Strategy.from_dict(data) for name, data in strategies_data.items()}
            
            self.logger.info(f"Loaded {len(self.strategies)} strategies from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading strategies from {filepath}: {str(e)}")
            return False

