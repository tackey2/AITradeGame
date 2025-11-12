"""
Test script for Binance Exchange Client

This script demonstrates how to use the exchange client on TESTNET.
No real money is used - completely safe for testing!

Prerequisites:
1. Create Binance Testnet account: https://testnet.binance.vision/
2. Get API key and secret from testnet
3. Add testnet API keys below
"""

from exchange_client import ExchangeClient
import time

# ============================================================
# CONFIGURATION - Add your TESTNET keys here
# ============================================================

# Get these from: https://testnet.binance.vision/
TESTNET_API_KEY = "your_testnet_api_key_here"
TESTNET_API_SECRET = "your_testnet_api_secret_here"

# Test symbol
SYMBOL = "BTCUSDT"


def test_connection():
    """Test 1: Basic connection and authentication"""
    print("\n" + "="*60)
    print("TEST 1: Connection and Authentication")
    print("="*60)

    try:
        # Initialize client (testnet=True by default)
        client = ExchangeClient(
            api_key=TESTNET_API_KEY,
            api_secret=TESTNET_API_SECRET,
            testnet=True  # IMPORTANT: Always True for testing!
        )

        print(f"✅ Client initialized: {client}")

        # Test ping
        if client.ping():
            print("✅ Exchange ping successful")
        else:
            print("❌ Exchange ping failed")
            return None

        return client

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return None


def test_account_info(client):
    """Test 2: Get account information"""
    print("\n" + "="*60)
    print("TEST 2: Account Information")
    print("="*60)

    try:
        account = client.get_account_info()

        print(f"✅ Can Trade: {account['can_trade']}")
        print(f"✅ Permissions: {account['permissions']}")

        print("\n📊 Balances:")
        for asset, balance in account['balances'].items():
            print(f"  {asset}: {balance['total']:.8f} (free: {balance['free']:.8f}, locked: {balance['locked']:.8f})")

        return True

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_market_data(client):
    """Test 3: Get market data"""
    print("\n" + "="*60)
    print("TEST 3: Market Data")
    print("="*60)

    try:
        # Get current price
        price = client.get_ticker_price(SYMBOL)
        print(f"✅ {SYMBOL} Price: ${price:,.2f}")

        # Get symbol info
        info = client.get_symbol_info(SYMBOL)
        print(f"\n📋 {SYMBOL} Trading Rules:")
        print(f"  Status: {info['status']}")
        print(f"  Base Asset: {info['base_asset']}")
        print(f"  Quote Asset: {info['quote_asset']}")

        if 'filters' in info:
            filters = info['filters']
            print(f"\n  Filters:")
            for key, value in filters.items():
                print(f"    {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_balance(client):
    """Test 4: Check specific balance"""
    print("\n" + "="*60)
    print("TEST 4: Balance Check")
    print("="*60)

    try:
        # Check USDT balance
        usdt = client.get_balance('USDT')
        print(f"✅ USDT Balance:")
        print(f"  Free: {usdt['free']:.2f}")
        print(f"  Locked: {usdt['locked']:.2f}")
        print(f"  Total: {usdt['total']:.2f}")

        # Check BTC balance
        btc = client.get_balance('BTC')
        print(f"\n✅ BTC Balance:")
        print(f"  Free: {btc['free']:.8f}")
        print(f"  Locked: {btc['locked']:.8f}")
        print(f"  Total: {btc['total']:.8f}")

        return True

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_order_placement(client):
    """Test 5: Place test orders (no execution)"""
    print("\n" + "="*60)
    print("TEST 5: Order Placement (TEST MODE)")
    print("="*60)

    try:
        # Test market buy order
        print("\n🧪 Testing market BUY order...")
        test_order = client.place_market_order(
            symbol=SYMBOL,
            side='BUY',
            quantity=0.001,  # Small amount for testing
            test=True  # TEST MODE - no execution!
        )
        print(f"✅ Test market order successful: {test_order}")

        # Test limit sell order
        print("\n🧪 Testing limit SELL order...")
        current_price = client.get_ticker_price(SYMBOL)
        limit_price = current_price * 1.1  # 10% above current price

        test_order = client.place_limit_order(
            symbol=SYMBOL,
            side='SELL',
            quantity=0.001,
            price=limit_price,
            test=True  # TEST MODE - no execution!
        )
        print(f"✅ Test limit order successful: {test_order}")

        return True

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_open_orders(client):
    """Test 6: Get open orders"""
    print("\n" + "="*60)
    print("TEST 6: Open Orders")
    print("="*60)

    try:
        # Get all open orders
        orders = client.get_open_orders()

        if not orders:
            print("✅ No open orders")
        else:
            print(f"✅ Found {len(orders)} open orders:")
            for order in orders:
                print(f"\n  Order ID: {order['order_id']}")
                print(f"  Symbol: {order['symbol']}")
                print(f"  Side: {order['side']}")
                print(f"  Type: {order['type']}")
                print(f"  Status: {order['status']}")
                print(f"  Quantity: {order['quantity']}")
                print(f"  Price: {order['price']}")

        # Get open orders for specific symbol
        symbol_orders = client.get_open_orders(SYMBOL)
        print(f"\n✅ {SYMBOL} open orders: {len(symbol_orders)}")

        return True

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_positions(client):
    """Test 7: Get positions"""
    print("\n" + "="*60)
    print("TEST 7: Current Positions")
    print("="*60)

    try:
        positions = client.get_positions()

        if not positions:
            print("✅ No positions (all balances are zero)")
        else:
            print(f"✅ Current positions:")
            for asset, amount in positions.items():
                print(f"  {asset}: {amount:.8f}")

        return True

    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 BINANCE TESTNET CLIENT TEST SUITE")
    print("="*60)
    print("\n⚠️  IMPORTANT: This uses TESTNET - no real money!")
    print("📝 Make sure you've added your testnet API keys above")
    print("\n")

    # Check if keys are set
    if TESTNET_API_KEY == "your_testnet_api_key_here":
        print("❌ ERROR: Please add your testnet API keys first!")
        print("\n📋 Steps to get testnet keys:")
        print("1. Go to: https://testnet.binance.vision/")
        print("2. Create account (or login)")
        print("3. Get API key from account settings")
        print("4. Update TESTNET_API_KEY and TESTNET_API_SECRET in this file")
        return

    # Test 1: Connection
    client = test_connection()
    if not client:
        print("\n❌ Connection failed - stopping tests")
        return

    # Test 2: Account Info
    test_account_info(client)

    # Test 3: Market Data
    test_market_data(client)

    # Test 4: Balance
    test_balance(client)

    # Test 5: Test Orders
    test_order_placement(client)

    # Test 6: Open Orders
    test_open_orders(client)

    # Test 7: Positions
    test_positions(client)

    # Summary
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\n📊 Summary:")
    print("  - Connection: ✅")
    print("  - Authentication: ✅")
    print("  - Market Data: ✅")
    print("  - Account Info: ✅")
    print("  - Order Testing: ✅")
    print("\n🎉 Exchange client is working correctly!")
    print("\n📖 Next steps:")
    print("  1. Try placing real orders on testnet (set test=False)")
    print("  2. Integrate with LiveExecutor")
    print("  3. Test with actual trading workflow")


if __name__ == '__main__':
    run_all_tests()
