#!/usr/bin/env python3
"""
Test script for Phase 3: Profile Recommendations
Tests the market analyzer and recommendation system
"""

import sys
import requests
import json
from database_enhanced import EnhancedDatabase
from market_analyzer import MarketAnalyzer

BASE_URL = "http://localhost:5000"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_success(msg):
    print(f"✓ {msg}")

def print_info(msg):
    print(f"ℹ {msg}")

def print_error(msg):
    print(f"✗ {msg}")

# ============ Direct Module Tests ============

def test_market_analyzer_module():
    """Test 1: MarketAnalyzer module directly"""
    print_header("Test 1: Market Analyzer Module")

    try:
        db = EnhancedDatabase('AITradeGame.db')
        analyzer = MarketAnalyzer(db)

        # Get first model
        models = db.get_all_models()
        if not models:
            print_error("No models found. Create a model first.")
            return False

        model_id = models[0]['id']
        print_info(f"Using model ID: {model_id}")

        # Test market metrics calculation
        print("\n--- Market Metrics ---")
        metrics = analyzer.get_market_metrics(model_id)

        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Recent Win Rate (last 10): {metrics['recent_win_rate']:.1f}%")
        print(f"  Volatility: {metrics['volatility']:.2f}")
        print(f"  Drawdown: {metrics['drawdown_pct']:.2f}%")
        print(f"  Consecutive Losses: {metrics['consecutive_losses']}")
        print(f"  Daily P&L: {metrics['daily_pnl_pct']:.2f}%")
        print(f"  Trades Today: {metrics['trades_today']}")
        print(f"  Total Trades: {metrics['total_trades']}")

        # Test recommendation
        print("\n--- Profile Recommendation ---")
        recommendation = analyzer.recommend_profile(model_id)

        print(f"  Recommended: {recommendation['recommended_profile']}")
        print(f"  Current: {recommendation['current_profile'] or 'None'}")
        print(f"  Should Switch: {recommendation['should_switch']}")
        print(f"  Confidence: {recommendation['confidence']:.0f}%")
        print(f"  Reason: {recommendation['reason']}")

        if recommendation['all_reasons']:
            print("\n  All Reasons:")
            for i, reason in enumerate(recommendation['all_reasons'], 1):
                print(f"    {i}. {reason}")

        if recommendation['alternatives']:
            print("\n  Alternative Profiles:")
            for alt in recommendation['alternatives']:
                print(f"    - {alt['profile']} (score: {alt['score']:.0f})")

        print_success("Market Analyzer module working correctly")
        return True

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ============ API Tests ============

def test_recommendation_api():
    """Test 2: GET /api/models/<id>/recommend-profile"""
    print_header("Test 2: Profile Recommendation API")

    try:
        # Get first model
        db = EnhancedDatabase('AITradeGame.db')
        models = db.get_all_models()

        if not models:
            print_error("No models found")
            return False

        model_id = models[0]['id']
        print_info(f"Testing with model ID: {model_id}")

        response = requests.get(f"{BASE_URL}/api/models/{model_id}/recommend-profile")

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                rec = data['recommendation']
                metrics = data['metrics']

                print_success("API returned recommendation")

                print(f"\n  📊 Recommendation:")
                print(f"     {rec['profile_icon']} {rec['profile_name']}")
                print(f"     Confidence: {rec['confidence']:.0f}%")
                print(f"     Reason: {rec['reason']}")

                if rec['current_profile']:
                    print(f"\n  Current Profile: {rec['current_profile']}")
                    if rec['should_switch']:
                        print(f"  ⚠️  Recommendation: SWITCH to {rec['profile_name']}")
                    else:
                        print(f"  ✓ Current profile is optimal")

                print(f"\n  📈 Performance Metrics:")
                print(f"     Win Rate: {metrics['win_rate']:.1f}%")
                print(f"     Drawdown: {metrics['drawdown_pct']:.2f}%")
                print(f"     Volatility: {metrics['volatility']:.2f}")
                print(f"     Total Trades: {metrics['total_trades']}")

                if data.get('alternatives'):
                    print(f"\n  🔄 Alternative Profiles:")
                    for alt in data['alternatives']:
                        print(f"     - {alt['profile']} (score: {alt['score']:.0f})")

                return True
            else:
                print_error("API returned success=false")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            print_error(response.text)
            return False

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running?")
        return False
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_market_metrics_api():
    """Test 3: GET /api/models/<id>/market-metrics"""
    print_header("Test 3: Market Metrics API")

    try:
        db = EnhancedDatabase('AITradeGame.db')
        models = db.get_all_models()

        if not models:
            print_error("No models found")
            return False

        model_id = models[0]['id']

        response = requests.get(f"{BASE_URL}/api/models/{model_id}/market-metrics")

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                metrics = data['metrics']
                analysis = data['analysis']

                print_success("Market metrics retrieved")

                print(f"\n  Metrics:")
                print(f"     Win Rate: {metrics['win_rate']:.1f}%")
                print(f"     Recent Win Rate: {metrics['recent_win_rate']:.1f}%")
                print(f"     Volatility: {metrics['volatility']:.2f}")
                print(f"     Drawdown: {metrics['drawdown_pct']:.2f}%")
                print(f"     Consecutive Losses: {metrics['consecutive_losses']}")

                print(f"\n  Analysis:")
                print(f"     Market Condition: {analysis['condition'].upper()}")
                print(f"     Risk Level: {analysis['risk_level'].upper()}")
                print(f"     Trading Suitability: {analysis['trading_suitability'].replace('_', ' ').title()}")

                return True
            else:
                print_error("API returned success=false")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_profile_suitability_api():
    """Test 4: GET /api/models/<id>/profile-suitability"""
    print_header("Test 4: Profile Suitability API")

    try:
        db = EnhancedDatabase('AITradeGame.db')
        models = db.get_all_models()

        if not models:
            print_error("No models found")
            return False

        model_id = models[0]['id']

        response = requests.get(f"{BASE_URL}/api/models/{model_id}/profile-suitability")

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                profiles = data['profiles']

                print_success("Profile suitability calculated")

                print(f"\n  Profile Suitability Ranking:")
                print("  " + "-" * 60)

                for i, profile in enumerate(profiles, 1):
                    score = profile['suitability_score']
                    label = profile['suitability_label']
                    icon = profile['icon']
                    name = profile['name']

                    # Create visual bar
                    bar_length = int(score / 5)  # 100% = 20 chars
                    bar = "█" * bar_length + "░" * (20 - bar_length)

                    print(f"  {i}. {icon} {name:15} [{bar}] {score:.0f}% - {label}")

                return True
            else:
                print_error("API returned success=false")
                return False
        else:
            print_error(f"API returned status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

# ============ Integration Test ============

def test_recommendation_workflow():
    """Test 5: Full recommendation workflow"""
    print_header("Test 5: Complete Recommendation Workflow")

    try:
        db = EnhancedDatabase('AITradeGame.db')
        models = db.get_all_models()

        if not models:
            print_error("No models found")
            return False

        model_id = models[0]['id']

        print_info("Step 1: Get recommendation...")
        rec_response = requests.get(f"{BASE_URL}/api/models/{model_id}/recommend-profile")

        if rec_response.status_code != 200:
            print_error("Failed to get recommendation")
            return False

        rec_data = rec_response.json()
        recommended_profile_id = rec_data['recommendation']['profile_id']
        recommended_name = rec_data['recommendation']['profile_name']

        print_success(f"Recommended: {recommended_name}")

        if rec_data['recommendation']['should_switch']:
            print_info(f"Step 2: Applying recommended profile...")

            apply_response = requests.post(
                f"{BASE_URL}/api/models/{model_id}/apply-profile",
                json={"profile_id": recommended_profile_id},
                headers={"Content-Type": "application/json"}
            )

            if apply_response.status_code == 200:
                print_success(f"Profile '{recommended_name}' applied successfully")

                # Verify it's active
                active_response = requests.get(f"{BASE_URL}/api/models/{model_id}/active-profile")
                active_data = active_response.json()

                if active_data.get('active_profile'):
                    active_name = active_data['active_profile']['name']
                    if active_name == recommended_name:
                        print_success(f"Verified: Active profile is now '{active_name}'")
                        return True
                    else:
                        print_error(f"Mismatch: Expected '{recommended_name}', got '{active_name}'")
                        return False
                else:
                    print_error("No active profile set")
                    return False
            else:
                print_error(f"Failed to apply profile: {apply_response.status_code}")
                return False
        else:
            print_info("Current profile is already optimal - no need to switch")
            return True

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# ============ Main Test Runner ============

def run_all_tests():
    """Run all Phase 3 tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 3: RECOMMENDATION SYSTEM TESTS" + " " * 16 + "║")
    print("╚" + "═" * 68 + "╝")

    tests = [
        ("Market Analyzer Module", test_market_analyzer_module),
        ("Recommendation API", test_recommendation_api),
        ("Market Metrics API", test_market_metrics_api),
        ("Profile Suitability API", test_profile_suitability_api),
        ("Complete Workflow", test_recommendation_workflow),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))

    # Print summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {test_name}")

    print("\n" + "-" * 70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("-" * 70)

    if passed == total:
        print("\n🎉 All Phase 3 tests passed! Recommendation system is working.")
        print("\nYou can now:")
        print("  1. Get profile recommendations: GET /api/models/1/recommend-profile")
        print("  2. View market metrics: GET /api/models/1/market-metrics")
        print("  3. Check profile suitability: GET /api/models/1/profile-suitability")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return False

if __name__ == "__main__":
    print("\n⚙️  Starting Phase 3 Recommendation Tests...")
    print("Make sure the Flask server is running on port 5001\n")

    input("Press Enter when ready...")

    success = run_all_tests()

    sys.exit(0 if success else 1)
