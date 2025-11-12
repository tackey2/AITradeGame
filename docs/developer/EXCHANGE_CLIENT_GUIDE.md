# Binance Exchange Client Guide

**Module:** `exchange_client.py`
**Purpose:** Interface with Binance exchange for live trading
**Safety:** Supports both Testnet (fake money) and Mainnet (real money)

---

## 🎯 Quick Start

### 1. Get Binance Testnet Account

**Why Testnet?** Test with fake money before risking real money!

1. Go to: https://testnet.binance.vision/
2. Create account (or login with GitHub)
3. Click your profile → API Management
4. Create new API key
5. Save API Key and Secret Key

**Free Testnet Funds:**
- You get fake USDT and BTC automatically
- Use for testing without any risk
- Reset anytime if needed

### 2. Test the Client

```python
from exchange_client import ExchangeClient

# Initialize with testnet keys
client = ExchangeClient(
    api_key="your_testnet_api_key",
    api_secret="your_testnet_secret",
    testnet=True  # ALWAYS use testnet for testing!
)

# Check connection
if client.ping():
    print("✅ Connected!")

# Get account info
account = client.get_account_info()
print(f"Balance: {account['balances']}")
```

### 3. Run Test Script

```bash
# 1. Edit test_exchange_client.py
# 2. Add your testnet API keys
# 3. Run tests

python test_exchange_client.py
```

---

## 📚 Features

### ✅ What's Included

1. **Account Management**
   - Get account info and permissions
   - Check balances (any asset)
   - Monitor positions

2. **Market Data**
   - Get current prices
   - Get symbol trading rules
   - Server time sync

3. **Order Placement**
   - Market orders (instant execution)
   - Limit orders (price-based execution)
   - Test mode (validation without execution)

4. **Order Management**
   - Get order status
   - Cancel individual orders
   - Cancel all orders for symbol
   - List open orders

5. **Safety Features**
   - Emergency cancel all orders
   - Testnet mode (default)
   - Comprehensive error handling
   - Logging of all operations

---

## 🔧 API Reference

### Initialization

```python
client = ExchangeClient(
    api_key: str,           # Binance API key
    api_secret: str,        # Binance API secret
    testnet: bool = True,   # Use testnet (default: True)
    timeout: int = 30       # Request timeout in seconds
)
```

**⚠️ IMPORTANT:** `testnet=True` by default for safety!

---

### Account Information

#### Get Account Info
```python
account = client.get_account_info()

# Returns:
{
    'can_trade': True,
    'can_withdraw': False,
    'can_deposit': True,
    'permissions': ['SPOT'],
    'balances': {
        'USDT': {'free': 10000.0, 'locked': 0.0, 'total': 10000.0},
        'BTC': {'free': 0.5, 'locked': 0.0, 'total': 0.5}
    },
    'update_time': 1699564800000
}
```

#### Get Balance
```python
balance = client.get_balance('USDT')

# Returns:
{
    'asset': 'USDT',
    'free': 10000.0,      # Available for trading
    'locked': 0.0,        # In open orders
    'total': 10000.0      # Total balance
}
```

#### Get Positions
```python
positions = client.get_positions()

# Returns (only non-zero balances):
{
    'USDT': 10000.0,
    'BTC': 0.5,
    'ETH': 2.0
}
```

---

### Market Data

#### Get Current Price
```python
price = client.get_ticker_price('BTCUSDT')
# Returns: 43250.50
```

#### Get Symbol Info
```python
info = client.get_symbol_info('BTCUSDT')

# Returns:
{
    'symbol': 'BTCUSDT',
    'status': 'TRADING',
    'base_asset': 'BTC',
    'quote_asset': 'USDT',
    'filters': {
        'min_qty': 0.00001,
        'max_qty': 9000.0,
        'step_size': 0.00001,
        'min_price': 0.01,
        'max_price': 1000000.0,
        'tick_size': 0.01,
        'min_notional': 10.0
    }
}
```

---

### Order Placement

#### Market Order (Instant Execution)

```python
# Buy BTC with market price
order = client.place_market_order(
    symbol='BTCUSDT',
    side='BUY',           # or 'SELL'
    quantity=0.001,       # Amount in BTC
    test=False            # Set True to test without execution
)

# Returns:
{
    'order_id': 12345,
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'type': 'MARKET',
    'status': 'FILLED',
    'quantity': 0.001,
    'executed_qty': 0.001,
    'price': None,
    'time': 1699564800000
}
```

#### Limit Order (Price-Based)

```python
# Sell BTC at specific price
order = client.place_limit_order(
    symbol='BTCUSDT',
    side='SELL',
    quantity=0.001,
    price=45000.0,        # Limit price
    time_in_force='GTC',  # Good Till Cancel
    test=False
)

# Returns same format as market order
```

**Time in Force Options:**
- `GTC` - Good Till Cancel (default)
- `IOC` - Immediate or Cancel
- `FOK` - Fill or Kill

---

### Order Management

#### Get Order Status
```python
order = client.get_order(
    symbol='BTCUSDT',
    order_id=12345
)
```

#### Cancel Order
```python
result = client.cancel_order(
    symbol='BTCUSDT',
    order_id=12345
)
```

#### Cancel All Orders (Symbol)
```python
results = client.cancel_all_orders('BTCUSDT')
```

#### Get Open Orders
```python
# All symbols
all_orders = client.get_open_orders()

# Specific symbol
btc_orders = client.get_open_orders('BTCUSDT')
```

---

### Safety Features

#### Emergency Cancel All
```python
# Cancel ALL orders on ALL symbols
result = client.emergency_cancel_all()

# Returns:
{
    'canceled_count': 5,
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'orders': [...]
}
```

#### Test Connectivity
```python
if client.ping():
    print("✅ Connected")
```

#### Get Server Time
```python
server_time = client.get_server_time()
```

---

## 🔒 Safety Best Practices

### 1. Always Start with Testnet

```python
# ✅ GOOD - Testnet (fake money)
client = ExchangeClient(
    api_key=TESTNET_KEY,
    api_secret=TESTNET_SECRET,
    testnet=True
)

# ❌ BAD - Mainnet (real money) without testing
client = ExchangeClient(
    api_key=MAINNET_KEY,
    api_secret=MAINNET_SECRET,
    testnet=False  # DANGEROUS!
)
```

### 2. Use Test Mode for Order Validation

```python
# Test order before real execution
test_result = client.place_market_order(
    symbol='BTCUSDT',
    side='BUY',
    quantity=0.001,
    test=True  # Validates but doesn't execute
)

if test_result['status'] == 'TEST':
    # Now place real order
    real_order = client.place_market_order(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.001,
        test=False
    )
```

### 3. Validate Quantities and Prices

```python
from exchange_client import format_quantity, format_price

# Get symbol rules
info = client.get_symbol_info('BTCUSDT')

# Format quantity according to rules
quantity = 0.0012345
formatted_qty = format_quantity(quantity, info['filters']['step_size'])
# Result: 0.00123 (rounded to step size)

# Format price according to rules
price = 43250.567
formatted_price = format_price(price, info['filters']['tick_size'])
# Result: 43250.56 (rounded to tick size)
```

### 4. Always Handle Errors

```python
from binance.exceptions import BinanceAPIException

try:
    order = client.place_market_order(
        symbol='BTCUSDT',
        side='BUY',
        quantity=0.001
    )
except BinanceAPIException as e:
    print(f"❌ Order failed: {e.message}")
    # Handle error (log, notify user, etc.)
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
```

### 5. Use Emergency Stop

```python
# If something goes wrong, cancel everything
if emergency_detected:
    client.emergency_cancel_all()
```

---

## 🧪 Testing Workflow

### Step 1: Test Connection
```bash
python test_exchange_client.py
```

Expected output:
```
✅ Client initialized
✅ Exchange ping successful
✅ Can Trade: True
✅ USDT Balance: 10000.00
```

### Step 2: Test Orders (Test Mode)

```python
# This will validate but NOT execute
client.place_market_order(
    symbol='BTCUSDT',
    side='BUY',
    quantity=0.001,
    test=True
)
```

### Step 3: Place Small Real Order on Testnet

```python
# Small amount for testing
client.place_market_order(
    symbol='BTCUSDT',
    side='BUY',
    quantity=0.001,  # ~$43 at $43000/BTC
    test=False
)
```

### Step 4: Verify Order Execution

```python
# Check positions
positions = client.get_positions()
print(positions)  # Should show BTC

# Check balance
btc_balance = client.get_balance('BTC')
print(btc_balance)  # Should show 0.001 BTC
```

---

## ⚠️ Common Errors

### 1. "Invalid API-key, IP, or permissions"
- **Cause:** Wrong API keys or IP not whitelisted
- **Fix:** Check API keys, verify testnet vs mainnet

### 2. "Account has insufficient balance"
- **Cause:** Not enough funds
- **Fix:** On testnet, request more funds from faucet

### 3. "Filter failure: MIN_NOTIONAL"
- **Cause:** Order value too small
- **Fix:** Increase quantity or check symbol's min_notional

### 4. "Filter failure: LOT_SIZE"
- **Cause:** Quantity doesn't match step size
- **Fix:** Use `format_quantity()` helper

### 5. "Filter failure: PRICE_FILTER"
- **Cause:** Price doesn't match tick size
- **Fix:** Use `format_price()` helper

---

## 📊 Example: Complete Trading Flow

```python
from exchange_client import ExchangeClient, format_quantity, format_price

# 1. Initialize client (testnet)
client = ExchangeClient(
    api_key="testnet_key",
    api_secret="testnet_secret",
    testnet=True
)

# 2. Check balance
usdt = client.get_balance('USDT')
print(f"Available USDT: {usdt['free']}")

# 3. Get current price and symbol info
symbol = 'BTCUSDT'
price = client.get_ticker_price(symbol)
info = client.get_symbol_info(symbol)
print(f"Current price: ${price:,.2f}")

# 4. Calculate quantity (e.g., $100 worth)
amount_usdt = 100
quantity = amount_usdt / price

# 5. Format according to rules
quantity = format_quantity(quantity, info['filters']['step_size'])
print(f"Buying {quantity} BTC")

# 6. Test order first
test_result = client.place_market_order(
    symbol=symbol,
    side='BUY',
    quantity=quantity,
    test=True
)
print(f"Test order: {test_result}")

# 7. Place real order
order = client.place_market_order(
    symbol=symbol,
    side='BUY',
    quantity=quantity,
    test=False
)
print(f"Order placed: {order}")

# 8. Verify position
positions = client.get_positions()
print(f"Positions: {positions}")
```

---

## 🚀 Next Steps

Now that you have the exchange client:

1. **Test on Testnet** ✅
   - Run `test_exchange_client.py`
   - Place test orders
   - Verify everything works

2. **Integrate with LiveExecutor** (Next)
   - Update `trading_modes.py`
   - Use real exchange in Live mode
   - Keep simulation mode for testing

3. **Add API Key Management** (Next)
   - UI for adding keys
   - Secure storage (encrypted)
   - Testnet vs Mainnet selector

4. **Production Testing**
   - Run on testnet for a few days
   - Monitor all operations
   - Fix any issues

5. **Mainnet (CAREFUL!)**
   - Only after extensive testnet testing
   - Start with very small amounts
   - Monitor closely

---

## 📞 Support

If you encounter issues:

1. Check `test_exchange_client.py` output
2. Verify API keys are correct
3. Confirm you're using testnet
4. Check Binance status: https://www.binance.com/en/support/announcement
5. Review error message carefully

---

**Status:** ✅ Exchange client ready for testing!
**Next:** Test on Binance Testnet and integrate with LiveExecutor

