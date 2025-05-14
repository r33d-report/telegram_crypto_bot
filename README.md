
# Crypto Trading Telegram Bot

A Telegram bot for cryptocurrency trading and meme coin sniping that integrates with BTCC, Coinbase, and Photon-SOL exchanges.

## Features

- **Price Alerts**: Set alerts for specific price conditions and receive notifications
- **Automatic Trading**: Define and execute trading strategies automatically
- **Wallet Integration**: Check balances and manage funds across exchanges
- **Trading Operations**: Place market and limit orders, view order books
- **Futures Trading**: Open long/short positions, set leverage, and manage futures contracts
- **Meme Coin Sniping**: Monitor new token listings and sudden price/volume increases
- **User-Friendly Interface**: Inline keyboards and custom menus for easy navigation
- **Multi-Exchange Support**: Compatible with BTCC, Coinbase, and Photon-SOL

## Setup Guide

### Step 1: Create a Telegram Bot using BotFather

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Start a chat with BotFather by clicking "Start"
3. Send the command `/newbot` to create a new bot
4. Follow the prompts:
   - Enter a name for your bot (e.g., "MyCryptoTrader Bot")
   - Enter a username for your bot (must end with "bot", e.g., "MyCryptoTraderBot")
5. BotFather will provide you with a token (API key) that looks like this: `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`
6. **Important**: Keep this token secure! It gives full access to control your bot.

### Step 2: Set Up the Python Environment

1. Make sure you have Python 3.8+ installed on your system
2. Clone or download this repository to your local machine
3. Navigate to the project directory in your terminal
4. Create a virtual environment:
   ```
   python -m venv venv
   ```
5. Activate the virtual environment:
   - On Windows: `venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
6. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

### Step 3: Configure the Bot

1. Create a `.env` file in the project root directory (copy from `.env.example`)
2. Add your Telegram bot token to the `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_TOKEN_HERE
   ```
3. Add your exchange API keys to the `.env` file:
   ```
   # BTCC API Keys
   BTCC_API_KEY=YOUR_BTCC_API_KEY
   BTCC_API_SECRET=YOUR_BTCC_API_SECRET
   
   # Coinbase API Keys
   COINBASE_API_KEY=YOUR_COINBASE_API_KEY
   COINBASE_API_SECRET=YOUR_COINBASE_API_SECRET
   
   # Photon-SOL API Keys
   PHOTON_SOL_API_KEY=YOUR_PHOTON_SOL_API_KEY
   PHOTON_SOL_API_SECRET=YOUR_PHOTON_SOL_API_SECRET
   ```

### Step 4: Setting Up Exchange API Keys

#### BTCC API Keys

1. Log in to your BTCC account
2. Navigate to Account Settings > API Management
3. Click "Create API Key"
4. Set the permissions (Read and Trade permissions are required for full functionality)
5. Optionally, restrict API access to specific IP addresses for enhanced security
6. Complete the verification process (may require 2FA)
7. Save the API Key and Secret Key securely
8. Add these keys to your `.env` file as shown above

#### Coinbase API Keys

1. Log in to your Coinbase account
2. Visit the [Coinbase Developer Platform](https://www.coinbase.com/developer-platform)
3. Create a new API key with the following permissions:
   - View permission (for account and market data)
   - Trade permission (for placing and managing orders)
4. Complete the verification process (requires 2FA)
5. Download the generated JSON file containing the key and private key
6. Add these keys to your `.env` file as shown above

#### Photon-SOL API Keys

1. Log in to your Photon-SOL account at [https://photon-sol.tinyastro.io/](https://photon-sol.tinyastro.io/)
2. Navigate to Account Settings > API Keys
3. Click "Generate New API Key"
4. Set the permissions:
   - Read permission for market data access
   - Trade permission for executing trades
   - Wallet permission for balance queries and transfers
5. Complete the verification process (may require 2FA)
6. Save the API Key and Secret Key securely
7. Add these keys to your `.env` file as shown above

### Step 5: Run the Bot

1. Make sure your virtual environment is activated
2. Run the bot:
   ```
   python bot.py
   ```
3. Open Telegram and search for your bot by its username
4. Start a chat with your bot and send the `/start` command

## Usage

The bot supports the following commands:

### Basic Commands
- `/start` - Initialize the bot and receive a welcome message
- `/help` - Display available commands and their descriptions

### Trading Commands
- `/price <symbol> <exchange>` - Get current price for a symbol (e.g., `/price BTC/USDT btcc`)
- `/balance <exchange>` - Check your wallet balance (e.g., `/balance coinbase`)
- `/buy <symbol> <amount> <exchange>` - Place a market buy order
- `/sell <symbol> <amount> <exchange>` - Place a market sell order
- `/limit_buy <symbol> <amount> <price> <exchange>` - Place a limit buy order
- `/limit_sell <symbol> <amount> <price> <exchange>` - Place a limit sell order
- `/orderbook <symbol> <exchange>` - Get order book for a symbol
- `/cancel <order_id> <symbol> <exchange>` - Cancel an order

### Price Alert Commands
- `/set_alert <symbol> <price> <above|below> <exchange>` - Set a price alert
- `/alerts` - List your active price alerts
- `/remove_alert <alert_id>` - Remove a price alert

### Automatic Trading Commands
- `/set_strategy <name> <type> <symbol> <exchange>` - Set up a trading strategy
- `/strategies` - List your active strategies
- `/remove_strategy <name>` - Remove a strategy
- `/run_strategy <name>` - Run a strategy once

### Futures Trading Commands
- `/futures_balance` - Check your futures account balance
- `/futures_positions` - View your open futures positions
- `/futures_leverage <symbol> <leverage>` - Set leverage for a symbol
- `/futures_long <symbol> <amount>` - Open a long position
- `/futures_short <symbol> <amount>` - Open a short position
- `/futures_close <symbol>` - Close a futures position

### Meme Coin Commands
- `/meme_trending` - Show trending meme coins
- `/meme_new` - Show new meme coin listings
- `/set_sniper` - Set up a meme coin sniper
- `/snipers` - List your active snipers
- `/remove_sniper <id>` - Remove a sniper

### Photon-SOL Specific Commands
- `/photon_price <symbol>` - Get current price for a token on Photon-SOL
- `/photon_balance` - Check your Photon-SOL wallet balance
- `/photon_buy <symbol> <amount>` - Place a market buy order on Photon-SOL
- `/photon_sell <symbol> <amount>` - Place a market sell order on Photon-SOL
- `/photon_tokens` - List available tokens on Photon-SOL
- `/photon_trending` - Show trending tokens on Photon-SOL
- `/photon_new` - Show new token listings on Photon-SOL

## Advanced Features

### Price Alert System

The price alert system allows you to:
- Set alerts for when a cryptocurrency's price goes above or below a specified value
- Receive instant notifications when your alert conditions are met
- Manage multiple alerts across different exchanges and trading pairs
- Easily create alerts directly from the price display with inline buttons

Example:
```
/set_alert BTC/USDT 50000 above btcc
```
This will notify you when Bitcoin's price goes above $50,000 on BTCC.

### Automatic Trading Strategies

The bot supports several trading strategies:
- **SMA Crossover**: Generates signals based on Simple Moving Average crossovers
- **EMA Crossover**: Uses Exponential Moving Average crossovers for trading signals
- **RSI**: Trades based on Relative Strength Index overbought/oversold conditions
- **Bollinger Bands**: Generates signals when price touches upper or lower bands

Example:
```
/set_strategy btc_sma BTC/USDT sma_crossover btcc
```
Then follow the prompts to configure the strategy parameters.

### Futures Trading

The futures trading module supports:
- Opening long and short positions
- Setting leverage for different trading pairs
- Viewing open positions and account balance
- Closing positions with a single command
- Checking funding rates

Example:
```
/futures_leverage BTC/USDT 10
/futures_long BTC/USDT 0.1
```

### Meme Coin Sniping

The meme coin sniping system allows you to:
- Monitor new token listings across multiple blockchains
- Set up alerts for sudden price or volume increases
- Filter tokens by market cap, keywords, and other criteria
- Quickly buy tokens with a single click
- Optionally enable auto-buy for matching tokens

Example:
```
/set_sniper
```
Then follow the prompts to configure your sniper parameters.

### Photon-SOL Integration

The Photon-SOL integration provides:
- Fast trading on the Solana blockchain
- Access to new token listings and trending tokens
- Real-time price monitoring
- Wallet integration for Solana-compatible wallets
- Token filtering based on various criteria

Example:
```
/photon_trending
```
This will show you the currently trending tokens on Photon-SOL.

## Project Structure

```
telegram_crypto_bot/
├── bot.py                # Main bot application
├── config.py             # Configuration handling
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables file
├── .env                  # Your actual environment variables (not in repo)
├── data/                 # Persistent data storage
│   ├── price_alerts.json # Saved price alerts
│   ├── strategies.json   # Saved trading strategies
│   ├── meme_tokens.json  # Tracked meme tokens
│   └── meme_alerts.json  # Meme coin sniper settings
├── exchanges/            # Exchange API integrations
│   ├── __init__.py       # Package initialization
│   ├── base.py           # Base exchange class
│   ├── btcc.py           # BTCC exchange implementation
│   ├── futures_btcc.py   # BTCC futures implementation
│   ├── coinbase.py       # Coinbase exchange implementation
│   └── photon_sol.py     # Photon-SOL exchange implementation
└── utils/                # Utility functions
    ├── __init__.py       # Makes utils a proper package
    ├── logger.py         # Logging configuration
    ├── price_alerts.py   # Price alert system
    ├── strategies.py     # Trading strategies
    ├── scheduler.py      # Task scheduler
    ├── keyboards.py      # Custom keyboard layouts
    └── meme_sniper.py    # Meme coin sniping system
```

## Extending the Bot

To add new commands:

1. Create a new function in `bot.py` or in a separate module
2. Register the function as a command handler in the main application
3. Update the help text to include the new command

Example of adding a new command:

```python
async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /my_command"""
    await update.message.reply_text("This is my custom command")

# In the main function, add:
application.add_handler(CommandHandler("my_command", my_command))
```

## Adding Support for New Exchanges

To add support for a new exchange:

1. Create a new file in the `exchanges` directory (e.g., `exchanges/new_exchange.py`)
2. Implement the exchange class by inheriting from `BaseExchange` in `exchanges/base.py`
3. Implement all required methods (authentication, market data, trading, etc.)
4. Update the `config.py` file to include configuration for the new exchange
5. Update the `.env.example` file with the new environment variables
6. Import and register the new exchange in `exchanges/__init__.py`

## Adding New Trading Strategies

To add a new trading strategy:

1. Create a new strategy class in `utils/strategies.py` that inherits from the `Strategy` base class
2. Implement the `analyze` method to generate trading signals
3. Add the new strategy type to the `StrategyType` enum
4. Update the `Strategy.from_dict` method to handle the new strategy type
5. Update the help documentation to include the new strategy

## Error Handling

The bot includes error handling to catch and log exceptions. Check the logs if you encounter any issues.

## Security Notes

- Never share your bot token or API keys
- The `.env` file containing sensitive information is excluded from version control
- Consider implementing additional security measures for production use
- Regularly rotate your API keys
- Use IP whitelisting for API access when available
- Enable 2FA on your exchange accounts

# Telegram Crypto Bot

This is a Telegram bot for trading and sniping meme coins.

## Features

- /price → returns current BTC or ETH price
- /alerts → set price alerts
- /snipe → start meme coin sniping
- /log → send latest error log

## Installation

Clone this repo and run:

```bash
python3 bot.py

## Disclaimer

This bot is provided for educational and informational purposes only. Trading cryptocurrencies involves significant risk. Use this bot at your own risk.
Webhook update test: 🚀 Wed May 14 17:09:41 UTC 2025
Test webhook at Wed May 14 17:22:49 UTC 2025
Test again at Wed May 14 17:33:01 UTC 2025
Test again at Wed May 14 17:34:26 UTC 2025
Push test at Wed May 14 17:37:33 UTC 2025
Push test at Wed May 14 17:38:24 UTC 2025
