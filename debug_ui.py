#!/usr/bin/env python3
"""
Debug script to check Enhanced UI issues
"""

from database_enhanced import EnhancedDatabase

def check_database():
    print("=" * 60)
    print("DATABASE DEBUG CHECK")
    print("=" * 60)

    db = EnhancedDatabase('AITradeGame.db')
    conn = db.get_connection()
    cursor = conn.cursor()

    # Check if models exist
    cursor.execute('SELECT id, name, trading_environment, automation_level FROM models')
    models = cursor.fetchall()

    print(f"\n1. MODELS IN DATABASE: {len(models)}")
    print("-" * 60)

    if len(models) == 0:
        print("❌ NO MODELS FOUND!")
        print("\nThis is why you see 'Select model' with no options.")
        print("\nCreating a test model...")

        # Create a test model
        cursor.execute('''
            INSERT INTO models (name, coins, capital, trading_environment, automation_level, exchange_environment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Test Trading Model', 'BTC,ETH,SOL', 10000.0, 'simulation', 'manual', 'testnet'))
        conn.commit()

        print("✓ Created 'Test Trading Model'")

        # Re-fetch models
        cursor.execute('SELECT id, name, trading_environment, automation_level FROM models')
        models = cursor.fetchall()

    for model in models:
        print(f"\nModel ID: {model['id']}")
        print(f"  Name: {model['name']}")
        print(f"  Environment: {model['trading_environment']}")
        print(f"  Automation: {model['automation_level']}")

    print("\n" + "=" * 60)
    print("2. CHECK API ENDPOINTS")
    print("=" * 60)

    if models:
        model_id = models[0]['id']
        print(f"\nTesting with Model ID: {model_id}")

        # Test get config
        env = db.get_trading_environment(model_id)
        auto = db.get_automation_level(model_id)
        exch = db.get_exchange_environment(model_id)

        print(f"\nCurrent Configuration:")
        print(f"  Environment: {env}")
        print(f"  Automation: {auto}")
        print(f"  Exchange: {exch}")

        print("\n✓ Database methods working")

    print("\n" + "=" * 60)
    print("3. JAVASCRIPT DEBUG INSTRUCTIONS")
    print("=" * 60)
    print("""
To debug JavaScript issues:

1. Open Enhanced UI: http://localhost:5000/enhanced

2. Open Browser Developer Tools:
   - Chrome/Edge: Press F12
   - Firefox: Press F12

3. Go to "Console" tab

4. Look for errors (red text)
   - If you see errors, copy them and share with me

5. Test manually in console:
   - Type: loadTradingMode()
   - Press Enter
   - Does it work?

6. Check if functions exist:
   - Type: typeof setTradingEnvironment
   - Should say: "function"
   - If it says "undefined", JavaScript didn't load

7. Check network requests:
   - Go to "Network" tab
   - Change environment or automation
   - Look for /api/models/1/environment or /api/models/1/automation
   - Click on it to see the response
   - Is it 200 OK or an error?
""")

    print("\n" + "=" * 60)
    print("4. COMMON ISSUES AND FIXES")
    print("=" * 60)
    print("""
Issue 1: "No model to select"
  Cause: Database is empty
  Fix: Run this script (debug_ui.py) - it creates a model

Issue 2: "No notifications/toasts"
  Cause: JavaScript error preventing showToast() from running
  Fix: Check browser console for errors

Issue 3: "Live warning modal doesn't appear"
  Cause: Event listener not attached or JavaScript error
  Fix: Check browser console, verify enhanced.js loaded

Issue 4: "Badge doesn't update"
  Cause: updateModeBadge() not being called
  Fix: Check if loadTradingMode() is running (console errors?)

Issue 5: "Selections don't persist"
  Cause: Either not saving to DB or not loading on page load
  Fix: Check Network tab - are POST requests succeeding?
""")

    print("\n" + "=" * 60)
    print("5. QUICK FIX CHECKLIST")
    print("=" * 60)
    print("""
□ Stop the server (Ctrl+C)
□ Run: python debug_ui.py
□ Start server: python app.py
□ Refresh browser (Ctrl+F5 or Cmd+Shift+R for hard refresh)
□ Open Developer Tools (F12)
□ Go to Console tab
□ Try changing environment - watch for errors
□ Try changing automation - watch for errors
□ Check Network tab for API calls
""")

    conn.close()

if __name__ == '__main__':
    check_database()
