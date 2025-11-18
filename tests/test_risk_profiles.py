#!/usr/bin/env python3
"""
Test script for Risk Profile Presets System
Tests all functionality including database, API, and profile application
"""

import sys
import requests
import json
from database_enhanced import EnhancedDatabase
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(message):
    """Print success message"""
    print(f"✓ {message}")

def print_error(message):
    """Print error message"""
    print(f"✗ {message}")

def print_info(message):
    """Print info message"""
    print(f"ℹ {message}")

# ============ Database Tests ============

def test_database_initialization():
    """Test 1: Database schema and system profiles"""
    print_section("Test 1: Database Initialization")

    try:
        db = EnhancedDatabase('AITradeGame.db')

        # Test profile table exists
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_profiles'")
        if cursor.fetchone():
            print_success("risk_profiles table exists")
        else:
            print_error("risk_profiles table NOT found")
            return False

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profile_sessions'")
        if cursor.fetchone():
            print_success("profile_sessions table exists")
        else:
            print_error("profile_sessions table NOT found")
            return False

        conn.close()

        # Test system profiles initialized
        profiles = db.get_all_risk_profiles()
        system_profiles = [p for p in profiles if p['is_system_preset']]

        print_info(f"Found {len(profiles)} total profiles, {len(system_profiles)} system presets")

        expected_profiles = ['Ultra-Safe', 'Conservative', 'Balanced', 'Aggressive', 'Scalper']
        found_names = [p['name'] for p in system_profiles]

        for name in expected_profiles:
            if name in found_names:
                print_success(f"System profile '{name}' exists")
            else:
                print_error(f"System profile '{name}' NOT found")

        # Display profile details
        print("\n" + "-" * 60)
        print("System Profile Details:")
        print("-" * 60)
        for profile in system_profiles:
            print(f"\n{profile['icon']} {profile['name']}")
            print(f"   Description: {profile['description']}")
            print(f"   Position Size: {profile['max_position_size_pct']}%")
            print(f"   Daily Loss: {profile['max_daily_loss_pct']}%")
            print(f"   Daily Trades: {profile['max_daily_trades']}")
            print(f"   Open Positions: {profile['max_open_positions']}")

        return True

    except Exception as e:
        print_error(f"Database test failed: {str(e)}")
        return False

# ============ API Tests ============

def test_api_get_all_profiles():
    """Test 2: GET /api/risk-profiles"""
    print_section("Test 2: API - Get All Profiles")

    try:
        response = requests.get(f"{BASE_URL}/api/risk-profiles")

        if response.status_code == 200:
            print_success(f"API returned status 200")
            profiles = response.json()
            print_info(f"Retrieved {len(profiles)} profiles")

            for profile in profiles[:3]:  # Show first 3
                print(f"   - {profile['icon']} {profile['name']}: {profile['description'][:40]}...")

            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on port 5001?")
        print_info("Start server with: python3 app.py")
        return False
    except Exception as e:
        print_error(f"API test failed: {str(e)}")
        return False

def test_api_get_specific_profile():
    """Test 3: GET /api/risk-profiles/<id>"""
    print_section("Test 3: API - Get Specific Profile")

    try:
        # Get Balanced profile (ID 3)
        response = requests.get(f"{BASE_URL}/api/risk-profiles/3")

        if response.status_code == 200:
            print_success("Retrieved specific profile")
            profile = response.json()

            print(f"\n   Name: {profile['name']}")
            print(f"   Max Position Size: {profile['max_position_size_pct']}%")
            print(f"   Max Daily Loss: {profile['max_daily_loss_pct']}%")
            print(f"   Max Daily Trades: {profile['max_daily_trades']}")
            print(f"   Trading Interval: {profile['trading_interval_minutes']} min")

            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_api_apply_profile():
    """Test 4: POST /api/models/<id>/apply-profile"""
    print_section("Test 4: API - Apply Profile to Model")

    try:
        # First, check if model 1 exists
        db = EnhancedDatabase('AITradeGame.db')
        models = db.get_all_models()

        if not models:
            print_info("No models found. Creating test model...")
            # Create a test model
            model_id = db.create_model(
                name="Test Model for Profiles",
                provider_id=1,
                initial_capital=10000
            )
            print_success(f"Created test model with ID: {model_id}")
        else:
            model_id = models[0]['id']
            print_info(f"Using existing model ID: {model_id}")

        # Apply Aggressive profile (ID 4)
        print_info("Applying 'Aggressive' profile (ID 4)...")

        response = requests.post(
            f"{BASE_URL}/api/models/{model_id}/apply-profile",
            json={"profile_id": 4},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Profile applied: {result['message']}")

            # Verify settings changed
            settings = db.get_model_settings(model_id)

            print("\n   Updated Settings:")
            print(f"   - Max Position Size: {settings['max_position_size_pct']}% (should be 15%)")
            print(f"   - Max Daily Loss: {settings['max_daily_loss_pct']}% (should be 5%)")
            print(f"   - Max Daily Trades: {settings['max_daily_trades']} (should be 40)")
            print(f"   - Active Profile ID: {settings.get('active_profile_id', 'None')}")

            # Verify correct values
            if (settings['max_position_size_pct'] == 15.0 and
                settings['max_daily_loss_pct'] == 5.0 and
                settings['max_daily_trades'] == 40):
                print_success("Settings match Aggressive profile!")
                return True
            else:
                print_error("Settings don't match expected profile values")
                return False
        else:
            print_error(f"API returned status {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_get_active_profile():
    """Test 5: GET /api/models/<id>/active-profile"""
    print_section("Test 5: API - Get Active Profile")

    try:
        db = EnhancedDatabase('AITradeGame.db')
        models = db.get_all_models()

        if not models:
            print_error("No models found")
            return False

        model_id = models[0]['id']

        response = requests.get(f"{BASE_URL}/api/models/{model_id}/active-profile")

        if response.status_code == 200:
            result = response.json()

            if result.get('active_profile'):
                profile = result['active_profile']
                print_success(f"Active profile: {profile['icon']} {profile['name']}")
                print(f"   Description: {profile['description']}")
                return True
            else:
                print_info("No active profile set (using custom settings)")
                return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_custom_profile_creation():
    """Test 6: Create custom profile"""
    print_section("Test 6: Create Custom Profile")

    try:
        custom_profile = {
            "name": "Test Custom Profile",
            "description": "A test custom profile",
            "color": "#ff6b6b",
            "icon": "🧪",
            "max_position_size_pct": 7.5,
            "max_open_positions": 4,
            "min_cash_reserve_pct": 25.0,
            "max_daily_loss_pct": 2.5,
            "max_drawdown_pct": 12.0,
            "max_daily_trades": 15,
            "trading_interval_minutes": 75,
            "auto_pause_consecutive_losses": 4,
            "auto_pause_win_rate_threshold": 42.0,
            "auto_pause_volatility_multiplier": 2.8,
            "trading_fee_rate": 0.1
        }

        print_info("Creating custom profile...")

        response = requests.post(
            f"{BASE_URL}/api/risk-profiles",
            json=custom_profile,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Custom profile created with ID: {result['profile_id']}")

            # Verify it's in the list
            all_profiles = requests.get(f"{BASE_URL}/api/risk-profiles").json()
            custom_profiles = [p for p in all_profiles if not p['is_system_preset']]

            print_info(f"Total custom profiles: {len(custom_profiles)}")

            return True
        else:
            print_error(f"Failed to create profile: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_profile_comparison():
    """Test 7: Compare profiles"""
    print_section("Test 7: Profile Comparison")

    try:
        # Compare Ultra-Safe (1) vs Aggressive (4)
        print_info("Comparing Ultra-Safe vs Aggressive...")

        response = requests.post(
            f"{BASE_URL}/api/risk-profiles/compare",
            json={"profile_ids": [1, 4]},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            profiles = result['profiles']
            comparison = result['comparison']

            print_success("Comparison successful")
            print("\n   Risk Levels:")
            for name, score in comparison['risk_levels'].items():
                print(f"   - {name}: {score:.1f}/100")

            print("\n   Profile Details:")
            for profile in profiles:
                print(f"\n   {profile['icon']} {profile['name']}:")
                print(f"      Position Size: {profile['max_position_size_pct']}%")
                print(f"      Daily Loss: {profile['max_daily_loss_pct']}%")
                print(f"      Daily Trades: {profile['max_daily_trades']}")

            return True
        else:
            print_error(f"Comparison failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def test_profile_protection():
    """Test 8: System profile protection"""
    print_section("Test 8: System Profile Protection")

    try:
        print_info("Attempting to delete system preset (should fail)...")

        response = requests.delete(f"{BASE_URL}/api/risk-profiles/1")  # Ultra-Safe

        if response.status_code == 403:
            print_success("System profile correctly protected from deletion")
            return True
        elif response.status_code == 200:
            print_error("ERROR: System profile was deleted! This should not happen!")
            return False
        else:
            print_info(f"Unexpected status: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

# ============ Main Test Runner ============

def run_all_tests():
    """Run all tests and display summary"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "RISK PROFILE SYSTEM TEST SUITE" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")

    tests = [
        ("Database Initialization", test_database_initialization),
        ("API: Get All Profiles", test_api_get_all_profiles),
        ("API: Get Specific Profile", test_api_get_specific_profile),
        ("API: Apply Profile", test_api_apply_profile),
        ("API: Get Active Profile", test_api_get_active_profile),
        ("Custom Profile Creation", test_custom_profile_creation),
        ("Profile Comparison", test_profile_comparison),
        ("System Profile Protection", test_profile_protection),
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
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {test_name}")

    print("\n" + "-" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("-" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Risk Profile system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return False

if __name__ == "__main__":
    print("\n⚙️  Starting Risk Profile System Tests...")
    print("Make sure the Flask server is running on port 5001")
    print("You can start it with: python3 app.py\n")

    input("Press Enter when ready to begin tests...")

    success = run_all_tests()

    sys.exit(0 if success else 1)
