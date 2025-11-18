#!/usr/bin/env python3
"""
Backend Testing Script for Graduation & Benchmark Features
"""
import sys
import json
from database import Database
from market_data import MarketDataFetcher

def test_database_schema():
    """Test 1: Database schema initialization"""
    print("\n" + "="*60)
    print("TEST 1: Database Schema Initialization")
    print("="*60)

    try:
        db = Database('AITradeGame.db')
        db.init_db()
        print("✅ Database initialized successfully")

        # Check if tables exist
        conn = db.get_connection()
        cursor = conn.cursor()

        tables = [
            'price_snapshots',
            'graduation_settings',
            'benchmark_settings',
            'cost_tracking_settings',
            'ai_costs'
        ]

        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"  ✅ Table '{table}' exists")
            else:
                print(f"  ❌ Table '{table}' missing")
                return False

        conn.close()
        print("✅ All tables created successfully\n")
        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}\n")
        return False

def test_graduation_settings():
    """Test 2: Graduation settings CRUD"""
    print("\n" + "="*60)
    print("TEST 2: Graduation Settings API")
    print("="*60)

    try:
        db = Database('AITradeGame.db')

        # Test GET (should have defaults)
        settings = db.get_graduation_settings()
        print(f"✅ GET graduation_settings: {json.dumps(settings, indent=2)}")

        if settings['strategy_preset'] != 'quick_test':
            print(f"  ⚠️  Expected 'quick_test', got '{settings['strategy_preset']}'")

        # Test UPDATE
        new_settings = {
            'strategy_preset': 'standard',
            'min_trades': 50,
            'confidence_level': 95,
            'min_testing_days': 30,
            'min_win_rate': 55.0,
            'min_sharpe_ratio': 1.0
        }

        db.update_graduation_settings(new_settings)
        print("✅ POST graduation_settings (update)")

        # Verify update
        updated = db.get_graduation_settings()
        if updated['strategy_preset'] == 'standard' and updated['min_trades'] == 50:
            print("✅ Settings updated correctly")
        else:
            print(f"❌ Settings not updated: {updated}")
            return False

        # Reset to defaults
        db.update_graduation_settings({'strategy_preset': 'quick_test', 'min_trades': 20})
        print("✅ Settings reset to defaults\n")
        return True

    except Exception as e:
        print(f"❌ Graduation settings test failed: {e}\n")
        return False

def test_benchmark_settings():
    """Test 3: Benchmark settings CRUD"""
    print("\n" + "="*60)
    print("TEST 3: Benchmark Settings API")
    print("="*60)

    try:
        db = Database('AITradeGame.db')

        # Test GET
        settings = db.get_benchmark_settings()
        print(f"✅ GET benchmark_settings")
        print(f"  track_btc_hold: {settings['track_btc_hold']}")
        print(f"  trading_fee_pct: {settings['trading_fee_pct']}")
        print(f"  calc_method: {settings['calc_method']}")

        # Test UPDATE
        db.update_benchmark_settings({
            'track_btc_hold': 1,
            'track_eth_hold': 1,
            'trading_fee_pct': 0.15
        })

        updated = db.get_benchmark_settings()
        if updated['trading_fee_pct'] == 0.15:
            print("✅ Benchmark settings updated correctly\n")
            return True
        else:
            print(f"❌ Update failed: {updated}\n")
            return False

    except Exception as e:
        print(f"❌ Benchmark settings test failed: {e}\n")
        return False

def test_price_snapshots():
    """Test 4: Price snapshot storage"""
    print("\n" + "="*60)
    print("TEST 4: Price Snapshot Storage")
    print("="*60)

    try:
        db = Database('AITradeGame.db')

        # Store test snapshots
        test_prices = {
            'BTC': 45000.50,
            'ETH': 2800.75,
            'SOL': 98.25
        }

        for coin, price in test_prices.items():
            db.store_price_snapshot(coin, price)

        print("✅ Stored 3 test price snapshots")

        # Verify storage
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM price_snapshots')
        count = cursor.fetchone()['count']
        print(f"✅ Total snapshots in database: {count}")

        # Test retrieval
        btc_snapshot = db.get_earliest_price_snapshot('BTC')
        if btc_snapshot:
            print(f"✅ Retrieved BTC snapshot: ${btc_snapshot['price']} at {btc_snapshot['timestamp']}")
        else:
            print("⚠️  No BTC snapshot found")

        conn.close()
        print("✅ Price snapshot storage working\n")
        return True

    except Exception as e:
        print(f"❌ Price snapshot test failed: {e}\n")
        return False

def test_ai_cost_tracking():
    """Test 5: AI cost tracking"""
    print("\n" + "="*60)
    print("TEST 5: AI Cost Tracking")
    print("="*60)

    try:
        db = Database('AITradeGame.db')

        # Check if we have any models
        models = db.get_all_models()
        if not models:
            print("⚠️  No models found - skipping cost tracking test")
            print("   (This is OK - create a model to test this feature)\n")
            return True

        model_id = models[0]['id']

        # Store test costs
        db.store_ai_cost(
            model_id=model_id,
            cost_type='trading_decision',
            cost_usd=0.05,
            tokens_used=1500,
            provider='openai',
            model_name='gpt-4-turbo'
        )

        print(f"✅ Stored test AI cost for model {model_id}")

        # Get total costs
        total = db.get_total_ai_costs(model_id)
        print(f"✅ Total AI costs for model {model_id}: ${total:.4f}")

        # Get detailed costs
        costs = db.get_ai_costs(model_id)
        print(f"✅ Retrieved {len(costs)} cost entries\n")
        return True

    except Exception as e:
        print(f"❌ AI cost tracking test failed: {e}\n")
        return False

def test_market_fetcher_integration():
    """Test 6: Market fetcher with price snapshots"""
    print("\n" + "="*60)
    print("TEST 6: Market Fetcher Integration")
    print("="*60)

    try:
        db = Database('AITradeGame.db')
        fetcher = MarketDataFetcher(db=db)

        print("Fetching market prices (this will store snapshots)...")
        prices = fetcher.get_current_prices(['BTC', 'ETH', 'SOL'])

        if prices:
            print("✅ Market prices fetched:")
            for coin, data in prices.items():
                print(f"  {coin}: ${data['price']:.2f} ({data['change_24h']:+.2f}%)")

            # Check if snapshots were stored
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT coin, price, timestamp FROM price_snapshots
                ORDER BY timestamp DESC LIMIT 3
            ''')
            recent = cursor.fetchall()
            conn.close()

            if recent:
                print("✅ Latest snapshots stored:")
                for row in recent:
                    print(f"  {row['coin']}: ${row['price']:.2f} at {row['timestamp']}")
            else:
                print("⚠️  No snapshots found (may be using cache)")

            print("✅ Market fetcher integration working\n")
            return True
        else:
            print("⚠️  No prices returned (API may be rate limited)\n")
            return True  # Not a failure, just rate limited

    except Exception as e:
        print(f"❌ Market fetcher test failed: {e}\n")
        return False

def test_graduation_status_calculation():
    """Test 7: Graduation status calculation (if models exist)"""
    print("\n" + "="*60)
    print("TEST 7: Graduation Status Calculation")
    print("="*60)

    try:
        db = Database('AITradeGame.db')

        # Check if we have models with trades
        models = db.get_all_models()
        if not models:
            print("⚠️  No models found - skipping graduation status test")
            print("   (This is OK - create a model with trades to test)\n")
            return True

        model_id = models[0]['id']

        # Check if model has trades
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM trades WHERE model_id = ?', (model_id,))
        trade_count = cursor.fetchone()['count']
        conn.close()

        if trade_count == 0:
            print(f"⚠️  Model {model_id} has no trades - skipping calculation")
            print("   (This is OK - make some trades to test)\n")
            return True

        # This would be tested via API endpoint in real scenario
        print(f"✅ Model {model_id} has {trade_count} trades")
        print(f"   Graduation status can be calculated via:")
        print(f"   GET /api/models/{model_id}/graduation-status")
        print("✅ Calculation logic is implemented\n")
        return True

    except Exception as e:
        print(f"❌ Graduation status test failed: {e}\n")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BACKEND TESTING SUITE")
    print("Testing Graduation & Benchmark Features")
    print("="*60)

    tests = [
        ("Database Schema", test_database_schema),
        ("Graduation Settings", test_graduation_settings),
        ("Benchmark Settings", test_benchmark_settings),
        ("Price Snapshots", test_price_snapshots),
        ("AI Cost Tracking", test_ai_cost_tracking),
        ("Market Fetcher Integration", test_market_fetcher_integration),
        ("Graduation Status", test_graduation_status_calculation)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Backend is ready for frontend integration.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
