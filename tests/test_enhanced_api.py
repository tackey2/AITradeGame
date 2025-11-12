"""
Test script for Enhanced API endpoints
Tests all new endpoints for the personal trading system
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_api():
    print("=" * 60)
    print("ENHANCED API TEST")
    print("=" * 60)

    # First, create a test provider and model
    print("\n1. Creating test provider...")
    provider_data = {
        'name': 'Test Provider',
        'api_url': 'https://api.openai.com/v1',
        'api_key': 'test-key',
        'models': 'gpt-3.5-turbo'
    }

    try:
        r = requests.post(f"{BASE_URL}/api/providers", json=provider_data)
        if r.status_code == 200:
            provider_id = r.json()['id']
            print(f"   ✓ Provider created: ID {provider_id}")
        else:
            print(f"   ✗ Provider creation failed: {r.text}")
            return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    print("\n2. Creating test model...")
    model_data = {
        'name': 'Test Model',
        'provider_id': provider_id,
        'model_name': 'gpt-3.5-turbo',
        'initial_capital': 10000
    }

    try:
        r = requests.post(f"{BASE_URL}/api/models", json=model_data)
        if r.status_code == 200:
            model_id = r.json()['id']
            print(f"   ✓ Model created: ID {model_id}")
        else:
            print(f"   ✗ Model creation failed: {r.text}")
            return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # Test trading mode management
    print("\n" + "=" * 60)
    print("TESTING TRADING MODE MANAGEMENT")
    print("=" * 60)

    print("\n3. Getting current trading mode...")
    try:
        r = requests.get(f"{BASE_URL}/api/models/{model_id}/mode")
        if r.status_code == 200:
            mode = r.json()['mode']
            print(f"   ✓ Current mode: {mode}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n4. Setting mode to semi_automated...")
    try:
        r = requests.post(f"{BASE_URL}/api/models/{model_id}/mode",
                         json={'mode': 'semi_automated'})
        if r.status_code == 200:
            print(f"   ✓ Mode changed to: {r.json()['mode']}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test settings management
    print("\n" + "=" * 60)
    print("TESTING SETTINGS MANAGEMENT")
    print("=" * 60)

    print("\n5. Getting model settings...")
    try:
        r = requests.get(f"{BASE_URL}/api/models/{model_id}/settings")
        if r.status_code == 200:
            settings = r.json()
            print(f"   ✓ Settings retrieved")
            print(f"      - Max position size: {settings.get('max_position_size_pct')}%")
            print(f"      - Max daily loss: {settings.get('max_daily_loss_pct')}%")
            print(f"      - Max open positions: {settings.get('max_open_positions')}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n6. Updating model settings...")
    try:
        new_settings = {
            'max_position_size_pct': 15.0,
            'max_daily_loss_pct': 5.0,
            'max_open_positions': 3
        }
        r = requests.post(f"{BASE_URL}/api/models/{model_id}/settings",
                         json=new_settings)
        if r.status_code == 200:
            print(f"   ✓ Settings updated")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test risk status
    print("\n" + "=" * 60)
    print("TESTING RISK STATUS")
    print("=" * 60)

    print("\n7. Getting risk status...")
    try:
        r = requests.get(f"{BASE_URL}/api/models/{model_id}/risk-status")
        if r.status_code == 200:
            risk = r.json()
            print(f"   ✓ Risk status retrieved")
            print(f"      - Position size: {risk['position_size']['status']}")
            print(f"      - Daily loss: {risk['daily_loss']['status']}")
            print(f"      - Open positions: {risk['open_positions']['status']}")
            print(f"      - Cash reserve: {risk['cash_reserve']['status']}")
            print(f"      - Daily trades: {risk['daily_trades']['status']}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test readiness assessment
    print("\n" + "=" * 60)
    print("TESTING READINESS ASSESSMENT")
    print("=" * 60)

    print("\n8. Getting readiness assessment...")
    try:
        r = requests.get(f"{BASE_URL}/api/models/{model_id}/readiness")
        if r.status_code == 200:
            readiness = r.json()
            print(f"   ✓ Readiness assessed")
            print(f"      - Ready: {readiness['ready']}")
            print(f"      - Score: {readiness['score']}/{readiness.get('max_score', 100)}")
            print(f"      - Message: {readiness['message']}")
            if readiness.get('metrics'):
                print(f"      - Total trades: {readiness['metrics'].get('total_trades', 0)}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test incidents log
    print("\n" + "=" * 60)
    print("TESTING INCIDENTS LOG")
    print("=" * 60)

    print("\n9. Getting model incidents...")
    try:
        r = requests.get(f"{BASE_URL}/api/models/{model_id}/incidents")
        if r.status_code == 200:
            incidents = r.json()
            print(f"   ✓ Incidents retrieved: {len(incidents)} total")
            if incidents:
                print(f"      Latest incident:")
                print(f"      - Type: {incidents[0]['incident_type']}")
                print(f"      - Severity: {incidents[0]['severity']}")
                print(f"      - Message: {incidents[0]['message']}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test pending decisions
    print("\n" + "=" * 60)
    print("TESTING PENDING DECISIONS")
    print("=" * 60)

    print("\n10. Getting pending decisions...")
    try:
        r = requests.get(f"{BASE_URL}/api/pending-decisions?model_id={model_id}")
        if r.status_code == 200:
            decisions = r.json()
            print(f"   ✓ Pending decisions retrieved: {len(decisions)} total")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test emergency controls
    print("\n" + "=" * 60)
    print("TESTING EMERGENCY CONTROLS")
    print("=" * 60)

    print("\n11. Testing emergency pause...")
    try:
        # First set to full auto
        requests.post(f"{BASE_URL}/api/models/{model_id}/mode",
                     json={'mode': 'fully_automated'})

        # Then pause
        r = requests.post(f"{BASE_URL}/api/models/{model_id}/pause",
                         json={'reason': 'Test emergency pause'})
        if r.status_code == 200:
            result = r.json()
            print(f"   ✓ Emergency pause executed")
            print(f"      - Previous mode: {result.get('previous_mode')}")
            print(f"      - New mode: {result.get('new_mode')}")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Cleanup
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    print("\n12. Deleting test model...")
    try:
        r = requests.delete(f"{BASE_URL}/api/models/{model_id}")
        if r.status_code == 200:
            print(f"   ✓ Model deleted")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n13. Deleting test provider...")
    try:
        r = requests.delete(f"{BASE_URL}/api/providers/{provider_id}")
        if r.status_code == 200:
            print(f"   ✓ Provider deleted")
        else:
            print(f"   ✗ Failed: {r.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    print("\nMake sure the Flask server is running (python app.py)")
    print("Press Enter to start test...")
    input()

    test_api()
