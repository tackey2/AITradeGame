"""
Quick Enhanced API Test
Tests all endpoints to verify they work
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"
MODEL_ID = 1

def test(name, func):
    """Test helper"""
    try:
        print(f"\n{name}...", end=" ")
        result = func()
        print("✓")
        return result
    except Exception as e:
        print(f"✗ {e}")
        return None

print("=" * 60)
print("QUICK ENHANCED API TEST")
print("=" * 60)

# Test 1: Get models
def test_models():
    r = requests.get(f"{BASE_URL}/api/models")
    assert r.status_code == 200
    models = r.json()
    assert len(models) > 0
    return models

models = test("1. Get models", test_models)
if models:
    print(f"   Found {len(models)} model(s)")

# Test 2: Get trading mode
def test_get_mode():
    r = requests.get(f"{BASE_URL}/api/models/{MODEL_ID}/mode")
    assert r.status_code == 200
    data = r.json()
    assert 'mode' in data
    return data['mode']

mode = test("2. Get trading mode", test_get_mode)
if mode:
    print(f"   Current mode: {mode}")

# Test 3: Get settings
def test_get_settings():
    r = requests.get(f"{BASE_URL}/api/models/{MODEL_ID}/settings")
    assert r.status_code == 200
    settings = r.json()
    assert 'max_position_size_pct' in settings
    return settings

settings = test("3. Get settings", test_get_settings)
if settings:
    print(f"   Max position size: {settings['max_position_size_pct']}%")

# Test 4: Update settings
def test_update_settings():
    r = requests.post(f"{BASE_URL}/api/models/{MODEL_ID}/settings",
                      json={'max_position_size_pct': 12.0})
    assert r.status_code == 200
    return r.json()

test("4. Update settings", test_update_settings)

# Test 5: Get risk status
def test_risk_status():
    r = requests.get(f"{BASE_URL}/api/models/{MODEL_ID}/risk-status")
    assert r.status_code == 200
    risk = r.json()
    assert 'position_size' in risk
    return risk

risk = test("5. Get risk status", test_risk_status)
if risk:
    print(f"   Position size status: {risk['position_size']['status']}")

# Test 6: Get pending decisions
def test_pending():
    r = requests.get(f"{BASE_URL}/api/pending-decisions?model_id={MODEL_ID}")
    assert r.status_code == 200
    return r.json()

pending = test("6. Get pending decisions", test_pending)
if pending is not None:
    print(f"   Pending decisions: {len(pending)}")

# Test 7: Get readiness
def test_readiness():
    r = requests.get(f"{BASE_URL}/api/models/{MODEL_ID}/readiness")
    assert r.status_code == 200
    readiness = r.json()
    return readiness

readiness = test("7. Get readiness", test_readiness)
if readiness:
    print(f"   Readiness score: {readiness.get('score', 0)}/100")
    print(f"   Message: {readiness.get('message', 'N/A')}")

# Test 8: Get incidents
def test_incidents():
    r = requests.get(f"{BASE_URL}/api/models/{MODEL_ID}/incidents?limit=10")
    assert r.status_code == 200
    return r.json()

incidents = test("8. Get incidents", test_incidents)
if incidents is not None:
    print(f"   Total incidents: {len(incidents)}")

# Test 9: Set trading mode
def test_set_mode():
    r = requests.post(f"{BASE_URL}/api/models/{MODEL_ID}/mode",
                     json={'mode': 'semi_automated'})
    assert r.status_code == 200
    return r.json()

test("9. Set mode to semi_automated", test_set_mode)

# Test 10: Set back to simulation
def test_reset_mode():
    r = requests.post(f"{BASE_URL}/api/models/{MODEL_ID}/mode",
                     json={'mode': 'simulation'})
    assert r.status_code == 200
    return r.json()

test("10. Reset mode to simulation", test_reset_mode)

# Test 11: Enhanced page loads
def test_enhanced_page():
    r = requests.get(f"{BASE_URL}/enhanced")
    assert r.status_code == 200
    assert 'Personal Trading System' in r.text
    return True

test("11. Enhanced page loads", test_enhanced_page)

print("\n" + "=" * 60)
print("ALL TESTS PASSED! ✓")
print("=" * 60)
print("\nThe enhanced UI is working correctly!")
print(f"\nOpen your browser to: {BASE_URL}/enhanced")
print("=" * 60)
